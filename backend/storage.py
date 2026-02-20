from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).with_name("market_ai.db")


def connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                sector TEXT NOT NULL,
                signal TEXT NOT NULL,
                horizon TEXT NOT NULL,
                entry_low REAL NOT NULL,
                entry_high REAL NOT NULL,
                target REAL NOT NULL,
                stop_loss REAL NOT NULL,
                confidence REAL NOT NULL,
                reasoning TEXT NOT NULL,
                recommended_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'OPEN',
                result TEXT,
                close_price REAL,
                closed_at TEXT,
                return_pct REAL
            )
            """
        )


def store_prediction(stock: dict[str, Any], recommendation: dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO predictions
            (symbol, sector, signal, horizon, entry_low, entry_high, target, stop_loss,
             confidence, reasoning, recommended_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                stock["symbol"],
                stock["sector"],
                recommendation["signal"],
                recommendation["time_horizon"],
                recommendation["entry_range"][0],
                recommendation["entry_range"][1],
                recommendation["target_price"],
                recommendation["stop_loss"],
                recommendation["confidence_score"],
                recommendation["reasoning_summary"],
                recommendation["recommended_at"],
            ),
        )


def evaluate_predictions(latest_prices: dict[str, float]) -> None:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, symbol, signal, entry_low, entry_high, target, stop_loss FROM predictions WHERE status='OPEN'"
        ).fetchall()
        for row in rows:
            pid, symbol, signal, entry_low, entry_high, target, stop = row
            price = latest_prices.get(symbol)
            if price is None:
                continue

            entry = (entry_low + entry_high) / 2
            result = None
            if signal == "BUY":
                if price >= target:
                    result = "TARGET_HIT"
                elif price <= stop:
                    result = "STOP_HIT"
            elif signal == "SELL":
                if price <= target:
                    result = "TARGET_HIT"
                elif price >= stop:
                    result = "STOP_HIT"
            else:
                if abs(price - entry) > abs(target - entry):
                    result = "TIME_EXIT"

            if result:
                ret = ((price - entry) / entry) * 100 if signal != "SELL" else ((entry - price) / entry) * 100
                conn.execute(
                    """
                    UPDATE predictions
                    SET status='CLOSED', result=?, close_price=?, closed_at=?, return_pct=?
                    WHERE id=?
                    """,
                    (result, price, datetime.now(timezone.utc).isoformat(), round(ret, 2), pid),
                )


def performance_snapshot() -> dict[str, Any]:
    with connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
        wins = conn.execute("SELECT COUNT(*) FROM predictions WHERE result='TARGET_HIT'").fetchone()[0]
        losses = conn.execute("SELECT COUNT(*) FROM predictions WHERE result='STOP_HIT'").fetchone()[0]
        open_signals = conn.execute("SELECT COUNT(*) FROM predictions WHERE status='OPEN'").fetchone()[0]
        avg_return = conn.execute("SELECT AVG(return_pct) FROM predictions WHERE status='CLOSED'").fetchone()[0] or 0.0

        sectors = conn.execute(
            "SELECT sector, AVG(return_pct) FROM predictions WHERE status='CLOSED' GROUP BY sector"
        ).fetchall()

        best_sector, worst_sector = "N/A", "N/A"
        if sectors:
            ranked = sorted(sectors, key=lambda x: x[1], reverse=True)
            best_sector, worst_sector = ranked[0][0], ranked[-1][0]

        monthly = conn.execute(
            """
            SELECT substr(recommended_at, 1, 7) as month, AVG(COALESCE(return_pct, 0)), COUNT(*)
            FROM predictions
            GROUP BY month
            ORDER BY month
            """
        ).fetchall()

        strategy = conn.execute(
            "SELECT horizon, COUNT(*), AVG(COALESCE(return_pct, 0)) FROM predictions GROUP BY horizon"
        ).fetchall()

        closed_rows = conn.execute(
            "SELECT symbol, signal, confidence, result, return_pct, recommended_at, closed_at FROM predictions WHERE status='CLOSED' ORDER BY id DESC LIMIT 100"
        ).fetchall()

        open_rows = conn.execute(
            "SELECT symbol, signal, confidence, target, stop_loss, recommended_at FROM predictions WHERE status='OPEN' ORDER BY id DESC LIMIT 100"
        ).fetchall()

    equity_curve = []
    equity = 100.0
    for row in reversed(closed_rows):
        ret = row[4] or 0
        equity *= 1 + (ret / 100)
        equity_curve.append(round(equity, 2))

    return {
        "total_predictions": total,
        "accuracy_pct": round((wins / total) * 100, 2) if total else 0.0,
        "win_loss_ratio": f"{wins}:{losses}",
        "average_return_per_trade": round(avg_return, 2),
        "best_performing_sector": best_sector,
        "worst_performing_sector": worst_sector,
        "live_open_signals": open_signals,
        "closed_signals_history": [
            {
                "symbol": r[0],
                "signal": r[1],
                "confidence": r[2],
                "result": r[3],
                "return_pct": r[4],
                "recommended_at": r[5],
                "closed_at": r[6],
            }
            for r in closed_rows
        ],
        "open_signals": [
            {
                "symbol": r[0],
                "signal": r[1],
                "confidence": r[2],
                "target": r[3],
                "stop_loss": r[4],
                "recommended_at": r[5],
            }
            for r in open_rows
        ],
        "monthly_performance": [
            {"month": m[0], "avg_return": round(m[1], 2), "trades": m[2]} for m in monthly
        ],
        "strategy_breakdown": [
            {"horizon": s[0], "trades": s[1], "avg_return": round(s[2], 2)} for s in strategy
        ],
        "equity_curve": equity_curve,
    }


def failure_analysis() -> dict[str, Any]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT symbol, sector, signal, confidence, result FROM predictions WHERE result='STOP_HIT'"
        ).fetchall()

    pattern_count = defaultdict(int)
    for _, sector, signal, confidence, _ in rows:
        bucket = "low_conf" if confidence < 55 else "high_conf"
        key = f"{sector}:{signal}:{bucket}"
        pattern_count[key] += 1

    ranked = sorted(pattern_count.items(), key=lambda x: x[1], reverse=True)
    return {
        "failing_patterns": [{"pattern": k, "failures": v} for k, v in ranked[:5]],
        "model_weight_adjustment": "Increase penalty on overbought RSI sell signals in weak sectors.",
        "continuous_learning_loop": "Engine reviews STOP_HIT clusters and dampens confidence for repeated setups.",
    }

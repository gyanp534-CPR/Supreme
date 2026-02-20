from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _confidence_from_signals(rsi: float, macd: float, volatility: float) -> float:
    score = 50
    if rsi < 40:
        score += 18
    elif rsi > 70:
        score -= 12
    else:
        score += 6

    score += 10 if macd > 0 else -7
    score += 8 if volatility < 2.2 else -5

    return max(30, min(95, float(score)))


def generate_recommendation(stock: dict[str, Any], horizon: str) -> dict[str, Any]:
    price = stock["current_price"]
    indicators = stock["technical_indicators"]
    rsi = indicators["rsi"]
    macd = indicators["macd"]
    atr = indicators["atr"]

    if rsi < 42 and macd >= 0:
        signal = "BUY"
        target = price + atr * 2.5
        stop_loss = price - atr * 1.2
        reasoning = "Momentum recovery with supportive trend indicators and controlled volatility."
    elif rsi > 68 and macd < 0:
        signal = "SELL"
        target = price - atr * 2
        stop_loss = price + atr
        reasoning = "Overbought exhaustion and negative momentum divergence detected."
    else:
        signal = "HOLD"
        target = price + atr
        stop_loss = price - atr
        reasoning = "Mixed signals; wait for confirmation before directional commitment."

    confidence = _confidence_from_signals(rsi, macd, stock["volatility"])

    return {
        "symbol": stock["symbol"],
        "signal": signal,
        "time_horizon": horizon,
        "entry_range": [round(price * 0.995, 2), round(price * 1.005, 2)],
        "target_price": round(target, 2),
        "stop_loss": round(stop_loss, 2),
        "confidence_score": round(confidence, 2),
        "reasoning_summary": reasoning,
        "recommended_at": datetime.now(timezone.utc).isoformat(),
    }


def sentiment_summary(stocks: list[dict[str, Any]]) -> dict[str, Any]:
    advances = sum(1 for s in stocks if s["percent_change"] > 0)
    declines = len(stocks) - advances
    bias = "Bullish" if advances > declines else "Bearish" if declines > advances else "Neutral"

    sector_strength: dict[str, list[float]] = {}
    for stock in stocks:
        sector_strength.setdefault(stock["sector"], []).append(stock["percent_change"])

    ranked = sorted(
        ((k, round(sum(v) / len(v), 2)) for k, v in sector_strength.items()),
        key=lambda item: item[1],
        reverse=True,
    )

    return {
        "market_sentiment": bias,
        "advance_decline": {"advances": advances, "declines": declines},
        "sector_strength": ranked,
        "advisory_banner": "AI Generated Advisory – User discretion advised",
    }

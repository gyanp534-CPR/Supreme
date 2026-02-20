from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any

DATASET_PATH = Path(__file__).with_name("master_market_dataset.json")


@dataclass
class MasterDataset:
    generated_at: str
    stocks: list[dict[str, Any]]


def build_master_dataset() -> MasterDataset:
    """Creates a centralized market dataset for major Indian indices and sectors."""
    generated_at = datetime.utcnow().isoformat() + "Z"

    stock_blueprint = [
        ("Reliance Industries", "RELIANCE", "NSE", "Energy", ["Nifty 50", "Nifty 100", "Nifty 500"], "Largecap", 2934.20),
        ("Tata Consultancy Services", "TCS", "NSE", "IT", ["Nifty 50", "Nifty 100", "Nifty 500"], "Largecap", 4120.40),
        ("HDFC Bank", "HDFCBANK", "NSE", "Banking", ["Nifty 50", "Bank Nifty", "Nifty 100"], "Largecap", 1654.35),
        ("ICICI Bank", "ICICIBANK", "NSE", "Banking", ["Nifty 50", "Bank Nifty", "Nifty 100"], "Largecap", 1198.10),
        ("Infosys", "INFY", "NSE", "IT", ["Nifty 50", "Nifty 100", "Nifty 500"], "Largecap", 1822.50),
        ("Larsen & Toubro", "LT", "NSE", "Capital Goods", ["Nifty 50", "Nifty 100"], "Largecap", 3544.15),
        ("Bharti Airtel", "BHARTIARTL", "NSE", "Telecom", ["Nifty 50", "Nifty 100"], "Largecap", 1191.75),
        ("State Bank of India", "SBIN", "NSE", "Banking", ["Nifty 50", "Nifty 100", "Bank Nifty"], "Largecap", 768.25),
        ("Sun Pharma", "SUNPHARMA", "NSE", "Pharma", ["Nifty 50", "Nifty 100"], "Largecap", 1610.40),
        ("Bajaj Finance", "BAJFINANCE", "NSE", "Financial Services", ["Nifty 50", "Nifty 100"], "Largecap", 7066.35),
        ("Zomato", "ZOMATO", "NSE", "Consumer", ["Nifty 100", "Nifty 200", "Nifty 500"], "Midcap", 227.45),
        ("Indian Railway Finance Corp", "IRFC", "NSE", "Financial Services", ["Nifty 200", "Nifty 500"], "Midcap", 151.90),
        ("BSE Ltd", "BSE", "BSE", "Financial Services", ["BSE 100", "BSE 500"], "Midcap", 2894.40),
        ("Bharat Electronics", "BEL", "NSE", "Defence", ["Nifty 100", "Nifty 200", "Nifty 500"], "Midcap", 298.30),
        ("KPIT Technologies", "KPITTECH", "NSE", "IT", ["Nifty 200", "Nifty 500"], "Midcap", 1488.70),
        ("Cochin Shipyard", "COCHINSHIP", "NSE", "Defence", ["Nifty 500"], "Smallcap", 1680.55),
        ("Aster DM Healthcare", "ASTERDM", "NSE", "Healthcare", ["Nifty 500"], "Smallcap", 468.90),
        ("Titagarh Rail Systems", "TITAGARH", "NSE", "Capital Goods", ["Nifty 500"], "Smallcap", 1018.25),
        ("Prismx Global Ventures", "PRISMX", "BSE", "Microcap Diversified", ["BSE 500"], "Microcap", 2.17),
        ("Blue Cloud Softech", "BLUECLOUDS", "BSE", "Microcap IT", ["BSE 500"], "Microcap", 34.80),
    ]

    stocks = []
    for idx, (name, symbol, exchange, sector, membership, cap, price) in enumerate(stock_blueprint):
        rsi = 35 + (idx * 3) % 40
        macd = round(-1.5 + ((idx * 0.33) % 3), 2)
        atr = round(price * 0.02, 2)
        change = round(((idx % 7) - 3) * 0.65, 2)
        volume = 1_500_000 + idx * 225_000

        stocks.append(
            {
                "stock_name": name,
                "symbol": symbol,
                "exchange": exchange,
                "sector": sector,
                "index_membership": membership,
                "market_cap_category": cap,
                "current_price": round(price, 2),
                "historical_price_data": [
                    round(price * (0.96 + step * 0.01), 2) for step in range(6)
                ],
                "volume": volume,
                "volatility": round(1.1 + (idx % 6) * 0.45, 2),
                "technical_indicators": {
                    "rsi": rsi,
                    "macd": macd,
                    "sma_20": round(price * 0.99, 2),
                    "sma_50": round(price * 0.97, 2),
                    "ema_20": round(price * 1.01, 2),
                    "atr": atr,
                },
                "fundamental_metrics": {
                    "pe": round(12 + (idx % 15) * 1.8, 2),
                    "pb": round(1 + (idx % 8) * 0.45, 2),
                    "debt_to_equity": round(0.1 + (idx % 5) * 0.25, 2),
                },
                "percent_change": change,
            }
        )

    return MasterDataset(generated_at=generated_at, stocks=stocks)


def ensure_master_dataset() -> dict[str, Any]:
    if not DATASET_PATH.exists():
        payload = build_master_dataset()
        DATASET_PATH.write_text(
            json.dumps({"generated_at": payload.generated_at, "stocks": payload.stocks}, indent=2)
        )

    return json.loads(DATASET_PATH.read_text())

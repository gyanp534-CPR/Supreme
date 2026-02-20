# Supreme Markets AI

An AI-powered Indian market intelligence platform with centralized market dataset, advisory intelligence, recommendation engine, and self-evaluating trader performance panel.

## Features

- Master market dataset (`backend/master_market_dataset.json`) covering NSE/BSE securities with sector, index memberships, market-cap classes, technical indicators, and fundamentals.
- Dynamic UI modes (no static table):
  - Smart expandable stock cards
  - Sector heatmap
  - Index heatmap
  - Momentum scanner
  - AI signal feed
- AI engine for Buy/Sell/Hold with entry, target, stop loss, confidence, reasoning, and timestamps.
- Continuous evaluation loop that tracks target hits, stop hits, time exits, and aggregated trader analytics.
- AI Trader Panel for totals, accuracy, win/loss, return metrics, sector winners/laggards, open/closed signals, equity curve, monthly report, strategy breakdown.
- Advisory endpoint with sentiment and sector strength summary including disclaimer.
- Expansion-ready modular backend for future portfolio, alerts, backtesting, broker APIs, and compliance.

## Run

```bash
python -m backend.app
```

Open `http://localhost:8000`.

## API

- `GET /api/master-dataset`
- `GET /api/signals?horizon=swing&min_confidence=50&sector=IT&index=Nifty%2050`
- `GET /api/ai-trader-panel`
- `GET /api/advisory`

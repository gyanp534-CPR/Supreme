from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .ai_engine import generate_recommendation, sentiment_summary
from .market_data import ensure_master_dataset
from .storage import evaluate_predictions, failure_analysis, init_db, performance_snapshot, store_prediction

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend"


class MarketHandler(BaseHTTPRequestHandler):
    def _json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_static(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        content = path.read_bytes()
        ctype = "text/plain"
        if path.suffix == ".html":
            ctype = "text/html"
        elif path.suffix == ".css":
            ctype = "text/css"
        elif path.suffix == ".js":
            ctype = "application/javascript"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/master-dataset":
            data = ensure_master_dataset()
            self._json(
                {
                    "coverage": {
                        "exchanges": ["NSE", "BSE"],
                        "indices": [
                            "Nifty 50",
                            "Nifty 100",
                            "Nifty 200",
                            "Nifty 500",
                            "Bank Nifty",
                            "Sensex",
                            "BSE 100",
                            "BSE 500",
                            "Midcap",
                            "Smallcap",
                            "Microcap",
                        ],
                    },
                    **data,
                }
            )
            return

        if parsed.path == "/api/signals":
            qs = parse_qs(parsed.query)
            horizon = qs.get("horizon", ["swing"])[0]
            min_conf = float(qs.get("min_confidence", ["50"])[0])
            sector = qs.get("sector", [None])[0]
            index = qs.get("index", [None])[0]

            data = ensure_master_dataset()
            stocks = data["stocks"]
            if sector:
                stocks = [s for s in stocks if s["sector"].lower() == sector.lower()]
            if index:
                stocks = [s for s in stocks if index in s["index_membership"]]

            evaluate_predictions({s["symbol"]: s["current_price"] for s in stocks})
            generated = []
            for stock in stocks:
                signal = generate_recommendation(stock, horizon)
                if signal["confidence_score"] >= min_conf:
                    store_prediction(stock, signal)
                    generated.append(signal)

            self._json(
                {
                    "generated_count": len(generated),
                    "signals": generated,
                    "advisory": sentiment_summary(stocks),
                }
            )
            return

        if parsed.path == "/api/ai-trader-panel":
            self._json({"panel": performance_snapshot(), "continuous_learning": failure_analysis()})
            return

        if parsed.path == "/api/advisory":
            data = ensure_master_dataset()
            self._json(sentiment_summary(data["stocks"]))
            return

        if parsed.path in ["/", ""]:
            self._serve_static(FRONTEND_DIR / "index.html")
            return

        self._serve_static(FRONTEND_DIR / parsed.path.lstrip("/"))


def run(host: str = "0.0.0.0", port: int = 8000) -> None:
    init_db()
    with ThreadingHTTPServer((host, port), MarketHandler) as server:
        print(f"Serving Supreme Markets AI at http://{host}:{port}")
        server.serve_forever()


if __name__ == "__main__":
    run()

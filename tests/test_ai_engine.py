from backend.ai_engine import generate_recommendation


def test_generate_buy_signal():
    stock = {
        "symbol": "TEST",
        "current_price": 100.0,
        "volatility": 1.5,
        "technical_indicators": {"rsi": 35, "macd": 0.6, "atr": 2.0},
    }
    signal = generate_recommendation(stock, "swing")
    assert signal["signal"] == "BUY"
    assert signal["target_price"] > 100
    assert signal["confidence_score"] >= 50

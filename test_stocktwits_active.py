"""Test StockTwits avec un limit plus élevé et des symboles actifs."""
from src.data.stocktwits_client import bull_bear_ratio

symbols = ["AAPL", "TSLA", "NVDA"]
for sym in symbols:
    try:
        ratio = bull_bear_ratio(sym, limit=200)
        print(f"{sym}: {ratio}")
    except Exception as e:
        print(f"{sym}: error {e}")
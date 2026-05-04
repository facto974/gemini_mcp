"""Test StockTwits bull/bear ratio for several symbols."""
from src.data.stocktwits_client import bull_bear_ratio

symbols = ["BTC-USD", "ETH-USD", "SOL-USD", "DOGE-USD"]
for sym in symbols:
    try:
        ratio = bull_bear_ratio(sym)
        print(f"{sym}: {ratio}")
    except Exception as e:
        print(f"{sym}: error {e}")
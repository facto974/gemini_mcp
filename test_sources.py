"""Test each data source individually."""
import sys
sys.path.insert(0, '.')

from src.data.yfinance_client import fetch_ohlcv
from src.data.coingecko_client import price, community_score
from src.data.fear_greed_client import normalized_score
from src.data.stocktwits_client import bull_bear_ratio
from src.data.reddit_client import RedditClient

print("Testing OHLCV (yfinance/ccxt)...")
df = fetch_ohlcv("BTC-USD", period="5d", interval="1d")
if df.empty:
    print("  No OHLCV data fetched.")
else:
    print(f"  Last close: {df['Close'].iloc[-1]}")
    print(f"  Number of bars: {len(df)}")

print("\nTesting CoinGecko price...")
px = price("BTC-USD")
print(f"  Price: {px}")

print("\nTesting CoinGecko community score...")
cs = community_score("BTC-USD")
print(f"  Community score: {cs}")

print("\nTesting Fear & Greed index...")
fg = normalized_score()
print(f"  Normalized score: {fg}")

print("\nTesting StockTwits bull/bear ratio...")
try:
    st = bull_bear_ratio("BTC-USD")
    print(f"  Ratio: {st}")
except Exception as e:
    print(f"  Error: {e}")

print("\nTesting Reddit sentiment (needs REDDIT_CLIENT_ID/SECRET)...")
try:
    client_id = ""  # leave empty to test disabled case
    client_secret = ""
    user_agent = "test"
    rc = RedditClient(client_id, client_secret, user_agent)
    if rc.enabled:
        sent = rc.sentiment("BTC-USD", ["CryptoCurrency"], 10)
        print(f"  Sentiment: {sent}")
    else:
        print("  Reddit client disabled (no credentials).")
except Exception as e:
    print(f"  Error: {e}")

print("\nDone.")
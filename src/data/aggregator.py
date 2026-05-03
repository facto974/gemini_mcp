"""Agrégateur — fusionne toutes les sources en un snapshot par symbole."""
from __future__ import annotations

from dataclasses import dataclass

from . import coingecko_client, fear_greed_client, stocktwits_client, yfinance_client
from .finnhub_client import FinnhubClient
from .reddit_client import RedditClient


@dataclass
class MarketSnapshot:
    symbol: str
    price: float
    ohlcv: object  # pandas.DataFrame
    reddit: float
    stocktwits: float
    coingecko_social: float
    fear_greed: float


class DataAggregator:
    def __init__(self, finnhub: FinnhubClient, reddit: RedditClient,
                 reddit_subs: list[str], reddit_limit: int = 50):
        self.finnhub = finnhub
        self.reddit = reddit
        self.reddit_subs = reddit_subs
        self.reddit_limit = reddit_limit

    def snapshot(self, symbol: str, period: str = "60d", interval: str = "1h") -> MarketSnapshot:
        df = yfinance_client.fetch_ohlcv(symbol, period=period, interval=interval)
        price = float(df["Close"].iloc[-1]) if not df.empty else (coingecko_client.price(symbol) or 0.0)
        return MarketSnapshot(
            symbol=symbol,
            price=price,
            ohlcv=df,
            reddit=self.reddit.sentiment(symbol, self.reddit_subs, self.reddit_limit),
            stocktwits=stocktwits_client.bull_bear_ratio(symbol),
            coingecko_social=coingecko_client.community_score(symbol),
            fear_greed=fear_greed_client.normalized_score(),
        )

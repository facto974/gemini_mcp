"""Finnhub — quote temps réel + news sentiment (free tier)."""
from __future__ import annotations

from ._http import get_json, to_finnhub_symbol


BASE = "https://finnhub.io/api/v1"


class FinnhubClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def quote(self, symbol: str) -> dict:
        if not self.api_key:
            return {}
        return get_json(f"{BASE}/quote",
                        params={"symbol": to_finnhub_symbol(symbol), "token": self.api_key})

    def news_sentiment(self, symbol: str) -> dict:
        if not self.api_key:
            return {}
        return get_json(f"{BASE}/news-sentiment",
                        params={"symbol": symbol, "token": self.api_key})

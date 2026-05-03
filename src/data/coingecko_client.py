"""CoinGecko — prix crypto + scores sociaux (free tier)."""
from __future__ import annotations

from ._http import get_json, to_coingecko_id


BASE = "https://api.coingecko.com/api/v3"


def price(symbol: str, vs: str = "usd") -> float | None:
    cid = to_coingecko_id(symbol)
    data = get_json(f"{BASE}/simple/price", params={"ids": cid, "vs_currencies": vs})
    return data.get(cid, {}).get(vs)


def coin_overview(symbol: str) -> dict:
    cid = to_coingecko_id(symbol)
    return get_json(f"{BASE}/coins/{cid}",
                    params={"localization": "false", "tickers": "false",
                            "market_data": "true", "community_data": "true",
                            "developer_data": "false", "sparkline": "false"})


def community_score(symbol: str) -> float:
    """Score normalisé [-1, 1] basé sur sentiment_votes_up_percentage."""
    try:
        ov = coin_overview(symbol)
        up = ov.get("sentiment_votes_up_percentage")
        if up is None:
            return 0.0
        return (float(up) - 50.0) / 50.0
    except Exception:
        return 0.0

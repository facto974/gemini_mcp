"""StockTwits — bullish/bearish ratio par ticker (free, sans clé)."""
from __future__ import annotations

from ._http import get_json


def bull_bear_ratio(symbol: str) -> float:
    """Retourne ratio normalisé [-1, 1] basé sur les 30 derniers messages."""
    base = symbol.split("-")[0].upper() + ".X"  # crypto convention StockTwits
    try:
        data = get_json(f"https://api.stocktwits.com/api/2/streams/symbol/{base}.json")
    except Exception:
        return 0.0
    msgs = data.get("messages", [])
    bull = bear = 0
    for m in msgs:
        sent = (m.get("entities") or {}).get("sentiment") or {}
        b = sent.get("basic")
        if b == "Bullish":
            bull += 1
        elif b == "Bearish":
            bear += 1
    total = bull + bear
    if total == 0:
        return 0.0
    return (bull - bear) / total

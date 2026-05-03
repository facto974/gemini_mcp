"""Fear & Greed Index — alternative.me (gratuit, sans clé)."""
from __future__ import annotations

from ._http import get_json


URL = "https://api.alternative.me/fng/"


def current_index() -> dict:
    """Retourne {'value': int, 'value_classification': str}."""
    try:
        data = get_json(URL, params={"limit": 1, "format": "json"})
        item = data["data"][0]
        return {"value": int(item["value"]),
                "classification": item["value_classification"]}
    except Exception:
        return {"value": 50, "classification": "Neutral"}


def normalized_score() -> float:
    """Centre [0,100] sur [-1,+1] (0 = peur extrême, +1 = avidité extrême)."""
    v = current_index()["value"]
    return (v - 50.0) / 50.0

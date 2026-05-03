"""Helpers réseau partagés par les data clients."""
from __future__ import annotations

import time
from typing import Any

import httpx

DEFAULT_TIMEOUT = 10.0


def get_json(url: str, params: dict | None = None, headers: dict | None = None,
             timeout: float = DEFAULT_TIMEOUT, retries: int = 2) -> Any:
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with httpx.Client(timeout=timeout) as client:
                r = client.get(url, params=params, headers=headers)
                r.raise_for_status()
                return r.json()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(0.5 * (attempt + 1))
    raise RuntimeError(f"get_json failed: {url}: {last}")


def to_finnhub_symbol(sym: str) -> str:
    """BTC-USD -> BINANCE:BTCUSDT (fallback). Adapté à votre besoin."""
    base = sym.split("-")[0]
    return f"BINANCE:{base}USDT"


def to_coingecko_id(sym: str) -> str:
    base = sym.split("-")[0].lower()
    table = {"btc": "bitcoin", "eth": "ethereum", "sol": "solana",
             "doge": "dogecoin", "ada": "cardano", "avax": "avalanche-2"}
    return table.get(base, base)

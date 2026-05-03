"""yfinance — historique OHLCV illimité (gratuit, sans clé)."""
from __future__ import annotations

import pandas as pd
import yfinance as yf


def fetch_ohlcv(symbol: str, start: str | None = None, end: str | None = None,
                period: str = "60d", interval: str = "1h") -> pd.DataFrame:
    """Retourne un DataFrame avec colonnes Open/High/Low/Close/Volume."""
    if start or end:
        df = yf.download(symbol, start=start, end=end, interval=interval,
                         auto_adjust=True, progress=False)
    else:
        df = yf.download(symbol, period=period, interval=interval,
                         auto_adjust=True, progress=False)
    if df is None or df.empty:
        return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    df = df.rename(columns=str.title)
    return df.dropna()


def latest_price(symbol: str) -> float | None:
    df = fetch_ohlcv(symbol, period="2d", interval="1h")
    if df.empty:
        return None
    return float(df["Close"].iloc[-1])

"""Indicateurs techniques utilitaires."""
from __future__ import annotations

import numpy as np
import pandas as pd


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def momentum(series: pd.Series, lookback: int) -> pd.Series:
    return series.pct_change(lookback)


def zscore(series: pd.Series, window: int = 100) -> pd.Series:
    mean = series.rolling(window).mean()
    std = series.rolling(window).std().replace(0, np.nan)
    return (series - mean) / std


def returns(close: pd.Series) -> pd.Series:
    return close.pct_change().fillna(0.0)


def rolling_sharpe(rets: pd.Series, periods_per_year: int = 252 * 24) -> float:
    if rets.std() == 0 or rets.empty:
        return 0.0
    return float(rets.mean() / rets.std() * np.sqrt(periods_per_year))


def max_drawdown(equity: pd.Series) -> float:
    if equity.empty:
        return 0.0
    cummax = equity.cummax()
    dd = (equity - cummax) / cummax
    return float(dd.min())

"""Stratégie hybride momentum + sentiment.

Score composite ∈ [-1, 1] :
    score = w_mom * tanh(z_momentum) + w_sent * sentiment_avg + w_fg * fear_greed
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import indicators as ind


@dataclass
class StrategyConfig:
    w_momentum: float = 0.5
    w_sentiment: float = 0.3
    w_fear_greed: float = 0.2
    lookback: int = 7
    ema_smooth: int = 24
    threshold_long: float = 0.35
    threshold_short: float = -0.35
    allow_short: bool = False


@dataclass
class Signal:
    score: float
    momentum: float
    sentiment: float
    fear_greed: float
    decision: str  # 'LONG' | 'SHORT' | 'FLAT'


class MomentumSentimentStrategy:
    def __init__(self, cfg: StrategyConfig):
        self.cfg = cfg

    # ---- API "live" : prend un snapshot agrégé ----
    def evaluate(self, ohlcv: pd.DataFrame, reddit: float,
                 stocktwits: float, coingecko: float, fear_greed: float) -> Signal:
        if ohlcv is None or ohlcv.empty or "Close" not in ohlcv.columns:
            return Signal(0.0, 0.0, 0.0, fear_greed, "FLAT")

        close = ind.ema(ohlcv["Close"], self.cfg.ema_smooth)
        mom = ind.momentum(close, self.cfg.lookback).iloc[-1]
        z = ind.zscore(ind.momentum(close, self.cfg.lookback)).iloc[-1]
        if pd.isna(z):
            z = 0.0
        mom_score = float(np.tanh(z))

        sentiment_avg = float(np.mean([reddit, stocktwits, coingecko]))
        score = (self.cfg.w_momentum * mom_score
                 + self.cfg.w_sentiment * sentiment_avg
                 + self.cfg.w_fear_greed * fear_greed)
        score = max(-1.0, min(1.0, score))

        if score >= self.cfg.threshold_long:
            decision = "LONG"
        elif score <= self.cfg.threshold_short and self.cfg.allow_short:
            decision = "SHORT"
        elif score <= self.cfg.threshold_short:
            decision = "FLAT"  # close mais pas short
        else:
            decision = "FLAT"

        return Signal(score=score, momentum=float(mom or 0.0),
                      sentiment=sentiment_avg, fear_greed=fear_greed,
                      decision=decision)

    # ---- API "vectorisée" pour backtest ----
    def vectorized_signals(self, ohlcv: pd.DataFrame, sentiment_series: pd.Series | None = None,
                           fear_greed_series: pd.Series | None = None) -> pd.DataFrame:
        close = ind.ema(ohlcv["Close"], self.cfg.ema_smooth)
        mom = ind.momentum(close, self.cfg.lookback)
        z = ind.zscore(mom)
        mom_score = np.tanh(z.fillna(0.0))

        if sentiment_series is None:
            sentiment_series = pd.Series(0.0, index=ohlcv.index)
        if fear_greed_series is None:
            fear_greed_series = pd.Series(0.0, index=ohlcv.index)

        sentiment = sentiment_series.reindex(ohlcv.index).ffill().fillna(0.0)
        fg = fear_greed_series.reindex(ohlcv.index).ffill().fillna(0.0)

        score = (self.cfg.w_momentum * mom_score
                 + self.cfg.w_sentiment * sentiment
                 + self.cfg.w_fear_greed * fg).clip(-1, 1)

        position = pd.Series(0, index=ohlcv.index)
        position[score >= self.cfg.threshold_long] = 1
        if self.cfg.allow_short:
            position[score <= self.cfg.threshold_short] = -1

        return pd.DataFrame({"score": score, "momentum": mom_score,
                             "sentiment": sentiment, "fear_greed": fg,
                             "position": position})

"""Backtest engine vectorisé — long/short, fees, slippage."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..strategy import indicators as ind
from ..strategy.momentum_sentiment import MomentumSentimentStrategy


@dataclass
class BacktestResult:
    equity: pd.Series
    trades: int
    sharpe: float
    max_dd: float
    total_return: float
    win_rate: float


def run(ohlcv: pd.DataFrame, strategy: MomentumSentimentStrategy,
        fee_bps: float = 10, slippage_bps: float = 5,
        initial_equity: float = 10_000.0) -> BacktestResult:
    """Backtest vectorisé : la position du jour t est appliquée au close de t→t+1."""
    if ohlcv.empty:
        return BacktestResult(pd.Series(dtype=float), 0, 0.0, 0.0, 0.0, 0.0)

    sig = strategy.vectorized_signals(ohlcv)
    pos = sig["position"].shift(1).fillna(0)  # exec sur barre suivante

    rets = ind.returns(ohlcv["Close"])
    strat_rets = pos * rets

    # Frais : à chaque changement de position
    turnover = pos.diff().abs().fillna(0)
    cost = turnover * (fee_bps + slippage_bps) / 1e4
    strat_rets = strat_rets - cost

    equity = (1 + strat_rets).cumprod() * initial_equity
    trades = int((turnover > 0).sum())
    sharpe = ind.rolling_sharpe(strat_rets)
    mdd = ind.max_drawdown(equity)
    total_ret = float(equity.iloc[-1] / initial_equity - 1)

    # win_rate : segments de position non nulle
    wins = 0
    losses = 0
    in_pos = False
    entry = None
    for i in range(len(pos)):
        p = pos.iloc[i]
        c = ohlcv["Close"].iloc[i]
        if not in_pos and p != 0:
            in_pos = True
            entry = (c, p)
        elif in_pos and (p == 0 or (entry and np.sign(p) != np.sign(entry[1]))):
            pnl = (c - entry[0]) * entry[1]
            wins += pnl > 0
            losses += pnl <= 0
            in_pos = bool(p)
            entry = (c, p) if in_pos else None
    total_trades = wins + losses
    win_rate = wins / total_trades if total_trades else 0.0

    return BacktestResult(equity=equity, trades=trades, sharpe=sharpe,
                          max_dd=mdd, total_return=total_ret, win_rate=win_rate)

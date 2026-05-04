"""Lance un backtest vectorisé sur yfinance."""
from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).parent))

from src.backtest.engine import run
from src.data.yfinance_client import fetch_ohlcv
from src.strategy.momentum_sentiment import (MomentumSentimentStrategy,
                                              StrategyConfig)


@click.command()
@click.option("--symbol", default="BTC-USD")
@click.option("--start", default="2023-01-01")
@click.option("--end", default=None)
@click.option("--interval", default="1h")
def main(symbol: str, start: str, end: str | None, interval: str) -> None:
    console = Console()
    console.log(f"Fetching {symbol} {interval} from {start} to {end or 'now'}...")
    # Accept '1day' as an alias for '1d' (Gemini API expects '1d')
    interval_gemini = "1d" if interval == "1day" else interval
    df = fetch_ohlcv(symbol, start=start, end=end, interval=interval_gemini)
    if df.empty:
        console.print("[red]No data fetched.")
        return
    console.log(f"{len(df)} bars loaded.")

    strat = MomentumSentimentStrategy(StrategyConfig())
    res = run(df, strat)

    out = Path("data") / f"backtest_{symbol.replace('-', '')}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    res.equity.to_csv(out, header=["equity"])

    table = Table(title=f"Backtest {symbol}")
    table.add_column("Metric"); table.add_column("Value")
    table.add_row("Total return", f"{res.total_return:+.2%}")
    table.add_row("Sharpe (annualized)", f"{res.sharpe:.2f}")
    table.add_row("Max drawdown", f"{res.max_dd:.2%}")
    table.add_row("Trades", str(res.trades))
    table.add_row("Win rate", f"{res.win_rate:.2%}")
    console.print(table)
    console.log(f"Equity curve → {out}")


if __name__ == "__main__":
    main()

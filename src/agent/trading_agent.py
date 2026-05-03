"""Boucle de trading — orchestre data → strat → LLM → broker → métriques."""
from __future__ import annotations

import time
import uuid
from typing import Any

from rich.console import Console

from ..config import Settings
from ..data.aggregator import DataAggregator
from ..data.finnhub_client import FinnhubClient
from ..data.reddit_client import RedditClient
from ..db import Database
from ..metrics import (API_LATENCY, COMPOSITE_SENT, EQUITY, ERRORS, FEAR_GREED,
                        LOOP_DURATION, OPEN_POSITIONS, ORDERS, PRICE,
                        REALIZED_PNL, REDDIT_SENT, SCORE, STOCKTWITS_RATIO,
                        UNREALIZED_PNL, TRADES_TOTAL)
from ..strategy.momentum_sentiment import (MomentumSentimentStrategy,
                                            StrategyConfig)
from ..broker.paper_broker import PaperBroker
from ..broker.gemini_client import GeminiClient
from .openrouter_client import OpenRouterAgent


console = Console()


class TradingAgent:
    def __init__(self, settings: Settings):
        self.s = settings
        cfg = settings.raw

        # Stratégie
        sc = StrategyConfig(
            w_momentum=cfg.get("strategy", {}).get("weights", {}).get("momentum", 0.5),
            w_sentiment=cfg.get("strategy", {}).get("weights", {}).get("sentiment", 0.3),
            w_fear_greed=cfg.get("strategy", {}).get("weights", {}).get("fear_greed", 0.2),
            lookback=cfg.get("strategy", {}).get("momentum", {}).get("lookback_days", 7),
            ema_smooth=cfg.get("strategy", {}).get("momentum", {}).get("ema_smooth", 24),
            threshold_long=cfg.get("strategy", {}).get("thresholds", {}).get("long", 0.35),
            threshold_short=cfg.get("strategy", {}).get("thresholds", {}).get("short", -0.35),
            allow_short=cfg.get("risk", {}).get("allow_short", False),
        )
        self.strategy = MomentumSentimentStrategy(sc)

        # Data
        self.aggregator = DataAggregator(
            FinnhubClient(settings.finnhub_api_key),
            RedditClient(settings.reddit_client_id, settings.reddit_client_secret,
                         settings.reddit_user_agent),
            cfg.get("strategy", {}).get("sentiment", {}).get("reddit_subs",
                                                              ["CryptoCurrency"]),
            cfg.get("strategy", {}).get("sentiment", {}).get("reddit_limit", 50),
        )

        # Broker
        self.mode = cfg.get("mode", "paper")
        self.paper = PaperBroker(initial_cash=10_000.0)
        self.gemini = GeminiClient(settings.gemini_api_key, settings.gemini_api_secret,
                                   sandbox=settings.gemini_sandbox)

        # LLM
        llm_cfg = cfg.get("llm", {})
        self.llm = OpenRouterAgent(
            settings.openrouter_api_key,
            llm_cfg.get("model", settings.openrouter_model),
            llm_cfg.get("temperature", 0.2),
        )
        self.validate_signals = llm_cfg.get("validate_signals", True)

        # Risk
        risk = cfg.get("risk", {})
        self.max_position_usd = float(risk.get("max_position_usd", 1000))
        self.kelly_fraction = float(risk.get("kelly_fraction", 0.25))

        self.db = Database(settings.sqlite_path)

    # ---- helpers ----
    def _log(self, msg: str) -> None:
        console.log(msg)

    def _execute(self, symbol: str, side: str, qty: float, price: float) -> dict[str, Any]:
        ORDERS.labels(side=side, symbol=symbol).inc()
        if self.mode == "paper":
            tr = self.paper.market(symbol, side, qty, price)
            self.db.insert_trade(symbol, side, qty, price, "paper",
                                 fee=tr["fee"], pnl=tr["pnl"])
            return tr
        # live / sandbox
        try:
            t0 = time.time()
            limit_price = price * (1.001 if side == "buy" else 0.999)
            res = self.gemini.place_order(symbol, side, qty, limit_price,
                                          client_order_id=str(uuid.uuid4()))
            API_LATENCY.labels(endpoint="place_order").observe(time.time() - t0)
            self.db.insert_trade(symbol, side, qty, price, "live",
                                 order_id=str(res.get("order_id", "")))
            return res
        except Exception as e:  # noqa: BLE001
            ERRORS.labels(component="gemini").inc()
            self._log(f"[red]Gemini error {e}")
            return {}

    # ---- main loop ----
    @LOOP_DURATION.time()
    def step(self) -> None:
        marks: dict[str, float] = {}
        for symbol in self.s.universe:
            try:
                snap = self.aggregator.snapshot(symbol)
            except Exception as e:  # noqa: BLE001
                ERRORS.labels(component="data").inc()
                self._log(f"[red]Data error {symbol}: {e}")
                continue

            if snap.price <= 0:
                continue
            marks[symbol] = snap.price
            PRICE.labels(symbol=symbol).set(snap.price)
            REDDIT_SENT.labels(symbol=symbol).set(snap.reddit)
            STOCKTWITS_RATIO.labels(symbol=symbol).set(snap.stocktwits)
            FEAR_GREED.set((snap.fear_greed + 1) * 50)  # back to 0-100

            sig = self.strategy.evaluate(snap.ohlcv, snap.reddit, snap.stocktwits,
                                         snap.coingecko_social, snap.fear_greed)
            SCORE.labels(symbol=symbol).set(sig.score)
            COMPOSITE_SENT.labels(symbol=symbol).set(sig.sentiment)
            self.db.record_signal(symbol, sig.score, sig.momentum, sig.sentiment,
                                  sig.fear_greed, sig.decision)

            self._log(f"{symbol} px={snap.price:.2f} score={sig.score:+.3f} "
                      f"decision={sig.decision}")

            if sig.decision in ("LONG", "SHORT"):
                action = "buy" if sig.decision == "LONG" else "sell"
                if self.validate_signals:
                    verdict = self.llm.validate(
                        {"score": sig.score, "momentum": sig.momentum,
                         "sentiment": sig.sentiment, "fear_greed": sig.fear_greed},
                        action,
                    )
                    self._log(f"  LLM: {verdict}")
                    if not verdict["approve"]:
                        continue
                notional = self.max_position_usd * self.kelly_fraction
                qty = round(notional / snap.price, 6)
                if qty > 0:
                    self._execute(symbol, action, qty, snap.price)
            elif sig.decision == "FLAT":
                pos = self.paper.positions.get(symbol)
                if pos and pos.qty > 0:
                    self._execute(symbol, "sell", pos.qty, snap.price)

        # Equity & metrics globales
        equity, unreal = self.paper.equity(marks)
        EQUITY.set(equity)
        REALIZED_PNL.set(self.paper.realized_pnl)
        UNREALIZED_PNL.set(unreal)
        OPEN_POSITIONS.set(sum(1 for p in self.paper.positions.values() if p.qty != 0))
        TRADES_TOTAL.set(len(self.paper.trades))
        self.db.record_equity(equity, self.paper.realized_pnl, unreal)

    def run_forever(self) -> None:
        self._log(f"[green]Agent démarré — mode={self.mode} sandbox={self.s.gemini_sandbox}")
        while True:
            try:
                self.step()
            except Exception as e:  # noqa: BLE001
                ERRORS.labels(component="loop").inc()
                self._log(f"[red]loop error: {e}")
            time.sleep(self.s.loop_interval)

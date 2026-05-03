"""Lance le paper-trading + exporter Prometheus."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.agent.trading_agent import TradingAgent
from src.config import Settings
from src.metrics import start_metrics_server


def main() -> None:
    settings = Settings.load()
    if settings.raw.get("metrics", {}).get("enabled", True):
        start_metrics_server(settings.metrics_port)
    TradingAgent(settings).run_forever()


if __name__ == "__main__":
    main()

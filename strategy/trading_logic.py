"""Logique de trading pour GeminiMCP‑Trader.

Cette implémentation utilise les indicateurs suivants :
* SMA courte (20 périodes)
* SMA longue (50 périodes)
* RSI (14 périodes)

Les signaux sont générés de la façon suivante :
* **Long** : SMA courte > SMA longue **et** RSI < overbought (70)
* **Short** : SMA courte < SMA longue **et** RSI > oversold (30)

La fonction `generate_signals` renvoie le DataFrame avec une colonne `signal`
valant 1 (long), -1 (short) ou 0 (neutre).
"""

import pandas as pd
import ta
import yaml

import os
from pathlib import Path

# Chargement du fichier de configuration en utilisant le chemin absolu du module
config_path = Path(__file__).resolve().parent.parent / "config.yaml"
with open(config_path, "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

SMA_SHORT = cfg["strategy"]["sma_short"]
SMA_LONG = cfg["strategy"]["sma_long"]
RSI_PERIOD = cfg["strategy"]["rsi_period"]
RSI_OB = cfg["strategy"]["rsi_overbought"]
RSI_OS = cfg["strategy"]["rsi_oversold"]


def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute les colonnes SMA, RSI et le signal de trading.

    Le DataFrame doit contenir au minimum une colonne `close`.
    """
    df = df.copy()
    df["sma_short"] = df["close"].rolling(SMA_SHORT).mean()
    df["sma_long"] = df["close"].rolling(SMA_LONG).mean()
    df["rsi"] = ta.momentum.RSIIndicator(df["close"], window=RSI_PERIOD).rsi()
    df["signal"] = 0

    # Long signal
    df.loc[(df["sma_short"] > df["sma_long"]) & (df["rsi"] < RSI_OB), "signal"] = 1
    # Short signal
    df.loc[(df["sma_short"] < df["sma_long"]) & (df["rsi"] > RSI_OS), "signal"] = -1
    return df

"""Backtesting avec l'API publique de Gemini.

Le script récupère les chandeliers via l'API Gemini (v2), applique la logique
de trading et calcule le rendement cumulé.
"""

import requests
import pandas as pd
from strategy.trading_logic import generate_signals
import yaml
from pathlib import Path

config_path = Path(__file__).resolve().parent.parent / "config.yaml"
with open(config_path, "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

PAIR = cfg["strategy"]["pair"]
TIMEFRAME = cfg["strategy"]["timeframe"]
# Utilise l'URL v2 publique (pas besoin d'API key pour les chandeliers publics)
BASE_URL_V2 = cfg["gemini"]["base_url_v2"]


def fetch_data() -> pd.DataFrame:
    """Récupère les chandeliers via l'API publique Gemini v2 (utilise l'URL live pour les données publiques)."""
    # Les données publiques (chandeliers) sont identiques sur sandbox et live,
    # mais le sandbox v2 peut ne pas avoir de données historiques. On utilise donc l'URL live.
    LIVE_V2_URL = "https://api.gemini.com/v2"
    symbol = PAIR.lower()
    
    # Essayer d'abord le timeframe configuré, puis un fallback sur 1hr si échec
    timeframes_to_try = [TIMEFRAME, "1hr", "1day"]
    for tf in timeframes_to_try:
        url = f"{LIVE_V2_URL}/candles/{symbol}/{tf}"
        print(f"[DEBUG] Requête Gemini (tf={tf}) : {url}")
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 400:
                print(f"[!] Pas de données pour {tf}, essai avec {timeframes_to_try[timeframes_to_try.index(tf)+1] if timeframes_to_try.index(tf)+1 < len(timeframes_to_try) else 'aucun'}")
                continue
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                print(f"[+] Données récupérées avec succès pour {tf} ({len(data)} chandeliers)")
                TIMEFRAME = tf  # Met à jour le timeframe utilisé
                break
        except requests.exceptions.HTTPError as e:
            print(f"[!] Erreur HTTP {resp.status_code} pour {url}")
            print(f"    Réponse Gemini : {resp.text[:200]}")
            continue
        except Exception as e:
            print(f"[!] Erreur lors de la récupération : {e}")
            continue
    else:
        print(f"[!] Aucune donnée disponible pour {symbol} après essais sur {timeframes_to_try}")
        return pd.DataFrame()

    if not isinstance(data, list) or len(data) == 0:
        print(f"[!] Aucune donnée reçue depuis l'API Gemini pour {PAIR} ({TIMEFRAME}).")
        return pd.DataFrame()

    df = pd.DataFrame(data)
    # Convertir le timestamp (millisecondes) en datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    df.sort_index(inplace=True)  # ordre chronologique croissant

    # Renommer les colonnes pour correspondre au format attendu
    df = df.rename(columns={"open": "open", "high": "high", "low": "low", "close": "close", "volume": "volume"})
    df = df[["open", "high", "low", "close", "volume"]]
    return df


def run_backtest():
    df = fetch_data()
    if df.empty or len(df) < 50:
        print("[!] Back‑testing annulé : données insuffisantes (besoin d'au moins 50 chandeliers).")
        return
    df = generate_signals(df)
    # Position prise au close du candle suivant le signal
    df["position"] = df["signal"].shift(1).fillna(0)
    df["returns"] = df["close"].pct_change()
    df["strategy"] = df["position"] * df["returns"]
    cumulative = (1 + df["strategy"].fillna(0)).cumprod()
    print(f"Backtest terminé : {len(df)} chandeliers traités.")
    print("Cumulative return (backtest) :", round(cumulative.iloc[-1], 4))


if __name__ == "__main__":
    run_backtest()

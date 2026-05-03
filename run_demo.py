"""Exécution de la stratégie en mode paper‑trading (sandbox Gemini).

Ce script récupère les dernières bougies 5 min, génère les signaux via
`strategy.trading_logic.generate_signals` et place des ordres market sur le
sandbox Gemini. Il utilise les paramètres définis dans `config.yaml`.
"""

import time
import yaml
import requests
import pandas as pd
from strategy.trading_logic import generate_signals
from metrics import (
    start_metrics_server,
    orders_total,
    trades_success,
    trades_failed,
    account_balance,
    cumulative_return,
)

with open("config.yaml", "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

BASE_URL_V1 = cfg["gemini"]["base_url_v1"]
BASE_URL_V2 = cfg["gemini"]["base_url_v2"]
API_KEY = cfg["gemini"]["api_key"]
PAIR = cfg["strategy"]["pair"]
TIMEFRAME = cfg["strategy"]["timeframe"]
RISK = cfg["strategy"]["risk_per_trade"]


def _auth_headers():
    return {"Content-Type": "application/json", "X-GEMINI-APIKEY": API_KEY}


def fetch_latest_candles() -> pd.DataFrame:
    """Récupère les dernières bougies 5 min via l’endpoint public de Gemini (v2)."""
    resp = requests.get(f"{BASE_URL_V2}/candles/{PAIR}/{TIMEFRAME}")
    data = resp.json()
    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
    df.set_index("timestamp", inplace=True)
    return df


def place_market_order(side: str, amount: float):
    """Envoie un ordre market au sandbox Gemini."""
    order = {
        "request": "/v1/order/new",
        "nonce": str(int(time.time() * 1000)),
        "symbol": PAIR,
        "amount": f"{amount:.8f}",
        "price": "0",
        "side": side,
        "type": "exchange market",
    }
    orders_total.labels(side=side).inc()
    resp = requests.post(f"{BASE_URL_V1}/order/new", json=order, headers=_auth_headers())
    if resp.ok:
        trades_success.inc()
        print(f"[+] Order {side} {amount:.8f} {PAIR} → OK")
    else:
        trades_failed.inc()
        print(f"[-] Order {side} {amount:.8f} {PAIR} → FAILED: {resp.text}")
    return resp


def update_balance():
    """Met à jour le solde du compte dans les métriques."""
    try:
        resp = requests.post(f"{BASE_URL_V1}/balances", json={}, headers=_auth_headers())
        if resp.ok:
            balances = resp.json()
            # Récupération du solde USD (à adapter selon la réponse de l'API)
            usd_balance = float(balances.get("USD", {}).get("available", 0))
            account_balance.set(usd_balance)
    except Exception as e:
        print(f"[!] Erreur mise à jour solde: {e}")


def main():
    # Démarrage du serveur de métriques Prometheus
    start_metrics_server(8000)
    print("[*] Serveur de métriques démarré sur http://localhost:8000/metrics")
    
    while True:
        df = fetch_latest_candles()
        df = generate_signals(df)
        signal = df["signal"].iloc[-1]
        # Exemple de taille de position fixe (0.001 BTC) – à adapter selon le capital
        amount = 0.001
        if signal == 1:
            print("[+] Signal LONG – envoi d'un ordre d'achat")
            place_market_order("buy", amount)
            update_balance()
        elif signal == -1:
            print("[-] Signal SHORT – envoi d'un ordre de vente")
            place_market_order("sell", amount)
            update_balance()
        else:
            print("[*] Aucun signal")
        time.sleep(300)  # 5 minutes

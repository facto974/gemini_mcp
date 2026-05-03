"""Serveur MCP minimal pour exposer les endpoints Gemini.

Ce serveur utilise Flask (déjà inclus dans la plupart des environnements Python).
Il fournit les fonctions suivantes :
* `/ticker/<pair>` : prix actuel du pair demandé.
* `/order` : placement d’un ordre market (sandbox ou live).
* `/balance` : solde du compte.

Pour la sandbox Gemini, la signature HMAC n’est pas requise ; le code ci‑dessous
est donc simplifié. En production, il faudra ajouter la génération de la
signature conformément à la documentation Gemini.
"""

import yaml
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Chargement de la configuration
# ---------------------------------------------------------------------------
with open("../config.yaml", "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

BASE_URL = cfg["gemini"]["base_url"]
API_KEY = cfg["gemini"]["api_key"]
API_SECRET = cfg["gemini"]["api_secret"]


def _auth_headers():
    """En-têtes d’authentification simplifiés pour la sandbox.
    En production il faut ajouter le header X‑Gemini‑Payload et la signature
    HMAC‑SHA384.
    """
    return {"Content-Type": "application/json", "X-GEMINI-APIKEY": API_KEY}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.route("/ticker/<pair>", methods=["GET"])
def get_ticker(pair: str):
    """Retourne le ticker public du pair demandé via l’endpoint public de Gemini."""
    resp = requests.get(f"{BASE_URL}/pubticker/{pair}", headers=_auth_headers())
    return jsonify(resp.json())


@app.route("/order", methods=["POST"])
def place_order():
    """Place un ordre market.
    Le corps JSON attendu :
    {
        "symbol": "BTCUSD",
        "amount": "0.001",
        "side": "buy"|"sell",
        "type": "exchange market"
    }
    """
    data = request.json
    # Pour la sandbox, on peut appeler directement l’endpoint /order/new
    resp = requests.post(f"{BASE_URL}/order/new", json=data, headers=_auth_headers())
    return jsonify(resp.json())


@app.route("/balance", methods=["GET"])
def get_balance():
    """Récupère le solde du compte (sandbox)."""
    resp = requests.post(f"{BASE_URL}/balances", json={}, headers=_auth_headers())
    return jsonify(resp.json())


if __name__ == "__main__":
    # Le serveur écoute sur le port 5000 en mode debug – à désactiver en prod
    app.run(host="127.0.0.1", port=5000, debug=True)

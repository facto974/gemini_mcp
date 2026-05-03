"""Exportateur Prometheus pour GeminiMCP‑Trader."""

from prometheus_client import Counter, Gauge, start_http_server

# Compteurs d'événements
orders_total = Counter(
    "gemini_orders_total",
    "Nombre total d'ordres envoyés",
    ["side"]  # buy / sell
)

trades_success = Counter(
    "gemini_trades_success_total",
    "Nombre total de trades exécutés avec succès"
)

trades_failed = Counter(
    "gemini_trades_failed_total",
    "Nombre total de trades échoués"
)

# Gauges d'état
account_balance = Gauge(
    "gemini_account_balance",
    "Solde du compte Gemini (en USD)"
)

cumulative_return = Gauge(
    "gemini_cumulative_return",
    "Rendement cumulé de la stratégie"
)

def start_metrics_server(port: int = 8000):
    """Démarre le serveur HTTP qui expose les métriques sur /metrics."""
    start_http_server(port)
    print(f"[Metrics] Serveur Prometheus démarré sur le port {port}")
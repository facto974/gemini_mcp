# GeminiMCP‑Trader

Stratégie de trading automatisée pour BTC/USD sur Gemini, construite avec le Model Context Protocol (MCP).

## Prérequis
- Python 3.10+
- Clés API Gemini (sandbox ou live) – à placer dans `config.yaml`
- Bibliothèques Python listées dans `requirements.txt`

## Installation
```bash
python -m venv venv
venv\\Scripts\\activate   # sous Windows
pip install -r requirements.txt
```

## Utilisation
### Backtesting
```bash
python -m backtest.backtest
```

### Paper‑trading (sandbox)
```bash
python run_demo.py
```

### Live (après KYC)
Modifiez `sandbox: false` dans `config.yaml` puis lancez `run_demo.py`.

## Structure du projet
```
gemini_mcp/
│   config.yaml
│   requirements.txt
│   README.md
│   run_demo.py
│
├─ server/
│   mcp_server.py
│
├─ strategy/
│   trading_logic.py
│
└─ backtest/
    backtest.py
```

## Licence
MIT – tout est gratuit.

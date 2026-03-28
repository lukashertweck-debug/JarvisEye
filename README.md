# 🤖 J.A.R.V.I.S. — Trading Agent System

> **Just A Rather Very Intelligent System**  
> Multi-Agent Trading Platform powered by free NVIDIA NIM APIs

## Phase 1: Foundation

Ein vollständiges Trading-Agent-System mit:
- **News Agent** — RSS-Feeds + AI Sentiment-Analyse
- **Chart Agent** — Technische Analyse mit 20+ Indikatoren + AI Interpretation
- **Strategy Agent** — Kombiniert alles zu konkreten Trade Signals
- **NVIDIA NIM** — Kostenlose LLM-API (Kimi K2.5, DeepSeek R1, Qwen VLM)
- **CCXT** — Live-Daten von 100+ Exchanges

## ⚡ Quickstart

### 1. Voraussetzungen
- Python 3.10+
- NVIDIA API Key (kostenlos)

### 2. NVIDIA API Key holen
1. Gehe zu https://build.nvidia.com/settings/api-keys
2. Registriere dich (kostenlos)
3. Generiere einen API Key

### 3. Setup
```bash
cd jarvis
pip install -r requirements.txt
cp .env.example .env
# Trage deinen NVIDIA API Key in .env ein
```

### 4. Starten
```bash
python jarvis.py
```

## 📋 Commands

| Command | Beschreibung |
|---------|-------------|
| `briefing` | Komplettes Morning Briefing (News + Chart + Signal) |
| `price BTC/USDT` | Aktueller Preis & 24h Stats |
| `chart BTC/USDT` | Technische Analyse mit AI |
| `mtf BTC/USDT` | Multi-Timeframe Confluence |
| `news BTC` | News + Sentiment-Analyse |
| `signal BTC/USDT` | Trade Signal (Entry, SL, TPs) |
| `scan` | Watchlist-Scan |
| `ask <frage>` | Frag JARVIS alles über Märkte |

## 🏗️ Projektstruktur

```
jarvis/
├── jarvis.py              # Haupt-CLI (das "Hey JARVIS" Interface)
├── requirements.txt
├── .env.example
├── core/
│   ├── nim_client.py      # NVIDIA NIM API Client
│   └── market_data.py     # CCXT Market Data
├── agents/
│   ├── news_agent.py      # News & Sentiment
│   ├── chart_agent.py     # Technical Analysis
│   └── strategy_agent.py  # Signal Generation
└── utils/
    └── indicators.py      # TA Indikatoren
```

## 🔮 Roadmap

- **Phase 2**: Vision-Analyse (Chart-Screenshots → Qwen VLM)
- **Phase 3**: Custom Strategy Rules (APEX Confluence System)
- **Phase 4**: Auto-Execution via CCXT + Telegram Alerts
- **Phase 5**: Cowork Integration + `/loop` Scheduled Scans

## 💰 Kosten

| Komponente | Kosten |
|-----------|--------|
| NVIDIA NIM API | **Kostenlos** |
| CCXT | Open Source |
| Python + Libraries | Open Source |
| Exchange-Daten | Kostenlos (public API) |

---
*Built with Claude Code + NVIDIA NIM*

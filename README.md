# IndianMarket 🇮🇳

**Multi-Agent Equity Research System for the Indian Stock Market (NSE/BSE)**

Parallel specialized agents gather market data, fundamentals, technicals, news, FII/DII flows, Reddit sentiment and Screener.in insights — then synthesize a structured research report (Markdown + PDF). Includes a Streamlit dashboard and portfolio mode.

## Features

| Agent | What it does |
|-------|--------------|
| **Market Data** | Live & historical prices, volume, returns (yfinance) |
| **Fundamental** | Valuation, profitability, balance-sheet health |
| **Screener.in** | Top ratios, pros/cons from public Screener pages |
| **Technical** | RSI, MACD, SMAs, support/resistance, trend bias |
| **News** | Recent headlines & summaries |
| **FII / DII** | Latest institutional cash flows (NSE-sourced) |
| **Sentiment** | Reddit (r/IndiaInvestments, r/IndianStreetBets) keyword sentiment |
| **Macro & Risk** | India macro factors + risk checklist |
| **Synthesis** | Combines everything → structured research report |

- **Parallel execution** (LangGraph-style fan-out → synthesis)
- **Portfolio mode** (comma-separated tickers)
- **Streamlit interactive dashboard**
- **PDF export**

## Quick Start

```bash
git clone https://github.com/DineshGupta-cloud/IndianMarket.git
cd IndianMarket
pip install -r requirements.txt

# Single stock
python main.py RELIANCE
python main.py TCS --pdf

# Portfolio
python main.py RELIANCE,TCS,INFY --pdf

# Streamlit dashboard
streamlit run streamlit_app.py
```

Reports land in `reports/` (Markdown + PDF when requested).

## Project Structure

```
IndianMarket/
├── agents/
│   ├── market_data.py
│   ├── fundamental.py
│   ├── screener.py          # Screener.in enrichment
│   ├── technical.py
│   ├── news.py
│   ├── fii_dii.py
│   ├── sentiment.py         # Reddit sentiment
│   ├── macro_risk.py
│   ├── synthesis.py
│   └── orchestrator.py      # Parallel + portfolio mode
├── utils/pdf_export.py
├── reports/
├── main.py
├── streamlit_app.py
├── requirements.txt
└── README.md
```

## Supported Tickers

NSE symbols (`.NS` appended automatically):

`RELIANCE` · `TCS` · `INFY` · `HDFCBANK` · `ICICIBANK` · `SBIN` · `BHARTIARTL` · `ITC` · `LT` · `HINDUNILVR` …

## Roadmap

- [x] FII/DII flows
- [x] Parallel (LangGraph-style) agents
- [x] Streamlit dashboard
- [x] PDF export
- [x] Reddit social sentiment
- [x] Screener.in enrichment
- [x] Multi-stock portfolio mode
- [ ] X/Twitter sentiment (API key optional)
- [ ] Full LangGraph + LLM reasoning layer
- [ ] Watchlist alerts

## Disclaimer

Educational / research tool only. **Not financial advice.** Always do your own due diligence and consult a SEBI-registered advisor.

---
Built for the Indian markets 🇮🇳

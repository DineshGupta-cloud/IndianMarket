# IndianMarket 🇮🇳

**Multi-Agent Equity Research System for the Indian Stock Market (NSE/BSE)**

A modular, agent-based research platform that analyzes Indian listed companies using specialized agents running in parallel, then synthesizes a clear research report (Markdown + optional PDF). Includes a Streamlit dashboard.

## Features

| Agent | What it does |
|-------|--------------|
| **Market Data** | Live & historical prices, volume, returns (yfinance) |
| **Fundamental** | Valuation, profitability, balance-sheet health |
| **Technical** | RSI, MACD, SMAs, support/resistance, trend bias |
| **News** | Recent headlines & summaries |
| **FII / DII** | Latest institutional cash flows (NSE-sourced) |
| **Sentiment** | Placeholder (ready for X/Reddit later) |
| **Macro & Risk** | India macro factors + risk checklist |
| **Synthesis** | Combines everything → structured research report |

- **Parallel execution** (LangGraph-style fan-out → synthesis)
- **Streamlit interactive dashboard**
- **PDF export**

## Quick Start

```bash
git clone https://github.com/DineshGupta-cloud/IndianMarket.git
cd IndianMarket
pip install -r requirements.txt

# CLI
python main.py RELIANCE
python main.py TCS --pdf
python main.py HDFCBANK --period 2y --pdf

# Streamlit dashboard
streamlit run streamlit_app.py
```

Reports are saved in the `reports/` folder (Markdown + PDF when requested).

## Project Structure

```
IndianMarket/
├── agents/                 # Specialized research agents
│   ├── market_data.py
│   ├── fundamental.py
│   ├── technical.py
│   ├── news.py
│   ├── fii_dii.py          # NEW – institutional flows
│   ├── sentiment.py
│   ├── macro_risk.py
│   ├── synthesis.py
│   └── orchestrator.py     # Parallel fan-out + synthesis
├── utils/
│   └── pdf_export.py       # Markdown → PDF
├── reports/               # Generated reports
├── main.py                # CLI
├── streamlit_app.py       # Interactive dashboard
├── requirements.txt
└── README.md
```

## Supported Tickers

Use NSE symbols (system appends `.NS` automatically):

`RELIANCE` · `TCS` · `INFY` · `HDFCBANK` · `ICICIBANK` · `SBIN` · `BHARTIARTL` · `ITC` · `LT` · `HINDUNILVR` …

## Roadmap

- [x] FII/DII flows
- [x] Parallel (LangGraph-style) agents
- [x] Streamlit dashboard
- [x] PDF export
- [ ] Deeper Screener.in fundamentals
- [ ] Real X/Twitter + Reddit sentiment
- [ ] Full LangGraph / LLM reasoning layer
- [ ] Portfolio multi-stock mode

## Disclaimer

This is a research and educational tool only. **Not financial advice.** Always do your own due diligence and consult a SEBI-registered advisor.

---
Built for the Indian markets 🇮🇳

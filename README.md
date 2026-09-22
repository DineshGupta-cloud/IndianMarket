# IndianMarket 🇮🇳

**Multi-Agent Equity Research System for the Indian Stock Market (NSE/BSE)**

**One app for everything** — single stock, portfolio, reports, PDF.

Parallel agents gather market data, fundamentals, technicals, news, FII/DII flows, Reddit sentiment and Screener.in insights, then synthesize a research report.

## Quick Start (only command you need)

```bash
git clone https://github.com/DineshGupta-cloud/IndianMarket.git
cd IndianMarket

python -m venv venv
# Windows:  venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

pip install -r requirements.txt

streamlit run app.py
```

Open the browser → choose **Single Stock** or **Portfolio** → enter ticker(s) → **Run Research**.

That’s it. One entry point for all features.

---

## What the app does

| Mode | Example input | Result |
|------|---------------|--------|
| Single Stock | `RELIANCE` | Full multi-agent report |
| Portfolio | `RELIANCE,TCS,INFY` | Summary table + report per stock |

- Parallel agents (market, fundamental, screener, technical, news, FII/DII, sentiment, macro)
- Markdown report + optional PDF download
- Reports also saved under `reports/`

## Optional: CLI (for scripts / automation)

```bash
python main.py RELIANCE --pdf
python main.py RELIANCE,TCS,INFY --pdf
```

## Project structure

```
IndianMarket/
├── app.py                 ← START HERE (single Streamlit app)
├── main.py                ← optional CLI
├── streamlit_app.py       ← legacy (same as app.py flow)
├── agents/                ← research agents
├── utils/pdf_export.py
├── reports/
├── requirements.txt
└── README.md
```

## Supported tickers

NSE symbols (`.NS` added automatically):

`RELIANCE` · `TCS` · `INFY` · `HDFCBANK` · `ICICIBANK` · `SBIN` · `BHARTIARTL` · `ITC` · `LT` · …

## Disclaimer

Educational / research tool only. **Not financial advice.** Do your own due diligence and consult a SEBI-registered advisor.

---
Built for the Indian markets 🇮🇳

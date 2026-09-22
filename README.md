# IndianMarket 🇮🇳

**Multi-Agent Equity Research System for the Indian Stock Market (NSE/BSE)**

A modular, agent-based research platform that analyzes Indian listed companies using specialized agents for market data, fundamentals, technicals, news, sentiment, and macro risks — then synthesizes everything into a clear research report.

## Features

- **Market Data Agent** – Live & historical prices, volume, returns (via yfinance)
- **Fundamental Agent** – Key ratios, financial health, valuation metrics
- **Technical Agent** – RSI, MACD, Moving Averages, support/resistance levels
- **News & Events Agent** – Recent news and corporate developments
- **Sentiment Agent** – Placeholder for social & analyst sentiment (extensible)
- **Macro & Risk Agent** – High-level sector and macro context
- **Synthesis Agent** – Combines all inputs into a structured research report

## Quick Start

```bash
# Clone
git clone https://github.com/DineshGupta-cloud/IndianMarket.git
cd IndianMarket

# Install dependencies
pip install -r requirements.txt

# Run research on a stock (NSE ticker without .NS)
python main.py RELIANCE
python main.py TCS
python main.py HDFCBANK
```

Reports are saved in the `reports/` folder as Markdown.

## Project Structure

```
IndianMarket/
├── agents/              # Specialized research agents
├── data/                # Data fetchers (yfinance, etc.)
├── utils/               # Helpers
├── reports/             # Generated research reports
├── main.py              # CLI entry point
├── requirements.txt
└── README.md
```

## Supported Tickers

Use NSE symbols (the system automatically appends `.NS`):

- `RELIANCE`, `TCS`, `INFY`, `HDFCBANK`, `ICICIBANK`, `SBIN`, `BHARTIARTL`, `ITC`, `LT`, `HINDUNILVR`, etc.

## Roadmap

- [ ] Deeper Screener.in / NSE fundamentals integration
- [ ] Real-time news scraping + RSS feeds
- [ ] X/Twitter & Reddit sentiment analysis
- [ ] FII/DII flow tracking
- [ ] LangGraph / CrewAI orchestration
- [ ] Streamlit / Gradio interactive dashboard
- [ ] PDF report generation
- [ ] Portfolio-level multi-stock analysis

## Disclaimer

This is a research and educational tool only. Not financial advice. Always do your own due diligence.

---
Built for the Indian markets 🇮🇳

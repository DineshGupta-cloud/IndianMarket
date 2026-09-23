# IndianMarket 🇮🇳

**Multi-Agent Equity Research System for the Indian Stock Market (NSE/BSE)**

**One app for everything** — single stock, portfolio, optional LLM thesis, PDF reports.

## Quick Start

```bash
git clone https://github.com/DineshGupta-cloud/IndianMarket.git
cd IndianMarket

python -m venv venv
# Windows:  venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

## Optional: LLM-powered synthesis

Without a key, reports use **rule-based** bias (always works).

With a key, the Synthesis agent adds an **LLM investment thesis** (bull/bear cases, risks, confidence).

### Recommended: free Groq key
1. Create a key at [console.groq.com](https://console.groq.com/)
2. Either:
   - Paste it in the Streamlit sidebar, **or**
   - Set env var and restart:

```bash
# Windows (PowerShell)
$env:GROQ_API_KEY="your_key_here"

# Mac/Linux
export GROQ_API_KEY="your_key_here"
```

Also supported: `OPENAI_API_KEY`, `LLM_API_KEY`, custom OpenAI-compatible `LLM_BASE_URL` + `LLM_MODEL`.

### CLI examples

```bash
python main.py RELIANCE --pdf
python main.py RELIANCE --llm-key YOUR_KEY --pdf
python main.py RELIANCE,TCS --no-llm
```

## Features

| Agent | Role |
|-------|------|
| Market Data | Prices, volume, returns |
| Fundamental | Valuation & quality (yfinance) |
| Screener.in | Top ratios, pros/cons |
| Technical | RSI, MACD, SMAs, S/R |
| News | Recent headlines |
| FII/DII | Institutional cash flows |
| Sentiment | Reddit keyword sentiment |
| Macro & Risk | India checklist |
| Synthesis | Rules + **optional LLM thesis** |

## Disclaimer

Educational tool only. **Not financial advice.** Consult a SEBI-registered advisor.

---
Built for the Indian markets 🇮🇳

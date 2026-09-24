# IndianMarket 🇮🇳

Multi-agent NSE/BSE research — **one dashboard** with charts, EMA50/SMA200 crossover dates, portfolios, alerts, and BUY/SELL/HOLD.

## Run

```bash
git clone https://github.com/DineshGupta-cloud/IndianMarket.git
cd IndianMarket
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Single dashboard (`app.py`)

| Section | What it does |
|--------|----------------|
| **Chart** | Close + EMA50 + SMA200 for searched ticker |
| **Last cross date** | When EMA50 last crossed SMA200 |
| **MA scan board** | All symbols in universe + crossover date column |
| **Research** | Multi-agent report + technical BUY/SELL/HOLD |
| **Quick alerts** | Price, RSI, MA cross alerts |
| **Portfolios** | SQLite saved lists |

### Sidebar
- Search ticker
- Period
- MA scan universe: Suggested stocks / Portfolio / Custom
- Optional LLM key (or `.env` `GROQ_API_KEY`)

## Optional `.env`

```text
GROQ_API_KEY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

Copy from `.env.example`. Never commit real secrets.

## CLI (optional)

```bash
python main.py RELIANCE --pdf
```

## Disclaimer

Educational only. **Not financial advice.**

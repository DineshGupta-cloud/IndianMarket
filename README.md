# IndianMarket

**Equity research terminal for NSE/BSE** — multi-agent analysis, charts, MA crossovers with dates, portfolios, and alerts.

Premium single-page dashboard designed like a modern fintech product.

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

Open **http://localhost:8501**

## Dashboard

| Area | Features |
|------|----------|
| **Overview** | Price chart, EMA50, SMA200, crossover date |
| **Screening** | Universe MA board with dates |
| **Intelligence** | Multi-agent research + BUY/SELL/HOLD |
| **Monitoring** | Price / RSI / MA alerts |
| **Portfolios** | SQLite saved lists |

## Optional `.env`

```text
GROQ_API_KEY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

## Disclaimer

Educational only. **Not financial advice.**

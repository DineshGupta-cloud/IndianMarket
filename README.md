# IndianMarket 🇮🇳

Multi-agent NSE/BSE research + **portfolios (SQLite)** + **watchlist alerts**.

## Run

```bash
git pull
pip install -r requirements.txt
streamlit run app.py
```

### Tabs
| Tab | What it does |
|-----|----------------|
| **Research** | Single stock or ad-hoc list |
| **My Portfolios** | Create / add stocks / research (saved in SQLite) |
| **Alerts** | Price, day %, RSI scan on portfolio or custom list |
| **Stock list** | Suggested tickers |

### Example portfolios (first run)
- **Core Long Term** — RELIANCE, TCS, HDFCBANK, INFY  
- **Banking Basket** — HDFCBANK, ICICIBANK, SBIN, KOTAKBANK  
- **Watchlist** — ITC, LT, BHARTIARTL, SUNPHARMA  

DB: `data/portfolios.db`

### Alerts
Scan a portfolio or custom tickers for:
- Price above / below a level  
- Day move beyond ±X%  
- RSI overbought / oversold  

### Optional LLM
`.env` file:
```text
GROQ_API_KEY=gsk_your_key
```
https://console.groq.com/

## Disclaimer
Educational only. Not financial advice.

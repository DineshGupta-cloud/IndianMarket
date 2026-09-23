# IndianMarket 🇮🇳

Multi-agent equity research for NSE/BSE + **saved portfolios (SQLite)**.

## Run

```bash
git pull
pip install -r requirements.txt
streamlit run app.py
```

### Tabs
1. **Research** — single stock or ad-hoc list  
2. **My Portfolios** — create / add stocks / research saved portfolios  
3. **Stock list** — suggested NSE tickers  

### Example portfolios (auto-created first run)
| Portfolio | Stocks |
|-----------|--------|
| **Core Long Term** | RELIANCE, TCS, HDFCBANK, INFY |
| **Banking Basket** | HDFCBANK, ICICIBANK, SBIN, KOTAKBANK |
| **Watchlist** | ITC, LT, BHARTIARTL, SUNPHARMA |

Storage: `data/portfolios.db` (local SQLite). Export JSON backup from the Portfolios tab.

### Optional LLM
Create `.env`:
```text
GROQ_API_KEY=gsk_your_key
```
Free key: https://console.groq.com/

## Disclaimer
Educational only. Not financial advice.

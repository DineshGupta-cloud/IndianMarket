# IndianMarket 🇮🇳

Multi-agent NSE/BSE research + portfolios + alerts (RSI divergence) + optional Telegram.

## Run

```bash
git pull
pip install -r requirements.txt
streamlit run app.py
```

## Telegram notifications (safe setup)

**Do not put bot tokens in code or GitHub.**

1. Open `.env` in the project folder (create from `.env.example` if needed):

```text
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

2. Test:

```bash
python scripts/test_telegram.py
```

3. In the app **Alerts** tab, run a scan and enable **Send to Telegram** (if shown) or messages will use the same helper.

If you ever pasted a token in chat, **revoke it in BotFather** and create a new one.

## RSI divergence

Technical agent + alerts detect:
- Regular bullish / bearish
- Hidden bullish / bearish

Shown in research reports and alert scans.

## Optional LLM

```text
GROQ_API_KEY=gsk_...
```

## Disclaimer

Educational only. Not financial advice.

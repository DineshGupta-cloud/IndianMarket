# IndianMarket 🇮🇳

**Multi-Agent Equity Research for NSE/BSE** — one app for single stock, portfolio, optional LLM thesis, PDF.

## Run the app

```bash
git clone https://github.com/DineshGupta-cloud/IndianMarket.git
cd IndianMarket
python -m venv venv

# Windows:  venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

## Easiest way to add Groq LLM (one-time)

1. Get a free key: https://console.groq.com/ → API Keys → Create
2. In the project folder, create a file named **`.env`** with only this line:

```text
GROQ_API_KEY=gsk_your_key_here
```

3. Run:

```bash
streamlit run app.py
```

That’s it. The app loads the key automatically.  
**Do not** put the key on GitHub. `.env` is already ignored.

Windows (create file quickly):
```powershell
copy .env.example .env
notepad .env
```

Mac/Linux:
```bash
cp .env.example .env
nano .env
```

Without a key, research still works (rule-based synthesis only).

## CLI (optional)

```bash
python main.py RELIANCE --pdf
python main.py RELIANCE,TCS,INFY --pdf
```

## Disclaimer

Educational only. **Not financial advice.**

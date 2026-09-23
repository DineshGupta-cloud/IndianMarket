"""
Quick Telegram test (uses .env — never hardcode tokens).

  1. Put in .env:
       TELEGRAM_BOT_TOKEN=...
       TELEGRAM_CHAT_ID=...
  2. Run:  python scripts/test_telegram.py
"""

from utils.telegram_notify import is_telegram_configured, send_telegram_message


def main():
    if not is_telegram_configured():
        print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env first.")
        return
    r = send_telegram_message("🇮🇳 IndianMarket test: Telegram notifications are working.")
    print(r)


if __name__ == "__main__":
    main()

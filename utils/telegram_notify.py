"""
Send Telegram messages via Bot API.

NEVER hardcode tokens in source. Use .env:

  TELEGRAM_BOT_TOKEN=...
  TELEGRAM_CHAT_ID=...

Requires: pip install requests  (already in requirements)
"""

from __future__ import annotations

import os
from typing import Optional

import requests

from utils.env_loader import load_env

load_env()


def get_telegram_config(
    bot_token: Optional[str] = None,
    chat_id: Optional[str] = None,
) -> dict:
    load_env()
    token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN") or ""
    chat = chat_id or os.getenv("TELEGRAM_CHAT_ID") or ""
    return {"bot_token": token.strip(), "chat_id": str(chat).strip()}


def is_telegram_configured(
    bot_token: Optional[str] = None,
    chat_id: Optional[str] = None,
) -> bool:
    cfg = get_telegram_config(bot_token, chat_id)
    return bool(cfg["bot_token"] and cfg["chat_id"])


def send_telegram_message(
    text: str,
    bot_token: Optional[str] = None,
    chat_id: Optional[str] = None,
    timeout: int = 15,
) -> dict:
    """
    POST https://api.telegram.org/bot<token>/sendMessage
    Returns {"ok": bool, "response": ..., "error": ...}
    """
    cfg = get_telegram_config(bot_token, chat_id)
    if not cfg["bot_token"] or not cfg["chat_id"]:
        return {
            "ok": False,
            "error": "TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set",
        }

    url = f"https://api.telegram.org/bot{cfg['bot_token']}/sendMessage"
    data = {
        "chat_id": cfg["chat_id"],
        "text": text,
        "disable_web_page_preview": True,
    }
    try:
        r = requests.post(url, data=data, timeout=timeout)
        body = r.text
        ok = r.status_code == 200 and '"ok":true' in body.replace(" ", "").lower()
        # Telegram returns JSON {"ok": true/false}
        try:
            j = r.json()
            ok = bool(j.get("ok"))
            if not ok:
                return {"ok": False, "error": j.get("description", body), "response": j}
            return {"ok": True, "response": j}
        except Exception:
            return {"ok": ok, "response": body, "error": None if ok else body}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def format_alert_message(rows: list) -> str:
    """Build a readable Telegram text from alert scan rows."""
    lines = ["🇮🇳 IndianMarket Alerts", ""]
    triggered = [r for r in rows if r.get("alerts")]
    if not triggered:
        lines.append("No alerts fired.")
        return "\n".join(lines)

    for r in triggered:
        lines.append(
            f"*{r.get('ticker')}* ₹{r.get('price')} ({r.get('day_change_pct', 0):+.2f}%) "
            f"RSI {r.get('rsi_14', 'N/A')}"
        )
        for a in r.get("alerts") or []:
            lines.append(f"  ⚠ {a}")
        lines.append("")
    return "\n".join(lines)

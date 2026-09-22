from typing import Any, Dict
import yfinance as yf
from .base import BaseAgent


class NewsAgent(BaseAgent):
    name = "NewsAgent"

    def run(self) -> Dict[str, Any]:
        self.log(f"Fetching recent news for {self.ns_ticker}...")

        try:
            stock = yf.Ticker(self.ns_ticker)
            news_items = stock.news or []

            parsed = []
            for item in news_items[:8]:  # limit to recent 8
                content = item.get("content", {}) if isinstance(item.get("content"), dict) else {}
                title = (
                    item.get("title")
                    or content.get("title")
                    or item.get("headline")
                    or "No title"
                )
                publisher = (
                    item.get("publisher")
                    or content.get("provider", {}).get("displayName")
                    or "Unknown"
                )
                link = (
                    item.get("link")
                    or content.get("canonicalUrl", {}).get("url")
                    or item.get("url")
                )
                summary = content.get("summary") or item.get("summary") or ""

                parsed.append({
                    "title": title,
                    "publisher": publisher,
                    "link": link,
                    "summary": summary[:300] if summary else None,
                })

            result = {
                "ticker": self.ticker,
                "news_count": len(parsed),
                "items": parsed,
            }

            self.log(f"Found {len(parsed)} recent news items")
            return result

        except Exception as e:
            self.log(f"Error: {e}")
            return {"error": str(e), "ticker": self.ticker, "items": []}

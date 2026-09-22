from typing import Any, Dict, List, Optional
import requests
from bs4 import BeautifulSoup
from .base import BaseAgent


class ScreenerAgent(BaseAgent):
    """
    Lightweight enrichment from Screener.in public company pages.
    Extracts top ratios, pros/cons, and shareholding hints.
    Respects timeouts; fails gracefully if blocked.
    """
    name = "ScreenerAgent"

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; IndianMarketResearchBot/1.0; "
            "+https://github.com/DineshGupta-cloud/IndianMarket)"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    def run(self) -> Dict[str, Any]:
        self.log(f"Fetching Screener.in data for {self.ticker}...")

        urls = [
            f"https://www.screener.in/company/{self.ticker}/consolidated/",
            f"https://www.screener.in/company/{self.ticker}/",
        ]

        html = None
        used_url = None
        for url in urls:
            try:
                resp = requests.get(url, headers=self.HEADERS, timeout=15)
                if resp.status_code == 200 and "company" in resp.url:
                    html = resp.text
                    used_url = resp.url
                    break
            except Exception:
                continue

        if not html:
            self.log("Could not load Screener.in page")
            return {
                "ticker": self.ticker,
                "error": "Screener.in page unavailable",
                "note": "Falling back to yfinance fundamentals only.",
            }

        try:
            soup = BeautifulSoup(html, "html.parser")

            # Company name
            name_tag = soup.find("h1")
            company_name = name_tag.get_text(strip=True) if name_tag else self.ticker

            # Top ratios (ul#top-ratios li)
            top_ratios: Dict[str, str] = {}
            ratios_ul = soup.select_one("#top-ratios") or soup.select_one("ul#top-ratios")
            if ratios_ul:
                for li in ratios_ul.select("li"):
                    name_el = li.select_one("span.name") or li.select_one(".name")
                    val_el = li.select_one("span.number") or li.select_one(".number")
                    if name_el and val_el:
                        top_ratios[name_el.get_text(strip=True)] = val_el.get_text(strip=True)

            # Pros & Cons
            pros: List[str] = []
            cons: List[str] = []
            for box in soup.select(".pros, .cons, div.card"):
                heading = box.find(["h3", "h4", "strong"])
                if not heading:
                    continue
                htext = heading.get_text(strip=True).lower()
                items = [li.get_text(strip=True) for li in box.select("li")]
                if "pro" in htext:
                    pros.extend(items)
                elif "con" in htext:
                    cons.extend(items)

            # About / description
            about = None
            about_el = soup.select_one(".company-info p") or soup.select_one("#company-info p")
            if about_el:
                about = about_el.get_text(strip=True)[:600]

            result = {
                "ticker": self.ticker,
                "company_name": company_name,
                "source_url": used_url,
                "top_ratios": top_ratios,
                "pros": pros[:8],
                "cons": cons[:8],
                "about": about,
                "note": "Data scraped from public Screener.in company page for educational use.",
            }

            self.log(f"Got {len(top_ratios)} ratios, {len(pros)} pros, {len(cons)} cons")
            return result

        except Exception as e:
            self.log(f"Parse error: {e}")
            return {"ticker": self.ticker, "error": str(e)}

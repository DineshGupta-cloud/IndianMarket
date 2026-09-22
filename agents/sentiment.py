from typing import Any, Dict, List
import requests
import re
from .base import BaseAgent


class SentimentAgent(BaseAgent):
    """
    Social sentiment from Reddit (r/IndiaInvestments, r/IndianStreetBets)
    using public JSON endpoints. No API key required.
    """
    name = "SentimentAgent"

    SUBREDDITS = ["IndiaInvestments", "IndianStreetBets"]
    HEADERS = {
        "User-Agent": "IndianMarketResearchBot/1.0 (educational research tool)"
    }

    POSITIVE = {
        "buy", "bullish", "long", "accumulate", "undervalued", "strong", "growth",
        "breakout", "moon", "upside", "opportunity", "outperform", "positive", "good",
        "great", "solid", "cheap", "value", "sip", "hold",
    }
    NEGATIVE = {
        "sell", "bearish", "short", "overvalued", "weak", "crash", "downside",
        "avoid", "risk", "debt", "fraud", "scam", "negative", "bad", "poor",
        "expensive", "bubble", "exit", "cut",
    }

    def run(self) -> Dict[str, Any]:
        self.log(f"Fetching Reddit sentiment for {self.ticker}...")

        posts: List[Dict] = []
        errors = []

        for sub in self.SUBREDDITS:
            try:
                # Search within subreddit
                url = f"https://www.reddit.com/r/{sub}/search.json"
                params = {
                    "q": self.ticker,
                    "restrict_sr": "1",
                    "sort": "new",
                    "limit": 15,
                    "t": "month",
                }
                resp = requests.get(url, params=params, headers=self.HEADERS, timeout=12)
                if resp.status_code != 200:
                    errors.append(f"r/{sub}: HTTP {resp.status_code}")
                    continue

                data = resp.json()
                children = data.get("data", {}).get("children", [])
                for child in children:
                    d = child.get("data", {})
                    title = d.get("title", "")
                    selftext = (d.get("selftext") or "")[:400]
                    posts.append({
                        "subreddit": sub,
                        "title": title,
                        "snippet": selftext,
                        "score": d.get("score", 0),
                        "num_comments": d.get("num_comments", 0),
                        "url": f"https://reddit.com{d.get('permalink', '')}",
                        "created_utc": d.get("created_utc"),
                    })
            except Exception as e:
                errors.append(f"r/{sub}: {e}")

        # Simple keyword sentiment score
        pos_hits = 0
        neg_hits = 0
        for p in posts:
            text = (p["title"] + " " + p["snippet"]).lower()
            tokens = set(re.findall(r"[a-z]+", text))
            pos_hits += len(tokens & self.POSITIVE)
            neg_hits += len(tokens & self.NEGATIVE)

        if pos_hits + neg_hits == 0:
            label = "Neutral / Low discussion"
            score = 0.0
        else:
            score = (pos_hits - neg_hits) / (pos_hits + neg_hits)
            if score > 0.25:
                label = "Net Positive"
            elif score < -0.25:
                label = "Net Negative"
            else:
                label = "Mixed / Neutral"

        result = {
            "ticker": self.ticker,
            "status": "ok" if posts else "no_posts",
            "post_count": len(posts),
            "sentiment_label": label,
            "sentiment_score": round(score, 3),
            "positive_hits": pos_hits,
            "negative_hits": neg_hits,
            "top_posts": sorted(posts, key=lambda x: x.get("score", 0), reverse=True)[:8],
            "sources": [f"r/{s}" for s in self.SUBREDDITS],
            "errors": errors,
            "note": (
                "Sentiment derived from recent Reddit posts mentioning the ticker "
                "in r/IndiaInvestments and r/IndianStreetBets (keyword heuristic)."
            ),
        }

        self.log(f"{len(posts)} posts | Sentiment: {label} (score {score:.2f})")
        return result

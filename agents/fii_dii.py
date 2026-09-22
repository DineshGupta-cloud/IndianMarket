from typing import Any, Dict
import requests
from .base import BaseAgent


class FIIDIIAgent(BaseAgent):
    """
    Fetches latest and recent FII/DII cash market flows.
    Source: free public API (fii-diidata.mrchartist.com) sourced from NSE.
    """
    name = "FIIDIIAgent"

    BASE = "https://fii-diidata.mrchartist.com"

    def run(self) -> Dict[str, Any]:
        self.log("Fetching FII/DII institutional flows...")

        try:
            # Latest session
            latest_resp = requests.get(f"{self.BASE}/api/data", timeout=15)
            latest_resp.raise_for_status()
            latest = latest_resp.json()

            # Recent history (last ~60 sessions)
            hist_resp = requests.get(f"{self.BASE}/api/history", timeout=15)
            hist_resp.raise_for_status()
            history = hist_resp.json()

            # Normalize fields (API uses both long and short keys)
            fii_net = latest.get("fii_net") or latest.get("fn")
            dii_net = latest.get("dii_net") or latest.get("dn")
            fii_buy = latest.get("fii_buy") or latest.get("fb")
            fii_sell = latest.get("fii_sell") or latest.get("fs")
            dii_buy = latest.get("dii_buy") or latest.get("db")
            dii_sell = latest.get("dii_sell") or latest.get("ds")
            date_str = latest.get("date") or latest.get("d") or "Latest"

            # Simple sentiment from net flows
            if fii_net is not None and dii_net is not None:
                if fii_net > 0 and dii_net > 0:
                    flow_bias = "Both FII & DII buying (supportive)"
                elif fii_net < 0 and dii_net > 0:
                    flow_bias = "FII selling, DII absorbing (classic domestic support)"
                elif fii_net > 0 and dii_net < 0:
                    flow_bias = "FII buying, DII selling"
                else:
                    flow_bias = "Both FII & DII selling (cautious)"
            else:
                flow_bias = "Data incomplete"

            # Last 5 sessions summary
            recent = []
            if isinstance(history, list):
                for row in history[:5]:
                    recent.append({
                        "date": row.get("date") or row.get("d"),
                        "fii_net": row.get("fii_net") or row.get("fn"),
                        "dii_net": row.get("dii_net") or row.get("dn"),
                    })

            result = {
                "ticker": self.ticker,  # market-wide, not stock-specific
                "as_of": date_str,
                "latest": {
                    "fii_buy": fii_buy,
                    "fii_sell": fii_sell,
                    "fii_net": fii_net,
                    "dii_buy": dii_buy,
                    "dii_sell": dii_sell,
                    "dii_net": dii_net,
                },
                "flow_bias": flow_bias,
                "recent_5_sessions": recent,
                "note": "FII/DII data is market-wide (NSE cash). Useful context for overall institutional sentiment.",
            }

            self.log(f"As of {date_str}: FII net {fii_net} Cr | DII net {dii_net} Cr → {flow_bias}")
            return result

        except Exception as e:
            self.log(f"Error fetching FII/DII: {e}")
            return {
                "error": str(e),
                "ticker": self.ticker,
                "note": "Could not fetch FII/DII data. Continuing without it.",
            }

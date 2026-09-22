from typing import Any, Dict
import yfinance as yf
import pandas as pd
from .base import BaseAgent


class MarketDataAgent(BaseAgent):
    name = "MarketDataAgent"

    def run(self) -> Dict[str, Any]:
        self.log(f"Fetching market data for {self.ns_ticker}...")
        period = self.context.get("period", "1y")

        try:
            stock = yf.Ticker(self.ns_ticker)
            info = stock.info or {}
            hist = stock.history(period=period)

            if hist.empty:
                self.log("No historical data found.")
                return {"error": "No data available", "ticker": self.ticker}

            latest = hist.iloc[-1]
            prev_close = hist.iloc[-2]["Close"] if len(hist) > 1 else latest["Close"]

            # Basic performance metrics
            returns = {}
            for label, days in [("1W", 5), ("1M", 21), ("3M", 63), ("6M", 126), ("1Y", 252)]:
                if len(hist) > days:
                    past = hist.iloc[-days]["Close"]
                    returns[label] = round(((latest["Close"] - past) / past) * 100, 2)

            result = {
                "ticker": self.ticker,
                "ns_ticker": self.ns_ticker,
                "company_name": info.get("longName") or info.get("shortName") or self.ticker,
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "currency": info.get("currency", "INR"),
                "current_price": round(float(latest["Close"]), 2),
                "previous_close": round(float(prev_close), 2),
                "day_change_pct": round(((latest["Close"] - prev_close) / prev_close) * 100, 2),
                "volume": int(latest["Volume"]),
                "avg_volume": int(info.get("averageVolume") or hist["Volume"].mean()),
                "market_cap": info.get("marketCap"),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
                "returns": returns,
                "history_tail": hist.tail(5)[["Open", "High", "Low", "Close", "Volume"]].round(2).to_dict(),
            }

            self.log(f"Price: ₹{result['current_price']} ({result['day_change_pct']:+.2f}%)")
            return result

        except Exception as e:
            self.log(f"Error: {e}")
            return {"error": str(e), "ticker": self.ticker}

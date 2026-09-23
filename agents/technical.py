from typing import Any, Dict
import yfinance as yf
import pandas as pd
from .base import BaseAgent
from utils.divergence import compute_rsi_series, detect_rsi_divergence


class TechnicalAgent(BaseAgent):
    name = "TechnicalAgent"

    def run(self) -> Dict[str, Any]:
        self.log(f"Running technical analysis for {self.ns_ticker}...")
        period = self.context.get("period", "1y")

        try:
            stock = yf.Ticker(self.ns_ticker)
            hist = stock.history(period=period)

            if hist.empty or len(hist) < 50:
                return {"error": "Insufficient data for technicals", "ticker": self.ticker}

            close = hist["Close"]
            volume = hist["Volume"]

            sma_20 = close.rolling(20).mean().iloc[-1]
            sma_50 = close.rolling(50).mean().iloc[-1]
            sma_200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else None
            ema_12 = close.ewm(span=12).mean().iloc[-1]
            ema_26 = close.ewm(span=26).mean().iloc[-1]

            rsi_series = compute_rsi_series(close, 14)
            rsi = float(rsi_series.iloc[-1])

            macd_line = ema_12 - ema_26
            signal_line = (
                pd.Series(close.ewm(span=12).mean() - close.ewm(span=26).mean())
                .ewm(span=9)
                .mean()
                .iloc[-1]
            )
            macd_hist = macd_line - signal_line

            recent = hist.tail(60)
            support = round(float(recent["Low"].min()), 2)
            resistance = round(float(recent["High"].max()), 2)

            current = float(close.iloc[-1])

            trend = "Neutral"
            if sma_50 and current > sma_50 and (sma_200 is None or current > sma_200):
                trend = "Bullish"
            elif sma_50 and current < sma_50 and (sma_200 is None or current < sma_200):
                trend = "Bearish"

            rsi_signal = "Neutral"
            if rsi > 70:
                rsi_signal = "Overbought"
            elif rsi < 30:
                rsi_signal = "Oversold"

            # RSI divergence (regular + hidden)
            divergence = detect_rsi_divergence(close, rsi_series, order=5)

            result = {
                "ticker": self.ticker,
                "current_price": round(current, 2),
                "sma_20": round(float(sma_20), 2),
                "sma_50": round(float(sma_50), 2),
                "sma_200": round(float(sma_200), 2) if sma_200 is not None else None,
                "rsi_14": round(rsi, 2),
                "rsi_signal": rsi_signal,
                "macd": round(float(macd_line), 2),
                "macd_signal": round(float(signal_line), 2),
                "macd_hist": round(float(macd_hist), 2),
                "support_60d": support,
                "resistance_60d": resistance,
                "trend_bias": trend,
                "price_vs_sma50": "Above" if current > sma_50 else "Below",
                "volume_trend": (
                    "Higher than average"
                    if volume.iloc[-1] > volume.tail(20).mean()
                    else "Lower than average"
                ),
                "rsi_divergence": divergence,
            }

            div_note = ", ".join(divergence.get("signals") or []) or "none"
            self.log(f"Trend: {trend} | RSI: {result['rsi_14']} ({rsi_signal}) | Div: {div_note}")
            return result

        except Exception as e:
            self.log(f"Error: {e}")
            return {"error": str(e), "ticker": self.ticker}

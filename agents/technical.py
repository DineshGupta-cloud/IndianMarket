from typing import Any, Dict, List
import yfinance as yf
import pandas as pd
from .base import BaseAgent
from utils.divergence import compute_rsi_series, detect_rsi_divergence


def _technical_recommendation(
    *,
    current: float,
    sma_20: float,
    sma_50: float,
    sma_200,
    rsi: float,
    macd_hist: float,
    trend: str,
    volume_higher: bool,
    divergence: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Rule-based technical score → BUY / HOLD / SELL.

    Score roughly -10 to +10; thresholds decide action.
    Educational only — not investment advice.
    """
    score = 0
    reasons: List[str] = []

    # Trend / MAs
    if trend == "Bullish":
        score += 2
        reasons.append("Price above key MAs (bullish trend structure)")
    elif trend == "Bearish":
        score -= 2
        reasons.append("Price below key MAs (bearish trend structure)")

    if current > sma_20:
        score += 1
        reasons.append("Price above SMA20 (short-term strength)")
    else:
        score -= 1
        reasons.append("Price below SMA20 (short-term weakness)")

    if current > sma_50:
        score += 1
    else:
        score -= 1

    if sma_200 is not None:
        if current > sma_200:
            score += 1
            reasons.append("Price above SMA200 (long-term uptrend filter)")
        else:
            score -= 1
            reasons.append("Price below SMA200 (long-term downtrend filter)")

    # RSI
    if rsi < 30:
        score += 2
        reasons.append(f"RSI {rsi:.1f} oversold — possible bounce zone")
    elif rsi < 45:
        score += 1
        reasons.append(f"RSI {rsi:.1f} on the softer side")
    elif rsi > 70:
        score -= 2
        reasons.append(f"RSI {rsi:.1f} overbought — extended / caution")
    elif rsi > 55:
        score += 0
        reasons.append(f"RSI {rsi:.1f} neutral-to-firm")
    else:
        reasons.append(f"RSI {rsi:.1f} neutral")

    # MACD histogram
    if macd_hist > 0:
        score += 1
        reasons.append("MACD histogram positive (momentum up)")
    else:
        score -= 1
        reasons.append("MACD histogram negative (momentum down)")

    # Volume
    if volume_higher:
        score += 1
        reasons.append("Volume above recent average (participation)")
    else:
        reasons.append("Volume below recent average")

    # Divergence
    div = divergence or {}
    if div.get("regular_bullish"):
        score += 2
        reasons.append("Regular bullish RSI divergence")
    if div.get("hidden_bullish"):
        score += 1
        reasons.append("Hidden bullish RSI divergence (continuation bias)")
    if div.get("regular_bearish"):
        score -= 2
        reasons.append("Regular bearish RSI divergence")
    if div.get("hidden_bearish"):
        score -= 1
        reasons.append("Hidden bearish RSI divergence (continuation bias)")

    # Map score → action
    if score >= 4:
        action = "BUY"
        confidence = "Medium-High" if score >= 6 else "Medium"
    elif score <= -4:
        action = "SELL"
        confidence = "Medium-High" if score <= -6 else "Medium"
    else:
        action = "HOLD"
        confidence = "Medium" if abs(score) <= 2 else "Low-Medium"

    summary = (
        f"Technical action: **{action}** (score {score:+d}/10, confidence {confidence}). "
        "Based only on price/indicators — not fundamentals or news."
    )

    return {
        "action": action,
        "score": score,
        "confidence": confidence,
        "reasons": reasons,
        "summary": summary,
        "disclaimer": (
            "Educational technical signal only. Not investment advice. "
            "Combine with fundamentals, risk limits, and your own judgment."
        ),
    }


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

            sma_20 = float(close.rolling(20).mean().iloc[-1])
            sma_50 = float(close.rolling(50).mean().iloc[-1])
            sma_200 = (
                float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None
            )
            ema_12 = float(close.ewm(span=12).mean().iloc[-1])
            ema_26 = float(close.ewm(span=26).mean().iloc[-1])

            rsi_series = compute_rsi_series(close, 14)
            rsi = float(rsi_series.iloc[-1])

            macd_line = ema_12 - ema_26
            signal_line = float(
                pd.Series(close.ewm(span=12).mean() - close.ewm(span=26).mean())
                .ewm(span=9)
                .mean()
                .iloc[-1]
            )
            macd_hist = float(macd_line - signal_line)

            recent = hist.tail(60)
            support = round(float(recent["Low"].min()), 2)
            resistance = round(float(recent["High"].max()), 2)

            current = float(close.iloc[-1])

            trend = "Neutral"
            if current > sma_50 and (sma_200 is None or current > sma_200):
                trend = "Bullish"
            elif current < sma_50 and (sma_200 is None or current < sma_200):
                trend = "Bearish"

            rsi_signal = "Neutral"
            if rsi > 70:
                rsi_signal = "Overbought"
            elif rsi < 30:
                rsi_signal = "Oversold"

            divergence = detect_rsi_divergence(close, rsi_series, order=5)
            volume_higher = bool(volume.iloc[-1] > volume.tail(20).mean())

            recommendation = _technical_recommendation(
                current=current,
                sma_20=sma_20,
                sma_50=sma_50,
                sma_200=sma_200,
                rsi=rsi,
                macd_hist=macd_hist,
                trend=trend,
                volume_higher=volume_higher,
                divergence=divergence,
            )

            result = {
                "ticker": self.ticker,
                "current_price": round(current, 2),
                "sma_20": round(sma_20, 2),
                "sma_50": round(sma_50, 2),
                "sma_200": round(sma_200, 2) if sma_200 is not None else None,
                "rsi_14": round(rsi, 2),
                "rsi_signal": rsi_signal,
                "macd": round(float(macd_line), 2),
                "macd_signal": round(signal_line, 2),
                "macd_hist": round(macd_hist, 2),
                "support_60d": support,
                "resistance_60d": resistance,
                "trend_bias": trend,
                "price_vs_sma50": "Above" if current > sma_50 else "Below",
                "volume_trend": (
                    "Higher than average" if volume_higher else "Lower than average"
                ),
                "rsi_divergence": divergence,
                "recommendation": recommendation,
                "action": recommendation["action"],
                "action_score": recommendation["score"],
            }

            self.log(
                f"{recommendation['action']} (score {recommendation['score']:+d}) | "
                f"Trend {trend} | RSI {result['rsi_14']}"
            )
            return result

        except Exception as e:
            self.log(f"Error: {e}")
            return {"error": str(e), "ticker": self.ticker}

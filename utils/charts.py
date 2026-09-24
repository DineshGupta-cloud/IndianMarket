"""Price chart data: Close, EMA50, SMA200 for Streamlit."""

from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd
import yfinance as yf


def fetch_chart_frame(ticker: str, period: str = "1y") -> Dict[str, Any]:
    t = ticker.upper().strip()
    if t.endswith(".NS") or t.endswith(".BO"):
        t = t[:-3]
    ns = f"{t}.NS"
    try:
        hist = yf.Ticker(ns).history(period=period)
        if hist.empty:
            return {"ticker": t, "error": "No data", "df": None}

        close = hist["Close"]
        df = pd.DataFrame(
            {
                "Close": close,
                "EMA50": close.ewm(span=50, adjust=False).mean(),
                "SMA200": close.rolling(200).mean() if len(close) >= 200 else close.rolling(min(len(close), 200)).mean(),
                "SMA50": close.rolling(50).mean(),
            }
        )
        # Drop early NaNs for cleaner chart
        df = df.dropna(how="all")

        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else last

        ema50 = float(last["EMA50"]) if pd.notna(last["EMA50"]) else None
        sma200 = float(last["SMA200"]) if pd.notna(last["SMA200"]) else None
        ema_prev = float(prev["EMA50"]) if pd.notna(prev["EMA50"]) else None
        sma_prev = float(prev["SMA200"]) if pd.notna(prev["SMA200"]) else None

        cross = "none"
        if ema50 is not None and sma200 is not None and ema_prev is not None and sma_prev is not None:
            if ema_prev <= sma_prev and ema50 > sma200:
                cross = "bullish_cross"  # EMA50 crossed above SMA200
            elif ema_prev >= sma_prev and ema50 < sma200:
                cross = "bearish_cross"  # EMA50 crossed below SMA200
            elif ema50 > sma200:
                cross = "ema50_above_sma200"
            else:
                cross = "ema50_below_sma200"

        price = float(last["Close"])
        vs_200 = None
        if sma200:
            vs_200 = "above" if price > sma200 else "below"

        return {
            "ticker": t,
            "error": None,
            "df": df,
            "price": round(price, 2),
            "ema50": round(ema50, 2) if ema50 else None,
            "sma200": round(sma200, 2) if sma200 else None,
            "cross_status": cross,
            "price_vs_sma200": vs_200,
        }
    except Exception as e:
        return {"ticker": t, "error": str(e), "df": None}

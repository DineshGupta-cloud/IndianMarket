"""Price chart data: Close, EMA50, SMA200 + last crossover date."""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import pandas as pd
import yfinance as yf


def _last_crossover_date(ema50: pd.Series, sma200: pd.Series) -> Tuple[Optional[str], Optional[str]]:
    """
    Walk history for last time EMA50 crossed SMA200.
    Returns (date_str YYYY-MM-DD, kind) where kind is bullish_cross | bearish_cross.
    """
    df = pd.DataFrame({"ema": ema50, "sma": sma200}).dropna()
    if len(df) < 2:
        return None, None

    last_date = None
    last_kind = None
    prev_ema = df["ema"].iloc[0]
    prev_sma = df["sma"].iloc[0]

    for i in range(1, len(df)):
        e = float(df["ema"].iloc[i])
        s = float(df["sma"].iloc[i])
        pe, ps = float(prev_ema), float(prev_sma)
        idx = df.index[i]
        date_str = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10]

        if pe <= ps and e > s:
            last_date, last_kind = date_str, "bullish_cross"
        elif pe >= ps and e < s:
            last_date, last_kind = date_str, "bearish_cross"

        prev_ema, prev_sma = e, s

    return last_date, last_kind


def fetch_chart_frame(ticker: str, period: str = "1y") -> Dict[str, Any]:
    t = ticker.upper().strip()
    if t.endswith(".NS") or t.endswith(".BO"):
        t = t[:-3]
    ns = f"{t}.NS"
    try:
        # Prefer enough history for SMA200 + crossover lookback
        hist = yf.Ticker(ns).history(period=period if period in ("2y", "5y", "max") else "2y")
        if hist.empty:
            return {"ticker": t, "error": "No data", "df": None}

        close = hist["Close"]
        ema50 = close.ewm(span=50, adjust=False).mean()
        sma200 = close.rolling(200).mean()
        sma50 = close.rolling(50).mean()

        df = pd.DataFrame(
            {
                "Close": close,
                "EMA50": ema50,
                "SMA200": sma200,
                "SMA50": sma50,
            }
        )

        cross_date, cross_kind_hist = _last_crossover_date(ema50, sma200)

        last = df.dropna(subset=["EMA50"]).iloc[-1] if df["EMA50"].notna().any() else df.iloc[-1]
        prev_rows = df.dropna(subset=["EMA50", "SMA200"])
        if len(prev_rows) >= 2:
            prev = prev_rows.iloc[-2]
            cur = prev_rows.iloc[-1]
            e, s = float(cur["EMA50"]), float(cur["SMA200"])
            pe, ps = float(prev["EMA50"]), float(prev["SMA200"])
            if pe <= ps and e > s:
                cross_status = "bullish_cross"
                # Prefer exact bar date for fresh cross
                idx = prev_rows.index[-1]
                cross_date = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10]
            elif pe >= ps and e < s:
                cross_status = "bearish_cross"
                idx = prev_rows.index[-1]
                cross_date = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10]
            elif e > s:
                cross_status = "ema50_above_sma200"
            else:
                cross_status = "ema50_below_sma200"
        else:
            cross_status = cross_kind_hist or "none"

        price = float(close.iloc[-1])
        ema_v = float(ema50.iloc[-1]) if pd.notna(ema50.iloc[-1]) else None
        sma_v = float(sma200.iloc[-1]) if pd.notna(sma200.iloc[-1]) else None
        vs_200 = None
        if sma_v is not None:
            vs_200 = "above" if price > sma_v else "below"

        # Chart window: last period-ish rows if user asked shorter period
        plot_df = df.copy()
        if period == "6mo":
            plot_df = plot_df.tail(130)
        elif period == "1y":
            plot_df = plot_df.tail(260)

        return {
            "ticker": t,
            "error": None,
            "df": plot_df,
            "price": round(price, 2),
            "ema50": round(ema_v, 2) if ema_v is not None else None,
            "sma200": round(sma_v, 2) if sma_v is not None else None,
            "cross_status": cross_status,
            "crossover_date": cross_date,
            "crossover_kind": cross_kind_hist or cross_status,
            "price_vs_sma200": vs_200,
        }
    except Exception as e:
        return {"ticker": t, "error": str(e), "df": None}

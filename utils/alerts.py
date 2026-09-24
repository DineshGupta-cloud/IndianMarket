"""
Watchlist alerts: price, day %, RSI, divergence, EMA50/SMA200 crossover.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import yfinance as yf

from utils.divergence import compute_rsi_series, detect_rsi_divergence
from utils.charts import fetch_chart_frame


def pd_isna(x) -> bool:
    try:
        import math
        return x is None or (isinstance(x, float) and math.isnan(x))
    except Exception:
        return True


def fetch_snapshot(ticker: str, include_divergence: bool = True) -> Dict[str, Any]:
    t = ticker.upper().strip()
    if t.endswith(".NS") or t.endswith(".BO"):
        t = t[:-3]
    ns = f"{t}.NS"
    try:
        stock = yf.Ticker(ns)
        hist = stock.history(period="1y")
        if hist.empty:
            return {"ticker": t, "error": "No data"}
        last = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) > 1 else last
        price = float(last["Close"])
        prev_c = float(prev["Close"])
        day_pct = ((price - prev_c) / prev_c) * 100 if prev_c else 0.0
        close = hist["Close"]
        rsi_series = compute_rsi_series(close)
        rsi = round(float(rsi_series.iloc[-1]), 2) if not pd_isna(rsi_series.iloc[-1]) else None

        div = None
        if include_divergence:
            div = detect_rsi_divergence(close, rsi_series, order=5)

        chart = fetch_chart_frame(t, period="1y")

        return {
            "ticker": t,
            "price": round(price, 2),
            "day_change_pct": round(day_pct, 2),
            "rsi_14": rsi,
            "rsi_divergence": div,
            "ema50": chart.get("ema50"),
            "sma200": chart.get("sma200"),
            "cross_status": chart.get("cross_status"),
            "price_vs_sma200": chart.get("price_vs_sma200"),
            "error": None,
        }
    except Exception as e:
        return {"ticker": t, "error": str(e)}


def evaluate_alerts(
    tickers: List[str],
    *,
    price_above: Optional[float] = None,
    price_below: Optional[float] = None,
    day_change_abs_pct: Optional[float] = None,
    rsi_overbought: float = 70.0,
    rsi_oversold: float = 30.0,
    check_rsi: bool = True,
    check_divergence: bool = True,
    check_ma_cross: bool = True,
) -> List[Dict[str, Any]]:
    results = []
    for ticker in tickers:
        snap = fetch_snapshot(ticker, include_divergence=check_divergence)
        if snap.get("error"):
            results.append({**snap, "alerts": [f"Data error: {snap['error']}"]})
            continue

        fired: List[str] = []
        price = snap["price"]
        day_pct = snap["day_change_pct"]
        rsi = snap.get("rsi_14")

        if price_above is not None and price >= price_above:
            fired.append(f"Price ₹{price} ≥ above level ₹{price_above}")
        if price_below is not None and price <= price_below:
            fired.append(f"Price ₹{price} ≤ below level ₹{price_below}")

        if day_change_abs_pct is not None and abs(day_pct) >= day_change_abs_pct:
            direction = "up" if day_pct > 0 else "down"
            fired.append(
                f"Day move {day_pct:+.2f}% ({direction}) exceeds ±{day_change_abs_pct}%"
            )

        if check_rsi and rsi is not None:
            if rsi >= rsi_overbought:
                fired.append(f"RSI {rsi} overbought (≥ {rsi_overbought})")
            if rsi <= rsi_oversold:
                fired.append(f"RSI {rsi} oversold (≤ {rsi_oversold})")

        if check_divergence and snap.get("rsi_divergence"):
            for sig in snap["rsi_divergence"].get("signals") or []:
                fired.append(sig)

        if check_ma_cross:
            cs = snap.get("cross_status")
            if cs == "bullish_cross":
                fired.append("EMA50 crossed ABOVE SMA200 (bullish)")
            elif cs == "bearish_cross":
                fired.append("EMA50 crossed BELOW SMA200 (bearish)")
            if snap.get("price_vs_sma200") == "above":
                fired.append("Price above SMA200")
            elif snap.get("price_vs_sma200") == "below":
                fired.append("Price below SMA200")

        results.append({**snap, "alerts": fired})
    return results

"""Watchlist alerts: price, RSI, divergence, EMA50/SMA200 + crossover date."""

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
    try:
        chart = fetch_chart_frame(t, period="2y")
        if chart.get("error"):
            return {"ticker": t, "error": chart["error"]}

        stock = yf.Ticker(f"{t}.NS")
        hist = stock.history(period="5d")
        day_pct = 0.0
        if hist is not None and len(hist) >= 2:
            price = float(hist["Close"].iloc[-1])
            prev = float(hist["Close"].iloc[-2])
            day_pct = ((price - prev) / prev) * 100 if prev else 0.0
        else:
            price = chart.get("price") or 0.0

        # RSI from longer history inside chart df if present
        rsi = None
        div = None
        if chart.get("df") is not None and "Close" in chart["df"].columns:
            close = chart["df"]["Close"].dropna()
            # Need fuller series — refetch short for RSI only if needed
            full = yf.Ticker(f"{t}.NS").history(period="6mo")
            if not full.empty:
                rsi_series = compute_rsi_series(full["Close"])
                if not pd_isna(rsi_series.iloc[-1]):
                    rsi = round(float(rsi_series.iloc[-1]), 2)
                if include_divergence:
                    div = detect_rsi_divergence(full["Close"], rsi_series, order=5)

        return {
            "ticker": t,
            "price": round(float(price), 2),
            "day_change_pct": round(day_pct, 2),
            "rsi_14": rsi,
            "rsi_divergence": div,
            "ema50": chart.get("ema50"),
            "sma200": chart.get("sma200"),
            "cross_status": chart.get("cross_status"),
            "crossover_date": chart.get("crossover_date"),
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
        cdate = snap.get("crossover_date") or "N/A"

        if price_above is not None and price >= price_above:
            fired.append(f"Price ₹{price} ≥ ₹{price_above}")
        if price_below is not None and price <= price_below:
            fired.append(f"Price ₹{price} ≤ ₹{price_below}")

        if day_change_abs_pct is not None and abs(day_pct) >= day_change_abs_pct:
            fired.append(f"Day move {day_pct:+.2f}% exceeds ±{day_change_abs_pct}%")

        if check_rsi and rsi is not None:
            if rsi >= rsi_overbought:
                fired.append(f"RSI {rsi} overbought")
            if rsi <= rsi_oversold:
                fired.append(f"RSI {rsi} oversold")

        if check_divergence and snap.get("rsi_divergence"):
            for sig in snap["rsi_divergence"].get("signals") or []:
                fired.append(sig)

        if check_ma_cross:
            cs = snap.get("cross_status")
            if cs == "bullish_cross":
                fired.append(f"EMA50 crossed ABOVE SMA200 on {cdate}")
            elif cs == "bearish_cross":
                fired.append(f"EMA50 crossed BELOW SMA200 on {cdate}")
            elif cs == "ema50_above_sma200":
                fired.append(f"EMA50 above SMA200 (last cross {cdate})")
            elif cs == "ema50_below_sma200":
                fired.append(f"EMA50 below SMA200 (last cross {cdate})")
            if snap.get("price_vs_sma200") == "above":
                fired.append("Price above SMA200")
            elif snap.get("price_vs_sma200") == "below":
                fired.append("Price below SMA200")

        results.append({**snap, "alerts": fired})
    return results

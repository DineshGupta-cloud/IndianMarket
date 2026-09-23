"""
Watchlist / portfolio alerts using yfinance.
Rules: price above/below, day change %, RSI overbought/oversold.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import yfinance as yf


def _rsi(closes, period: int = 14) -> Optional[float]:
    if closes is None or len(closes) < period + 1:
        return None
    delta = closes.diff()
    gain = delta.where(delta > 0, 0.0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(period).mean()
    rs = gain / loss
    val = 100 - (100 / (1 + rs.iloc[-1]))
    try:
        return round(float(val), 2)
    except Exception:
        return None


def fetch_snapshot(ticker: str) -> Dict[str, Any]:
    t = ticker.upper().strip()
    if t.endswith(".NS") or t.endswith(".BO"):
        t = t[:-3]
    ns = f"{t}.NS"
    try:
        stock = yf.Ticker(ns)
        hist = stock.history(period="3mo")
        if hist.empty:
            return {"ticker": t, "error": "No data"}
        last = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) > 1 else last
        price = float(last["Close"])
        prev_c = float(prev["Close"])
        day_pct = ((price - prev_c) / prev_c) * 100 if prev_c else 0.0
        rsi = _rsi(hist["Close"])
        return {
            "ticker": t,
            "price": round(price, 2),
            "day_change_pct": round(day_pct, 2),
            "rsi_14": rsi,
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
) -> List[Dict[str, Any]]:
    """
    Returns list of triggered alerts:
      {ticker, price, day_change_pct, rsi_14, alerts: [str, ...]}
    """
    results = []
    for ticker in tickers:
        snap = fetch_snapshot(ticker)
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
            fired.append(f"Day move {day_pct:+.2f}% ({direction}) exceeds ±{day_change_abs_pct}%")

        if check_rsi and rsi is not None:
            if rsi >= rsi_overbought:
                fired.append(f"RSI {rsi} overbought (≥ {rsi_overbought})")
            if rsi <= rsi_oversold:
                fired.append(f"RSI {rsi} oversold (≤ {rsi_oversold})")

        results.append({**snap, "alerts": fired})
    return results

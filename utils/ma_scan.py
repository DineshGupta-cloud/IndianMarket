"""
Scan tickers for:
  - Price vs SMA200
  - EMA50 vs SMA200 (position + fresh crossover)
"""

from __future__ import annotations

from typing import Any, Dict, List

from utils.charts import fetch_chart_frame


def scan_ma_crossovers(tickers: List[str], period: str = "1y") -> List[Dict[str, Any]]:
    rows = []
    for t in tickers:
        info = fetch_chart_frame(t, period=period)
        if info.get("error"):
            rows.append(
                {
                    "ticker": t.upper(),
                    "error": info["error"],
                    "price": None,
                    "ema50": None,
                    "sma200": None,
                    "cross_status": None,
                    "price_vs_sma200": None,
                    "alert": f"Error: {info['error']}",
                }
            )
            continue

        cross = info.get("cross_status") or "none"
        alert = None
        if cross == "bullish_cross":
            alert = "EMA50 crossed ABOVE SMA200 (bullish crossover)"
        elif cross == "bearish_cross":
            alert = "EMA50 crossed BELOW SMA200 (bearish crossover)"
        elif cross == "ema50_above_sma200":
            alert = "EMA50 above SMA200"
        elif cross == "ema50_below_sma200":
            alert = "EMA50 below SMA200"

        vs = info.get("price_vs_sma200")
        if vs == "above":
            alert = (alert or "") + (" | Price above SMA200" if alert else "Price above SMA200")
        elif vs == "below":
            alert = (alert or "") + (" | Price below SMA200" if alert else "Price below SMA200")

        rows.append(
            {
                "ticker": info["ticker"],
                "error": None,
                "price": info.get("price"),
                "ema50": info.get("ema50"),
                "sma200": info.get("sma200"),
                "cross_status": cross,
                "price_vs_sma200": vs,
                "alert": alert,
            }
        )
    return rows

"""
RSI divergence detection: regular + hidden (bullish/bearish).
Uses swing highs/lows on close and RSI series.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


def compute_rsi_series(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _swing_points(
    series: pd.Series, order: int = 5
) -> Tuple[List[Tuple[int, float]], List[Tuple[int, float]]]:
    """
    Local extrema: index position + value.
    order = bars on each side that must be lower/higher.
    """
    vals = series.values.astype(float)
    highs: List[Tuple[int, float]] = []
    lows: List[Tuple[int, float]] = []
    n = len(vals)
    for i in range(order, n - order):
        window = vals[i - order : i + order + 1]
        if np.isnan(vals[i]):
            continue
        if vals[i] == np.nanmax(window):
            highs.append((i, float(vals[i])))
        if vals[i] == np.nanmin(window):
            lows.append((i, float(vals[i])))
    return highs, lows


def detect_rsi_divergence(
    close: pd.Series,
    rsi: Optional[pd.Series] = None,
    order: int = 5,
) -> Dict[str, Any]:
    """
    Compare last two swing highs and last two swing lows of price vs RSI.

    Returns flags for:
      regular_bullish, regular_bearish,
      hidden_bullish, hidden_bearish
    """
    if rsi is None:
        rsi = compute_rsi_series(close)

    if len(close) < order * 4 + 20:
        return {
            "regular_bullish": False,
            "regular_bearish": False,
            "hidden_bullish": False,
            "hidden_bearish": False,
            "signals": [],
            "detail": "Insufficient data for swings",
        }

    # Align RSI to close index
    rsi = rsi.reindex(close.index)

    price_highs, price_lows = _swing_points(close, order=order)
    rsi_highs, rsi_lows = _swing_points(rsi.ffill(), order=order)

    signals: List[str] = []
    regular_bullish = regular_bearish = False
    hidden_bullish = hidden_bearish = False
    detail: Dict[str, Any] = {}

    # --- Bearish types: use last two price highs, match RSI near those bars ---
    if len(price_highs) >= 2:
        (i1, p1), (i2, p2) = price_highs[-2], price_highs[-1]
        # RSI value at same bars (approx)
        r1 = float(rsi.iloc[i1]) if not np.isnan(rsi.iloc[i1]) else None
        r2 = float(rsi.iloc[i2]) if not np.isnan(rsi.iloc[i2]) else None
        detail["last_two_price_highs"] = {"p1": p1, "p2": p2, "r1": r1, "r2": r2}

        if r1 is not None and r2 is not None:
            # Regular bearish: higher high price, lower high RSI
            if p2 > p1 and r2 < r1:
                regular_bearish = True
                signals.append("Regular bearish divergence (price HH, RSI LH)")
            # Hidden bearish: lower high price, higher high RSI
            if p2 < p1 and r2 > r1:
                hidden_bearish = True
                signals.append("Hidden bearish divergence (price LH, RSI HH)")

    # --- Bullish types: last two price lows ---
    if len(price_lows) >= 2:
        (i1, p1), (i2, p2) = price_lows[-2], price_lows[-1]
        r1 = float(rsi.iloc[i1]) if not np.isnan(rsi.iloc[i1]) else None
        r2 = float(rsi.iloc[i2]) if not np.isnan(rsi.iloc[i2]) else None
        detail["last_two_price_lows"] = {"p1": p1, "p2": p2, "r1": r1, "r2": r2}

        if r1 is not None and r2 is not None:
            # Regular bullish: lower low price, higher low RSI
            if p2 < p1 and r2 > r1:
                regular_bullish = True
                signals.append("Regular bullish divergence (price LL, RSI HL)")
            # Hidden bullish: higher low price, lower low RSI
            if p2 > p1 and r2 < r1:
                hidden_bullish = True
                signals.append("Hidden bullish divergence (price HL, RSI LL)")

    return {
        "regular_bullish": regular_bullish,
        "regular_bearish": regular_bearish,
        "hidden_bullish": hidden_bullish,
        "hidden_bearish": hidden_bearish,
        "signals": signals,
        "detail": detail,
        "swing_order": order,
    }

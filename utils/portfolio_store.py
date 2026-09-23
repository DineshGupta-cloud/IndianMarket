"""
SQLite-backed portfolio storage.
DB file: data/portfolios.db (created automatically).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Popular NSE tickers users can add quickly
SUGGESTED_STOCKS: List[Dict[str, str]] = [
    {"ticker": "RELIANCE", "name": "Reliance Industries", "sector": "Energy / Conglomerate"},
    {"ticker": "TCS", "name": "Tata Consultancy Services", "sector": "IT"},
    {"ticker": "INFY", "name": "Infosys", "sector": "IT"},
    {"ticker": "HDFCBANK", "name": "HDFC Bank", "sector": "Banking"},
    {"ticker": "ICICIBANK", "name": "ICICI Bank", "sector": "Banking"},
    {"ticker": "SBIN", "name": "State Bank of India", "sector": "Banking"},
    {"ticker": "KOTAKBANK", "name": "Kotak Mahindra Bank", "sector": "Banking"},
    {"ticker": "BHARTIARTL", "name": "Bharti Airtel", "sector": "Telecom"},
    {"ticker": "ITC", "name": "ITC", "sector": "FMCG"},
    {"ticker": "HINDUNILVR", "name": "Hindustan Unilever", "sector": "FMCG"},
    {"ticker": "LT", "name": "Larsen & Toubro", "sector": "Infrastructure"},
    {"ticker": "AXISBANK", "name": "Axis Bank", "sector": "Banking"},
    {"ticker": "BAJFINANCE", "name": "Bajaj Finance", "sector": "NBFC"},
    {"ticker": "ASIANPAINT", "name": "Asian Paints", "sector": "Consumer"},
    {"ticker": "MARUTI", "name": "Maruti Suzuki", "sector": "Auto"},
    {"ticker": "TITAN", "name": "Titan Company", "sector": "Consumer"},
    {"ticker": "SUNPHARMA", "name": "Sun Pharma", "sector": "Pharma"},
    {"ticker": "WIPRO", "name": "Wipro", "sector": "IT"},
    {"ticker": "HCLTECH", "name": "HCL Technologies", "sector": "IT"},
    {"ticker": "POWERGRID", "name": "Power Grid", "sector": "Power"},
    {"ticker": "NTPC", "name": "NTPC", "sector": "Power"},
    {"ticker": "ONGC", "name": "ONGC", "sector": "Energy"},
    {"ticker": "TATASTEEL", "name": "Tata Steel", "sector": "Metals"},
    {"ticker": "JSWSTEEL", "name": "JSW Steel", "sector": "Metals"},
    {"ticker": "ADANIENT", "name": "Adani Enterprises", "sector": "Conglomerate"},
    {"ticker": "ADANIPORTS", "name": "Adani Ports", "sector": "Infrastructure"},
    {"ticker": "ULTRACEMCO", "name": "UltraTech Cement", "sector": "Cement"},
    {"ticker": "NESTLEIND", "name": "Nestle India", "sector": "FMCG"},
    {"ticker": "TATAMOTORS", "name": "Tata Motors", "sector": "Auto"},
    {"ticker": "M&M", "name": "Mahindra & Mahindra", "sector": "Auto"},
]

# Example portfolios seeded on first run
EXAMPLE_PORTFOLIOS = [
    {
        "name": "Core Long Term",
        "notes": "Example diversified core holdings",
        "holdings": [
            {"ticker": "RELIANCE", "qty": 10, "avg_price": 1200, "notes": "Example"},
            {"ticker": "TCS", "qty": 5, "avg_price": 3500, "notes": "Example"},
            {"ticker": "HDFCBANK", "qty": 15, "avg_price": 1500, "notes": "Example"},
            {"ticker": "INFY", "qty": 10, "avg_price": 1500, "notes": "Example"},
        ],
    },
    {
        "name": "Banking Basket",
        "notes": "Example banking-focused portfolio",
        "holdings": [
            {"ticker": "HDFCBANK", "qty": 20, "avg_price": 1500, "notes": ""},
            {"ticker": "ICICIBANK", "qty": 20, "avg_price": 1100, "notes": ""},
            {"ticker": "SBIN", "qty": 30, "avg_price": 750, "notes": ""},
            {"ticker": "KOTAKBANK", "qty": 10, "avg_price": 1800, "notes": ""},
        ],
    },
    {
        "name": "Watchlist",
        "notes": "Ideas to research (qty optional)",
        "holdings": [
            {"ticker": "ITC", "qty": None, "avg_price": None, "notes": "Watch"},
            {"ticker": "LT", "qty": None, "avg_price": None, "notes": "Watch"},
            {"ticker": "BHARTIARTL", "qty": None, "avg_price": None, "notes": "Watch"},
            {"ticker": "SUNPHARMA", "qty": None, "avg_price": None, "notes": "Watch"},
        ],
    },
]


def _db_path() -> Path:
    root = Path(__file__).resolve().parent.parent
    data_dir = root / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir / "portfolios.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_db_path()), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(seed_examples: bool = True) -> None:
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS portfolios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS holdings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            portfolio_id INTEGER NOT NULL,
            ticker TEXT NOT NULL,
            qty REAL,
            avg_price REAL,
            notes TEXT DEFAULT '',
            added_at TEXT NOT NULL,
            UNIQUE(portfolio_id, ticker),
            FOREIGN KEY(portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE
        )
        """
    )
    conn.commit()

    if seed_examples:
        cur.execute("SELECT COUNT(*) AS c FROM portfolios")
        if cur.fetchone()["c"] == 0:
            for p in EXAMPLE_PORTFOLIOS:
                pid = create_portfolio(p["name"], p.get("notes", ""))
                for h in p["holdings"]:
                    add_holding(
                        pid,
                        h["ticker"],
                        qty=h.get("qty"),
                        avg_price=h.get("avg_price"),
                        notes=h.get("notes") or "",
                    )
    conn.close()


def list_portfolios() -> List[Dict[str, Any]]:
    conn = _connect()
    rows = conn.execute(
        "SELECT id, name, notes, created_at FROM portfolios ORDER BY name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_portfolio(name: str, notes: str = "") -> int:
    name = name.strip()
    if not name:
        raise ValueError("Portfolio name required")
    conn = _connect()
    try:
        cur = conn.execute(
            "INSERT INTO portfolios (name, notes, created_at) VALUES (?, ?, ?)",
            (name, notes or "", datetime.now().isoformat(timespec="seconds")),
        )
        conn.commit()
        return int(cur.lastrowid)
    except sqlite3.IntegrityError:
        raise ValueError(f"Portfolio '{name}' already exists")
    finally:
        conn.close()


def delete_portfolio(portfolio_id: int) -> None:
    conn = _connect()
    conn.execute("DELETE FROM holdings WHERE portfolio_id = ?", (portfolio_id,))
    conn.execute("DELETE FROM portfolios WHERE id = ?", (portfolio_id,))
    conn.commit()
    conn.close()


def get_holdings(portfolio_id: int) -> List[Dict[str, Any]]:
    conn = _connect()
    rows = conn.execute(
        """
        SELECT id, ticker, qty, avg_price, notes, added_at
        FROM holdings WHERE portfolio_id = ? ORDER BY ticker
        """,
        (portfolio_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_holding(
    portfolio_id: int,
    ticker: str,
    qty: Optional[float] = None,
    avg_price: Optional[float] = None,
    notes: str = "",
) -> None:
    ticker = ticker.upper().strip()
    if ticker.endswith(".NS") or ticker.endswith(".BO"):
        ticker = ticker[:-3]
    if not ticker:
        raise ValueError("Ticker required")
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO holdings (portfolio_id, ticker, qty, avg_price, notes, added_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(portfolio_id, ticker) DO UPDATE SET
                qty = excluded.qty,
                avg_price = excluded.avg_price,
                notes = excluded.notes
            """,
            (
                portfolio_id,
                ticker,
                qty,
                avg_price,
                notes or "",
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def remove_holding(portfolio_id: int, ticker: str) -> None:
    ticker = ticker.upper().strip()
    conn = _connect()
    conn.execute(
        "DELETE FROM holdings WHERE portfolio_id = ? AND ticker = ?",
        (portfolio_id, ticker),
    )
    conn.commit()
    conn.close()


def tickers_csv(portfolio_id: int) -> str:
    holdings = get_holdings(portfolio_id)
    return ",".join(h["ticker"] for h in holdings)


def export_json() -> str:
    """Export all portfolios as JSON string (backup)."""
    out = []
    for p in list_portfolios():
        out.append(
            {
                "name": p["name"],
                "notes": p["notes"],
                "created_at": p["created_at"],
                "holdings": get_holdings(p["id"]),
            }
        )
    return json.dumps({"portfolios": out}, indent=2)

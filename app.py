"""
IndianMarket — Premium research terminal
International-grade Streamlit frontend

Run:  streamlit run app.py
"""

from __future__ import annotations

import traceback
from datetime import datetime

import streamlit as st

from agents.orchestrator import ResearchOrchestrator
from utils.alerts import evaluate_alerts
from utils.charts import fetch_chart_frame
from utils.llm_client import is_llm_available
from utils.ma_scan import scan_ma_crossovers
from utils.portfolio_store import (
    SUGGESTED_STOCKS,
    add_holding,
    create_portfolio,
    get_holdings,
    init_db,
    list_portfolios,
)

# ───────────────────────────────────────────────
# Page config
# ───────────────────────────────────────────────
st.set_page_config(
    page_title="IndianMarket | Equity Research Terminal",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db(seed_examples=True)

# ───────────────────────────────────────────────
# Design system (dark fintech terminal)
# ───────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
  --bg: #0b0f14;
  --bg-elevated: #12181f;
  --bg-card: #151c24;
  --border: #243041;
  --border-soft: #1a2330;
  --text: #e8eef6;
  --text-muted: #8b9bb0;
  --text-dim: #5c6b7e;
  --accent: #3b82f6;
  --accent-soft: rgba(59, 130, 246, 0.12);
  --green: #22c55e;
  --green-soft: rgba(34, 197, 94, 0.12);
  --red: #ef4444;
  --red-soft: rgba(239, 68, 68, 0.12);
  --amber: #f59e0b;
  --amber-soft: rgba(245, 158, 11, 0.12);
  --radius: 12px;
  --radius-sm: 8px;
}

html, body, [class*="css"] {
  font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
  background: var(--bg);
  color: var(--text);
}

/* Hide Streamlit chrome clutter */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* Sidebar */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0e1319 0%, #0b0f14 100%);
  border-right: 1px solid var(--border-soft);
}
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] label {
  color: var(--text-muted) !important;
}

/* Main padding */
.block-container {
  padding-top: 1.5rem !important;
  padding-bottom: 3rem !important;
  max-width: 1400px;
}

/* Hero */
.im-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1.5rem;
  margin-bottom: 1.75rem;
  padding-bottom: 1.25rem;
  border-bottom: 1px solid var(--border-soft);
}
.im-brand {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}
.im-logo {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  background: linear-gradient(135deg, #2563eb 0%, #06b6d4 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.1rem;
  color: white;
  box-shadow: 0 4px 20px rgba(37, 99, 235, 0.35);
}
.im-title {
  font-size: 1.45rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: var(--text);
  margin: 0;
  line-height: 1.2;
}
.im-subtitle {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin: 0.15rem 0 0 0;
}
.im-badge-row {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  align-items: center;
}
.im-badge {
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 0.28rem 0.65rem;
  border-radius: 999px;
  border: 1px solid var(--border);
  color: var(--text-muted);
  background: var(--bg-elevated);
}
.im-badge.live {
  color: var(--green);
  border-color: rgba(34, 197, 94, 0.35);
  background: var(--green-soft);
}
.im-badge.live::before {
  content: "";
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--green);
  margin-right: 6px;
  vertical-align: middle;
  box-shadow: 0 0 8px var(--green);
}

/* Section headers */
.im-section {
  margin: 1.75rem 0 0.9rem 0;
}
.im-section-label {
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-dim);
  margin-bottom: 0.35rem;
}
.im-section-title {
  font-size: 1.15rem;
  font-weight: 650;
  letter-spacing: -0.02em;
  color: var(--text);
  margin: 0;
}
.im-section-desc {
  font-size: 0.82rem;
  color: var(--text-muted);
  margin-top: 0.25rem;
}

/* Metric cards */
.im-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.75rem;
  margin: 1rem 0 1.25rem 0;
}
.im-metric {
  background: var(--bg-card);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  padding: 1rem 1.1rem;
  transition: border-color 0.15s ease;
}
.im-metric:hover {
  border-color: var(--border);
}
.im-metric .label {
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-dim);
  margin-bottom: 0.4rem;
}
.im-metric .value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--text);
  letter-spacing: -0.02em;
}
.im-metric .value.up { color: var(--green); }
.im-metric .value.down { color: var(--red); }
.im-metric .value.accent { color: #60a5fa; }

/* Action pill for BUY/SELL/HOLD */
.im-action {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  font-size: 0.95rem;
  letter-spacing: 0.06em;
  padding: 0.45rem 0.9rem;
  border-radius: var(--radius-sm);
}
.im-action.buy {
  background: var(--green-soft);
  color: var(--green);
  border: 1px solid rgba(34, 197, 94, 0.3);
}
.im-action.sell {
  background: var(--red-soft);
  color: var(--red);
  border: 1px solid rgba(239, 68, 68, 0.3);
}
.im-action.hold {
  background: var(--amber-soft);
  color: var(--amber);
  border: 1px solid rgba(245, 158, 11, 0.3);
}

/* Panel / card */
.im-panel {
  background: var(--bg-card);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  padding: 1.15rem 1.25rem;
  margin-bottom: 1rem;
}
.im-panel-title {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-dim);
  margin-bottom: 0.75rem;
}

/* Empty state */
.im-empty {
  text-align: center;
  padding: 2.5rem 1.5rem;
  border: 1px dashed var(--border);
  border-radius: var(--radius);
  background: rgba(18, 24, 31, 0.5);
  color: var(--text-muted);
  font-size: 0.9rem;
}
.im-empty strong {
  color: var(--text);
  display: block;
  margin-bottom: 0.35rem;
  font-size: 1rem;
}

/* Alert chips */
.im-alert {
  border-left: 3px solid var(--amber);
  background: var(--amber-soft);
  padding: 0.65rem 0.9rem;
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  margin: 0.4rem 0;
  font-size: 0.85rem;
  color: var(--text);
}
.im-alert.bull {
  border-left-color: var(--green);
  background: var(--green-soft);
}
.im-alert.bear {
  border-left-color: var(--red);
  background: var(--red-soft);
}

/* Buttons */
div.stButton > button {
  border-radius: var(--radius-sm) !important;
  font-weight: 600 !important;
  letter-spacing: 0.01em;
  border: 1px solid var(--border) !important;
  transition: all 0.15s ease !important;
}
div.stButton > button[kind="primary"],
div.stButton > button[data-testid="baseButton-primary"] {
  background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
  border: none !important;
  color: white !important;
  box-shadow: 0 2px 12px rgba(37, 99, 235, 0.35);
}
div.stButton > button:hover {
  transform: translateY(-1px);
}

/* Inputs */
.stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
  border-radius: var(--radius-sm) !important;
  background: var(--bg-elevated) !important;
  border-color: var(--border) !important;
  color: var(--text) !important;
}

/* Dataframes */
[data-testid="stDataFrame"] {
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  overflow: hidden;
}

/* Tabs if any */
.stTabs [data-baseweb="tab-list"] {
  gap: 0.35rem;
  background: transparent;
  border-bottom: 1px solid var(--border-soft);
}
.stTabs [data-baseweb="tab"] {
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  color: var(--text-muted);
  font-weight: 500;
}

/* Divider */
hr {
  border: none;
  border-top: 1px solid var(--border-soft);
  margin: 1.5rem 0;
}

/* Footer */
.im-footer {
  margin-top: 2.5rem;
  padding-top: 1.25rem;
  border-top: 1px solid var(--border-soft);
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
  font-size: 0.75rem;
  color: var(--text-dim);
}

/* Sidebar brand */
.im-side-brand {
  padding: 0.5rem 0 1rem 0;
  margin-bottom: 0.5rem;
  border-bottom: 1px solid var(--border-soft);
}
.im-side-brand .name {
  font-weight: 700;
  font-size: 1.05rem;
  color: var(--text);
  letter-spacing: -0.02em;
}
.im-side-brand .tag {
  font-size: 0.72rem;
  color: var(--text-dim);
  margin-top: 0.15rem;
}
.im-side-section {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--text-dim);
  margin: 1.1rem 0 0.5rem 0;
}
</style>
""",
    unsafe_allow_html=True,
)


def metric_card(label: str, value: str, tone: str = "") -> str:
    cls = f"value {tone}".strip()
    return f"""
    <div class="im-metric">
      <div class="label">{label}</div>
      <div class="{cls}">{value}</div>
    </div>
    """


def action_pill(action: str) -> str:
    a = (action or "HOLD").upper()
    if a == "BUY":
        cls = "buy"
    elif a == "SELL":
        cls = "sell"
    else:
        cls = "hold"
        a = "HOLD" if a not in ("BUY", "SELL") else a
    return f'<span class="im-action {cls}">{a}</span>'


def show_chart(ticker: str, period: str):
    info = fetch_chart_frame(ticker, period=period)
    if info.get("error") or info.get("df") is None:
        st.warning(info.get("error", "No chart data"))
        return None

    vs = info.get("price_vs_sma200") or "—"
    vs_tone = "up" if vs == "above" else ("down" if vs == "below" else "")
    cross = info.get("cross_status") or "—"

    cards = "".join(
        [
            metric_card("Last", f"₹{info.get('price')}", "accent"),
            metric_card("EMA 50", f"₹{info.get('ema50')}"),
            metric_card("SMA 200", f"₹{info.get('sma200')}"),
            metric_card("vs SMA200", str(vs).title(), vs_tone),
            metric_card("Crossover date", info.get("crossover_date") or "—"),
        ]
    )
    st.markdown(f'<div class="im-metrics">{cards}</div>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="im-panel">
          <div class="im-panel-title">Price structure · {info['ticker']}</div>
          <div style="font-size:0.82rem;color:var(--text-muted);margin-bottom:0.75rem;">
            Status: <strong style="color:var(--text)">{cross}</strong>
            &nbsp;·&nbsp; Last EMA50 × SMA200 cross:
            <strong style="color:var(--text)">{info.get('crossover_date') or 'N/A'}</strong>
            ({info.get('crossover_kind') or ''})
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.line_chart(info["df"][["Close", "EMA50", "SMA200"]], height=340)
    return info


# ───────────────────────────────────────────────
# Sidebar
# ───────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div class="im-side-brand">
          <div class="name">IndianMarket</div>
          <div class="tag">Equity research terminal · NSE / BSE</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="im-side-section">Instrument</div>', unsafe_allow_html=True)
    st.caption("Select the stock from the main research field.")

    period = st.selectbox("Lookback", ["6mo", "1y", "2y", "5y"], index=2)
    export_pdf = st.toggle("Export PDF with research", value=False)

    st.markdown('<div class="im-side-section">Scan universe</div>', unsafe_allow_html=True)
    universe = st.radio(
        "Universe",
        ["Suggested stocks", "Portfolio", "Custom"],
        index=0,
        label_visibility="collapsed",
    )
    custom_list = st.text_area(
        "Custom symbols",
        value="RELIANCE,TCS,INFY,HDFCBANK,ICICIBANK,SBIN,ITC,LT",
        height=68,
        label_visibility="collapsed",
    ).upper()

    st.markdown('<div class="im-side-section">Intelligence</div>', unsafe_allow_html=True)
    use_llm = st.toggle("LLM thesis", value=False)
    llm_key = st.text_input("API key", type="password", placeholder="GROQ_API_KEY or paste")

    if use_llm and is_llm_available(api_key=llm_key or None):
        st.success("LLM connected", icon="✨")
    elif use_llm:
        st.caption("No key — rule-based synthesis")

    st.markdown("---")
    st.caption("Educational use only. Not investment advice.")

llm_config = {
    "enabled": use_llm,
    "api_key": llm_key or None,
    "base_url": None,
    "model": None,
}

if universe == "Suggested stocks":
    scan_tickers = [s["ticker"] for s in SUGGESTED_STOCKS]
elif universe == "Portfolio":
    pfs = list_portfolios()
    scan_tickers = []
    for p in pfs:
        scan_tickers += [h["ticker"] for h in get_holdings(p["id"])]
    scan_tickers = sorted(set(scan_tickers))
else:
    scan_tickers = [p.strip() for p in custom_list.replace(";", ",").split(",") if p.strip()]

# ───────────────────────────────────────────────
# Hero
# ───────────────────────────────────────────────
st.markdown(
    f"""
    <div class="im-hero">
      <div class="im-brand">
        <div class="im-logo">IM</div>
        <div>
          <p class="im-title">Research Terminal</p>
          <p class="im-subtitle">Multi-agent equity intelligence for Indian markets</p>
        </div>
      </div>
      <div class="im-badge-row">
        <span class="im-badge live">Live data</span>
        <span class="im-badge">NSE / BSE</span>
        <span class="im-badge">{datetime.now().strftime('%d %b %Y')}</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Stock input — primary frontend control
st.markdown(
    """
    <div class="im-section" style="margin-top:0.25rem;">
      <div class="im-section-label">Stock research</div>
      <p class="im-section-title">Enter a stock symbol</p>
      <p class="im-section-desc">Type an NSE/BSE symbol such as RELIANCE, TCS, INFY or HDFCBANK.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

ticker_col, period_col = st.columns([3, 1])
with ticker_col:
    ticker = st.text_input(
        "Stock symbol",
        value="RELIANCE",
        placeholder="Enter stock symbol, e.g. RELIANCE",
        key="main_ticker",
    ).upper().strip()
with period_col:
    period = st.selectbox("Lookback", ["6mo", "1y", "2y", "5y"], index=2, key="main_period")

if ticker.endswith(".NS") or ticker.endswith(".BO"):
    ticker = ticker[:-3]

# Command bar
b1, b2, b3, b4 = st.columns(4)
run_chart = b1.button("Load chart", type="primary", use_container_width=True)
run_scan = b2.button("MA scan", use_container_width=True)
run_research = b3.button("Run research", use_container_width=True)
run_alerts = b4.button("Alerts", use_container_width=True)

# Auto-load chart first visit
if ticker and "chart_loaded" not in st.session_state:
    st.session_state["chart_loaded"] = True
    run_chart = True

# ───────────────────────────────────────────────
# Section 1 — Chart
# ───────────────────────────────────────────────
st.markdown(
    f"""
    <div class="im-section">
      <div class="im-section-label">Overview</div>
      <p class="im-section-title">{ticker or 'Select a symbol'}</p>
      <p class="im-section-desc">Price, EMA50, SMA200 and last crossover date</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if ticker and (run_chart or run_research):
    show_chart(ticker, period)
elif not ticker:
    st.markdown(
        '<div class="im-empty"><strong>No symbol selected</strong>Enter a ticker in the sidebar to begin.</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="im-empty"><strong>Chart ready</strong>Press <b>Load chart</b> to render price structure.</div>',
        unsafe_allow_html=True,
    )

# ───────────────────────────────────────────────
# Section 2 — MA scan
# ───────────────────────────────────────────────
st.markdown(
    """
    <div class="im-section">
      <div class="im-section-label">Screening</div>
      <p class="im-section-title">EMA50 × SMA200 board</p>
      <p class="im-section-desc">Full universe table with crossover dates</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if run_scan:
    if not scan_tickers:
        st.warning("No symbols in selected universe")
        st.session_state["ma_rows"] = []
    else:
        with st.spinner(f"Scanning {len(scan_tickers)} symbols…"):
            st.session_state["ma_rows"] = scan_ma_crossovers(scan_tickers, period="2y")

rows = st.session_state.get("ma_rows") or []
if rows:
    bull = [r for r in rows if r.get("cross_status") == "bullish_cross"]
    bear = [r for r in rows if r.get("cross_status") == "bearish_cross"]
    above = [r for r in rows if r.get("price_vs_sma200") == "above"]

    summary = "".join(
        [
            metric_card("Bullish crosses", str(len(bull)), "up"),
            metric_card("Bearish crosses", str(len(bear)), "down"),
            metric_card("Above SMA200", str(len(above)), "accent"),
            metric_card("Symbols scanned", str(len(rows))),
        ]
    )
    st.markdown(f'<div class="im-metrics">{summary}</div>', unsafe_allow_html=True)

    st.dataframe(
        [
            {
                "Ticker": r.get("ticker"),
                "Price": r.get("price"),
                "EMA50": r.get("ema50"),
                "SMA200": r.get("sma200"),
                "Cross status": r.get("cross_status"),
                "Crossover date": r.get("crossover_date") or "—",
                "vs SMA200": r.get("price_vs_sma200"),
                "Signal": r.get("alert") or r.get("error"),
            }
            for r in rows
        ],
        use_container_width=True,
        height=400,
    )

    if bull or bear:
        st.markdown('<div class="im-panel-title">Fresh crossovers</div>', unsafe_allow_html=True)
        for r in bull:
            st.markdown(
                f'<div class="im-alert bull"><strong>{r["ticker"]}</strong> · {r.get("alert")} · '
                f'<code>{r.get("crossover_date") or "N/A"}</code></div>',
                unsafe_allow_html=True,
            )
        for r in bear:
            st.markdown(
                f'<div class="im-alert bear"><strong>{r["ticker"]}</strong> · {r.get("alert")} · '
                f'<code>{r.get("crossover_date") or "N/A"}</code></div>',
                unsafe_allow_html=True,
            )
else:
    st.markdown(
        '<div class="im-empty"><strong>Scan not run</strong>Press <b>MA scan</b> to populate the board.</div>',
        unsafe_allow_html=True,
    )

# ───────────────────────────────────────────────
# Section 3 — Research
# ───────────────────────────────────────────────
st.markdown(
    """
    <div class="im-section">
      <div class="im-section-label">Intelligence</div>
      <p class="im-section-title">Multi-agent research</p>
      <p class="im-section-desc">Technical BUY / SELL / HOLD with full agent stack</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if run_research and ticker:
    with st.spinner(f"Running agents on {ticker}…"):
        try:
            orch = ResearchOrchestrator(
                ticker=ticker, period=period, llm_config=llm_config
            )
            path = orch.run(export_pdf=export_pdf)
            syn = orch.results.get("synthesis", {})
            tech = orch.results.get("technical", {})
            market = orch.results.get("market_data", {})

            action = syn.get("action") or syn.get("bias") or "HOLD"
            st.markdown(
                f"""
                <div class="im-panel" style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem;">
                  <div>
                    <div class="im-panel-title">Technical recommendation</div>
                    {action_pill(str(action))}
                  </div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size:0.85rem;color:var(--text-muted);">
                    Score {tech.get('action_score', '—')} &nbsp;·&nbsp; RSI {tech.get('rsi_14', '—')}
                    &nbsp;·&nbsp; ₹{market.get('current_price', '—')}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            rec_cards = "".join(
                [
                    metric_card("Action", str(action).upper()),
                    metric_card("Score", str(tech.get("action_score", "—"))),
                    metric_card("RSI 14", str(tech.get("rsi_14", "—"))),
                    metric_card("Price", f"₹{market.get('current_price', '—')}", "accent"),
                ]
            )
            st.markdown(f'<div class="im-metrics">{rec_cards}</div>', unsafe_allow_html=True)

            with st.expander("Full research report", expanded=True):
                st.markdown(syn.get("report_markdown", "_No report_"))
            st.caption(f"Saved · {path}")
        except Exception as e:
            st.error(str(e))
            with st.expander("Details"):
                st.code(traceback.format_exc())
elif run_research:
    st.warning("Enter a symbol in the sidebar first")
else:
    st.markdown(
        '<div class="im-empty"><strong>Research idle</strong>Press <b>Run research</b> for BUY / SELL / HOLD and full report.</div>',
        unsafe_allow_html=True,
    )

# ───────────────────────────────────────────────
# Section 4 — Alerts
# ───────────────────────────────────────────────
st.markdown(
    """
    <div class="im-section">
      <div class="im-section-label">Monitoring</div>
      <p class="im-section-title">Alert scan</p>
      <p class="im-section-desc">Price, RSI, and moving-average conditions</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if run_alerts:
    targets = scan_tickers or ([ticker] if ticker else [])
    if not targets:
        st.warning("No symbols to scan")
    else:
        with st.spinner("Evaluating alerts…"):
            alert_rows = evaluate_alerts(
                targets,
                day_change_abs_pct=2.0,
                check_rsi=True,
                check_ma_cross=True,
            )
        triggered = [r for r in alert_rows if r.get("alerts")]
        st.markdown(
            f"""
            <div class="im-metrics">
              {metric_card("Triggered", str(len(triggered)), "down" if triggered else "up")}
              {metric_card("Scanned", str(len(alert_rows)))}
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.dataframe(
            [
                {
                    "Ticker": r.get("ticker"),
                    "Price": r.get("price"),
                    "EMA50": r.get("ema50"),
                    "SMA200": r.get("sma200"),
                    "Cross": r.get("cross_status"),
                    "Cross date": r.get("crossover_date") or "—",
                    "Alerts": "; ".join(r.get("alerts") or []) or "—",
                }
                for r in alert_rows
            ],
            use_container_width=True,
            height=360,
        )
else:
    st.markdown(
        '<div class="im-empty"><strong>Alerts idle</strong>Press <b>Alerts</b> to evaluate the current universe.</div>',
        unsafe_allow_html=True,
    )

# ───────────────────────────────────────────────
# Portfolios
# ───────────────────────────────────────────────
with st.expander("Portfolios", expanded=False):
    pfs = list_portfolios()
    if pfs:
        for p in pfs:
            hs = get_holdings(p["id"])
            tickers_str = ", ".join(h["ticker"] for h in hs) or "(empty)"
            st.markdown(f"**{p['name']}** — `{tickers_str}`")
    c1, c2 = st.columns(2)
    with c1:
        nn = st.text_input("New portfolio name", placeholder="e.g. Core")
        if st.button("Create portfolio") and nn:
            create_portfolio(nn)
            st.rerun()
    with c2:
        if pfs:
            add_to = st.selectbox("Add to", [p["name"] for p in pfs])
            add_tk = st.text_input("Ticker", placeholder="INFY").upper().strip()
            if st.button("Add holding") and add_tk:
                pid = next(p["id"] for p in pfs if p["name"] == add_to)
                add_holding(pid, add_tk)
                st.rerun()

# Footer
st.markdown(
    """
    <div class="im-footer">
      <span>IndianMarket · Multi-agent research system</span>
      <span>Educational only · Not financial advice · SEBI-registered advisor recommended</span>
    </div>
    """,
    unsafe_allow_html=True,
)

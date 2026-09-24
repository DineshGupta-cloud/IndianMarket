"""
IndianMarket – ONE DASHBOARD
Search · Chart · MA table (with crossover dates) · Research · Alerts

Run:  streamlit run app.py
"""

import streamlit as st
import traceback

from agents.orchestrator import ResearchOrchestrator
from utils.llm_client import is_llm_available
from utils.alerts import evaluate_alerts
from utils.charts import fetch_chart_frame
from utils.ma_scan import scan_ma_crossovers
from utils.portfolio_store import (
    SUGGESTED_STOCKS,
    add_holding,
    create_portfolio,
    get_holdings,
    init_db,
    list_portfolios,
    tickers_csv,
)

st.set_page_config(
    page_title="IndianMarket Dashboard",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db(seed_examples=True)

# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🇮🇳 IndianMarket")
    st.caption("Single dashboard")

    ticker = st.text_input("Search ticker", value="RELIANCE").upper().strip()
    if ticker.endswith(".NS") or ticker.endswith(".BO"):
        ticker = ticker[:-3]

    period = st.selectbox("Period", ["6mo", "1y", "2y", "5y"], index=2)
    export_pdf = st.checkbox("PDF on research", value=False)

    st.markdown("---")
    st.markdown("**MA scan universe**")
    universe = st.radio(
        "Scan",
        ["Suggested stocks", "Portfolio", "Custom"],
        index=0,
    )
    custom_list = st.text_input(
        "Custom tickers",
        value="RELIANCE,TCS,INFY,HDFCBANK,ICICIBANK,SBIN,ITC,LT",
    ).upper()

    st.markdown("---")
    use_llm = st.checkbox("LLM thesis", value=False)
    llm_key = st.text_input("API key", type="password", placeholder=".env GROQ_API_KEY")
    st.caption("Educational only • Not advice")

llm_config = {
    "enabled": use_llm,
    "api_key": llm_key or None,
    "base_url": None,
    "model": None,
}

# Resolve scan list
if universe == "Suggested stocks":
    scan_tickers = [s["ticker"] for s in SUGGESTED_STOCKS]
elif universe == "Portfolio":
    pfs = list_portfolios()
    if pfs:
        scan_tickers = [h["ticker"] for h in get_holdings(pfs[0]["id"])]
        for p in pfs[1:]:
            scan_tickers += [h["ticker"] for h in get_holdings(p["id"])]
        scan_tickers = sorted(set(scan_tickers))
    else:
        scan_tickers = []
else:
    scan_tickers = [p.strip() for p in custom_list.replace(";", ",").split(",") if p.strip()]

# ---------------------------------------------------------------------------
# Header actions
# ---------------------------------------------------------------------------
st.title("IndianMarket Dashboard")
st.caption("Chart · EMA50/SMA200 with **crossover date** · Research · Alerts — all in one place")

c_btn1, c_btn2, c_btn3, c_btn4 = st.columns(4)
run_chart = c_btn1.button("📈 Load chart", type="primary", use_container_width=True)
run_scan = c_btn2.button("📊 Run MA scan", use_container_width=True)
run_research = c_btn3.button("🤖 Run research", use_container_width=True)
run_alerts = c_btn4.button("🔔 Quick alerts", use_container_width=True)

# ---------------------------------------------------------------------------
# ROW 1: Chart + key metrics for searched ticker
# ---------------------------------------------------------------------------
st.markdown("---")
st.subheader(f"1. Chart & crossover — **{ticker or '—'}**")

if run_chart or run_research or (ticker and "chart_loaded" not in st.session_state):
    # Auto-load chart once per session for default ticker
    st.session_state["chart_loaded"] = True
    do_chart = True
else:
    do_chart = run_chart

if ticker and (do_chart or run_chart or run_research):
    info = fetch_chart_frame(ticker, period=period)
    if info.get("error") or info.get("df") is None:
        st.warning(info.get("error", "No chart data"))
    else:
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Price", f"₹{info.get('price')}")
        m2.metric("EMA50", f"₹{info.get('ema50')}")
        m3.metric("SMA200", f"₹{info.get('sma200')}")
        m4.metric("vs SMA200", info.get("price_vs_sma200") or "—")
        m5.metric("Last cross date", info.get("crossover_date") or "—")

        st.caption(
            f"Status: **{info.get('cross_status')}** · "
            f"Last EMA50/SMA200 crossover: **{info.get('crossover_date') or 'N/A'}** "
            f"({info.get('crossover_kind') or ''})"
        )
        st.line_chart(info["df"][["Close", "EMA50", "SMA200"]])
elif not ticker:
    st.info("Enter a ticker in the sidebar.")
else:
    st.info("Click **Load chart** to show price / EMA50 / SMA200.")

# ---------------------------------------------------------------------------
# ROW 2: MA scan table (all stocks in universe) WITH DATES
# ---------------------------------------------------------------------------
st.markdown("---")
st.subheader("2. MA scan board (all symbols in universe)")
st.caption("Includes **crossover date** when EMA50 last crossed SMA200.")

if run_scan or st.session_state.get("ma_rows"):
    if run_scan:
        if not scan_tickers:
            st.warning("No tickers to scan")
            st.session_state["ma_rows"] = []
        else:
            with st.spinner(f"Scanning {len(scan_tickers)} symbols..."):
                st.session_state["ma_rows"] = scan_ma_crossovers(scan_tickers, period="2y")

    rows = st.session_state.get("ma_rows") or []
    if rows:
        bull = [r for r in rows if r.get("cross_status") == "bullish_cross"]
        bear = [r for r in rows if r.get("cross_status") == "bearish_cross"]
        above = [r for r in rows if r.get("price_vs_sma200") == "above"]

        a, b, c = st.columns(3)
        a.metric("Fresh bullish cross", len(bull))
        b.metric("Fresh bearish cross", len(bear))
        c.metric("Price above SMA200", len(above))

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
                    "Alert": r.get("alert") or r.get("error"),
                }
                for r in rows
            ],
            use_container_width=True,
            height=420,
        )

        if bull or bear:
            st.markdown("**Fresh crossovers**")
            for r in bull + bear:
                st.warning(
                    f"{r['ticker']}: {r.get('alert')} · date **{r.get('crossover_date') or 'N/A'}**"
                )
else:
    st.info("Click **Run MA scan** to list all symbols with crossover dates.")

# ---------------------------------------------------------------------------
# ROW 3: Research + recommendation
# ---------------------------------------------------------------------------
st.markdown("---")
st.subheader("3. Multi-agent research (BUY / SELL / HOLD)")

if run_research and ticker:
    with st.spinner(f"Researching {ticker}..."):
        try:
            orch = ResearchOrchestrator(
                ticker=ticker, period=period, llm_config=llm_config
            )
            path = orch.run(export_pdf=export_pdf)
            syn = orch.results.get("synthesis", {})
            tech = orch.results.get("technical", {})
            market = orch.results.get("market_data", {})

            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Action", syn.get("action") or syn.get("bias", "—"))
            r2.metric("Score", tech.get("action_score", "—"))
            r3.metric("RSI", tech.get("rsi_14", "—"))
            r4.metric("Price", f"₹{market.get('current_price', '—')}")

            st.markdown(syn.get("report_markdown", "_No report_"))
            st.caption(f"Saved: {path}")
        except Exception as e:
            st.error(str(e))
            st.code(traceback.format_exc())
elif run_research:
    st.warning("Enter a ticker first")

# ---------------------------------------------------------------------------
# ROW 4: Quick alerts on same universe
# ---------------------------------------------------------------------------
st.markdown("---")
st.subheader("4. Quick alerts (price / RSI / MA)")

if run_alerts:
    targets = scan_tickers or ([ticker] if ticker else [])
    if not targets:
        st.warning("No symbols")
    else:
        with st.spinner("Alert scan..."):
            alert_rows = evaluate_alerts(
                targets,
                day_change_abs_pct=2.0,
                check_rsi=True,
                check_ma_cross=True,
            )
        triggered = [r for r in alert_rows if r.get("alerts")]
        st.write(f"Triggered: **{len(triggered)}** / {len(alert_rows)}")
        st.dataframe(
            [
                {
                    "Ticker": r.get("ticker"),
                    "Price": r.get("price"),
                    "EMA50": r.get("ema50"),
                    "SMA200": r.get("sma200"),
                    "Cross": r.get("cross_status"),
                    "Cross date": r.get("crossover_date", "—")
                    if "crossover_date" in r
                    else "—",
                    "Alerts": "; ".join(r.get("alerts") or []),
                }
                for r in alert_rows
            ],
            use_container_width=True,
            height=360,
        )

# ---------------------------------------------------------------------------
# ROW 5: Portfolio strip (optional)
# ---------------------------------------------------------------------------
st.markdown("---")
with st.expander("Portfolios (optional)"):
    pfs = list_portfolios()
    if pfs:
        for p in pfs:
            hs = get_holdings(p["id"])
            st.write(f"**{p['name']}**: ", ", ".join(h["ticker"] for h in hs) or "(empty)")
    nn = st.text_input("New portfolio name")
    if st.button("Create portfolio") and nn:
        create_portfolio(nn)
        st.rerun()
    if pfs:
        add_to = st.selectbox("Add ticker to", [p["name"] for p in pfs])
        add_tk = st.text_input("Ticker to add").upper().strip()
        if st.button("Add holding") and add_tk:
            pid = next(p["id"] for p in pfs if p["name"] == add_to)
            add_holding(pid, add_tk)
            st.rerun()

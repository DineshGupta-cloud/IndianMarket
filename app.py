"""
IndianMarket – Research | Portfolios | Alerts | MA Scan | Charts
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
    delete_portfolio,
    export_json,
    get_holdings,
    init_db,
    list_portfolios,
    remove_holding,
    tickers_csv,
)
from utils.telegram_notify import format_alert_message, is_telegram_configured, send_telegram_message

st.set_page_config(
    page_title="IndianMarket",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db(seed_examples=True)

with st.sidebar:
    st.title("🇮🇳 IndianMarket")
    st.caption("Research · Charts · MA alerts")

    period = st.selectbox("History period", ["6mo", "1y", "2y", "5y"], index=1)
    export_pdf = st.checkbox("Export PDF", value=True)

    st.markdown("---")
    st.markdown("**LLM (optional)**")
    use_llm = st.checkbox("Enable LLM thesis", value=True)
    llm_key = st.text_input("API key", type="password", placeholder="Or use .env GROQ_API_KEY")
    llm_provider = st.selectbox("Provider", ["Groq (free tier)", "OpenAI", "Custom"], index=0)
    if llm_provider == "OpenAI":
        default_base, default_model = "https://api.openai.com/v1", "gpt-4o-mini"
    else:
        default_base, default_model = "https://api.groq.com/openai/v1", "llama-3.3-70b-versatile"
    llm_base = st.text_input("Base URL", value=default_base)
    llm_model = st.text_input("Model", value=default_model)

    if use_llm and is_llm_available(api_key=llm_key or None):
        st.success("LLM key ready")
    elif use_llm:
        st.info("No key → rule-based synthesis")

    st.markdown("---")
    st.caption("Educational only • Not investment advice")

llm_config = {
    "enabled": use_llm,
    "api_key": llm_key or None,
    "base_url": llm_base or None,
    "model": llm_model or None,
}


def show_chart(ticker: str, chart_period: str = "1y"):
    """Render Close + EMA50 + SMA200 on screen."""
    info = fetch_chart_frame(ticker, period=chart_period)
    if info.get("error") or info.get("df") is None:
        st.warning(f"Chart unavailable: {info.get('error', 'no data')}")
        return
    df = info["df"][["Close", "EMA50", "SMA200"]].copy()
    st.subheader(f"Chart: {info['ticker']}")
    st.caption(
        f"Price ₹{info.get('price')} · EMA50 ₹{info.get('ema50')} · "
        f"SMA200 ₹{info.get('sma200')} · Status: {info.get('cross_status')}"
    )
    st.line_chart(df)


def run_research(ticker_arg: str):
    with st.spinner(f"Running multi-agent research on **{ticker_arg}**..."):
        try:
            orch = ResearchOrchestrator(
                ticker=ticker_arg, period=period, llm_config=llm_config
            )
            report_path = orch.run(export_pdf=export_pdf)
            synthesis = orch.results.get("synthesis", {})

            if synthesis.get("portfolio_summaries"):
                st.success(f"Portfolio report ready: {ticker_arg}")
                st.dataframe(synthesis["portfolio_summaries"], use_container_width=True)
            else:
                market = orch.results.get("market_data", {})
                tech = orch.results.get("technical", {})
                llm_out = synthesis.get("llm") or {}

                st.success(f"Report ready: **{synthesis.get('company', ticker_arg)}**")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Company", synthesis.get("company", ticker_arg))
                c2.metric(
                    "Price",
                    f"₹{market.get('current_price', 'N/A')}",
                    f"{market.get('day_change_pct', 0):+.2f}%",
                )
                c3.metric("Action", synthesis.get("action") or synthesis.get("bias", "N/A"))
                c4.metric("RSI", tech.get("rsi_14", "N/A"), tech.get("rsi_signal", ""))

                # Chart for single-ticker research
                primary = ticker_arg.split(",")[0].strip()
                show_chart(primary, chart_period=period)

                if llm_out and not llm_out.get("error") and llm_out.get("thesis"):
                    st.subheader("LLM Thesis")
                    st.write(llm_out["thesis"])

            st.subheader("Full report")
            st.markdown(synthesis.get("report_markdown", "_No report_"))

            d1, d2 = st.columns(2)
            with d1:
                st.download_button(
                    "📄 Markdown",
                    data=synthesis.get("report_markdown", ""),
                    file_name=report_path.name,
                    mime="text/markdown",
                    use_container_width=True,
                )
            pdf_path = report_path.with_suffix(".pdf")
            if pdf_path.exists():
                with d2:
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            "📄 PDF",
                            data=f,
                            file_name=pdf_path.name,
                            mime="application/pdf",
                            use_container_width=True,
                        )
        except Exception as e:
            st.error(f"Research failed: {e}")
            st.code(traceback.format_exc())


tab_research, tab_charts, tab_ma, tab_portfolios, tab_alerts, tab_stocks = st.tabs(
    [
        "📊 Research",
        "📈 Charts",
        "📉 MA Scan",
        "💼 Portfolios",
        "🔔 Alerts",
        "📋 Stocks",
    ]
)

# ===== Research =====
with tab_research:
    st.header("Quick research")
    mode = st.radio("Mode", ["Single Stock", "Ad-hoc list"], horizontal=True)
    if mode == "Single Stock":
        t_in = st.text_input("NSE ticker", value="RELIANCE", key="res_t").upper().strip()
    else:
        t_in = st.text_input("Tickers", value="RELIANCE,TCS,INFY", key="res_list").upper().strip()

    if st.button("🚀 Run Research", type="primary", key="run_research"):
        parts = []
        for p in t_in.replace(";", ",").split(","):
            p = p.strip()
            if p.endswith(".NS") or p.endswith(".BO"):
                p = p[:-3]
            if p:
                parts.append(p)
        if not parts:
            st.warning("Enter at least one ticker")
        else:
            run_research(",".join(parts))

# ===== Charts =====
with tab_charts:
    st.header("Price chart (Close + EMA50 + SMA200)")
    chart_ticker = st.text_input("Search ticker", value="RELIANCE", key="chart_t").upper().strip()
    chart_period = st.selectbox("Chart period", ["6mo", "1y", "2y", "5y"], index=1, key="chart_p")
    if st.button("Show chart", type="primary", key="show_chart"):
        if chart_ticker.endswith(".NS") or chart_ticker.endswith(".BO"):
            chart_ticker = chart_ticker[:-3]
        if not chart_ticker:
            st.warning("Enter a ticker")
        else:
            show_chart(chart_ticker, chart_period)
            # Optional quick metrics
            info = fetch_chart_frame(chart_ticker, chart_period)
            if not info.get("error"):
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Price", f"₹{info.get('price')}")
                m2.metric("EMA50", f"₹{info.get('ema50')}")
                m3.metric("SMA200", f"₹{info.get('sma200')}")
                m4.metric("Cross", info.get("cross_status", "n/a"))

# ===== MA Scan (EMA50 / SMA200) =====
with tab_ma:
    st.header("EMA50 × SMA200 scan")
    st.caption(
        "Lists price vs SMA200 and EMA50/SMA200 position or fresh crossover. "
        "Scans suggested list, a portfolio, or custom tickers (not entire NSE)."
    )

    scan_src = st.radio(
        "Universe",
        ["Suggested stocks", "Saved portfolio", "Custom list"],
        horizontal=True,
        key="ma_src",
    )
    scan_tickers: list[str] = []
    if scan_src == "Suggested stocks":
        scan_tickers = [s["ticker"] for s in SUGGESTED_STOCKS]
    elif scan_src == "Saved portfolio":
        pfs = list_portfolios()
        if not pfs:
            st.warning("No portfolios")
        else:
            lm = {p["name"]: p["id"] for p in pfs}
            pn = st.selectbox("Portfolio", list(lm.keys()), key="ma_pf")
            scan_tickers = [h["ticker"] for h in get_holdings(lm[pn])]
    else:
        raw = st.text_input(
            "Tickers",
            value=",".join(s["ticker"] for s in SUGGESTED_STOCKS[:10]),
            key="ma_custom",
        ).upper()
        scan_tickers = [p.strip() for p in raw.replace(";", ",").split(",") if p.strip()]

    filter_only_cross = st.checkbox("Only show fresh crossovers (bullish/bearish cross)", value=False)
    send_tg = st.checkbox("Send results to Telegram", value=False)
    if send_tg and not is_telegram_configured():
        st.info("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env to enable Telegram.")

    if st.button("🔍 Run MA scan", type="primary", key="ma_run"):
        if not scan_tickers:
            st.warning("No tickers")
        else:
            with st.spinner(f"Scanning {len(scan_tickers)} symbols..."):
                rows = scan_ma_crossovers(scan_tickers, period="1y")

            if filter_only_cross:
                rows_view = [
                    r
                    for r in rows
                    if r.get("cross_status") in ("bullish_cross", "bearish_cross")
                ]
            else:
                rows_view = rows

            bull = [r for r in rows if r.get("cross_status") == "bullish_cross"]
            bear = [r for r in rows if r.get("cross_status") == "bearish_cross"]
            above = [r for r in rows if r.get("price_vs_sma200") == "above"]

            a, b, c = st.columns(3)
            a.metric("Fresh bullish cross", len(bull))
            b.metric("Fresh bearish cross", len(bear))
            c.metric("Price above SMA200", len(above))

            st.subheader("Results")
            st.dataframe(
                [
                    {
                        "Ticker": r.get("ticker"),
                        "Price": r.get("price"),
                        "EMA50": r.get("ema50"),
                        "SMA200": r.get("sma200"),
                        "Cross": r.get("cross_status"),
                        "vs SMA200": r.get("price_vs_sma200"),
                        "Alert": r.get("alert") or r.get("error"),
                    }
                    for r in rows_view
                ],
                use_container_width=True,
            )

            if bull or bear:
                st.subheader("Fresh crossovers")
                for r in bull + bear:
                    st.warning(f"**{r['ticker']}**: {r.get('alert')}")

            if send_tg and is_telegram_configured():
                msg_rows = [
                    {
                        "ticker": r["ticker"],
                        "price": r.get("price"),
                        "day_change_pct": 0,
                        "rsi_14": "—",
                        "alerts": [r.get("alert") or r.get("cross_status")],
                    }
                    for r in rows
                    if r.get("cross_status") in ("bullish_cross", "bearish_cross")
                    or r.get("price_vs_sma200")
                ]
                text = format_alert_message(msg_rows[:20])
                res = send_telegram_message("MA Scan\n" + text)
                if res.get("ok"):
                    st.success("Sent to Telegram")
                else:
                    st.error(res.get("error", "Telegram failed"))

# ===== Portfolios (compact) =====
with tab_portfolios:
    st.header("Saved portfolios")
    portfolios = list_portfolios()
    with st.expander("Create portfolio"):
        nn = st.text_input("Name", key="npn")
        if st.button("Create", key="npc") and nn:
            try:
                create_portfolio(nn)
                st.rerun()
            except Exception as e:
                st.error(str(e))
    if portfolios:
        names = {f"{p['name']}": p for p in portfolios}
        choice = st.selectbox("Portfolio", list(names.keys()), key="pf2")
        pid = names[choice]["id"]
        holdings = get_holdings(pid)
        st.dataframe(holdings, use_container_width=True)
        add_t = st.text_input("Add ticker", key="pfa").upper().strip()
        if st.button("Add") and add_t:
            add_holding(pid, add_t)
            st.rerun()
        if holdings and st.button("Research portfolio"):
            run_research(tickers_csv(pid))

# ===== Alerts =====
with tab_alerts:
    st.header("Watchlist alerts")
    source = st.radio("Source", ["Suggested stocks", "Custom"], horizontal=True, key="al_src")
    if source == "Suggested stocks":
        tickers = [s["ticker"] for s in SUGGESTED_STOCKS]
    else:
        tickers = [
            p.strip()
            for p in st.text_input("Tickers", "RELIANCE,TCS,HDFCBANK", key="al_t").upper().split(",")
            if p.strip()
        ]
    check_ma = st.checkbox("EMA50 / SMA200 alerts", value=True)
    check_rsi = st.checkbox("RSI", value=True)
    if st.button("Run alert scan", type="primary", key="al_run"):
        with st.spinner("Scanning..."):
            rows = evaluate_alerts(
                tickers,
                day_change_abs_pct=2.0,
                check_rsi=check_rsi,
                check_ma_cross=check_ma,
            )
        triggered = [r for r in rows if r.get("alerts")]
        st.subheader(f"Triggered ({len(triggered)})")
        for r in triggered:
            st.markdown(f"**{r['ticker']}** ₹{r.get('price')} · RSI {r.get('rsi_14')}")
            for a in r["alerts"]:
                st.warning(a)
        st.dataframe(
            [
                {
                    "Ticker": r.get("ticker"),
                    "Price": r.get("price"),
                    "EMA50": r.get("ema50"),
                    "SMA200": r.get("sma200"),
                    "Cross": r.get("cross_status"),
                    "Alerts": "; ".join(r.get("alerts") or []),
                }
                for r in rows
            ],
            use_container_width=True,
        )

# ===== Stocks =====
with tab_stocks:
    st.header("Suggested NSE stocks")
    st.dataframe(SUGGESTED_STOCKS, use_container_width=True)

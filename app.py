"""
IndianMarket – Single App
  Research | Portfolios | Alerts | Stock list

Run:  streamlit run app.py
"""

import streamlit as st
import traceback

from agents.orchestrator import ResearchOrchestrator
from utils.llm_client import is_llm_available
from utils.alerts import evaluate_alerts
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

st.set_page_config(
    page_title="IndianMarket",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db(seed_examples=True)

with st.sidebar:
    st.title("🇮🇳 IndianMarket")
    st.caption("Research · Portfolios · Alerts")

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
                st.subheader("Summary")
                st.dataframe(synthesis["portfolio_summaries"], use_container_width=True)
            else:
                market = orch.results.get("market_data", {})
                fii = orch.results.get("fii_dii", {})
                tech = orch.results.get("technical", {})
                sentiment = orch.results.get("sentiment", {})
                llm_out = synthesis.get("llm") or {}

                st.success(f"Report ready: **{synthesis.get('company', ticker_arg)}**")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Company", synthesis.get("company", ticker_arg))
                c2.metric(
                    "Price",
                    f"₹{market.get('current_price', 'N/A')}",
                    f"{market.get('day_change_pct', 0):+.2f}%",
                )
                c3.metric("Bias", synthesis.get("bias", "N/A"))
                c4.metric("RSI", tech.get("rsi_14", "N/A"), tech.get("rsi_signal", ""))

                if llm_out and not llm_out.get("error") and llm_out.get("thesis"):
                    st.subheader("LLM Thesis")
                    st.write(llm_out["thesis"])

                if not fii.get("error"):
                    st.subheader("FII / DII (market-wide)")
                    f1, f2, f3 = st.columns(3)
                    latest = fii.get("latest", {})
                    f1.metric("FII Net", latest.get("fii_net", "N/A"))
                    f2.metric("DII Net", latest.get("dii_net", "N/A"))
                    f3.write(fii.get("flow_bias", ""))

                if sentiment.get("post_count", 0) > 0:
                    st.caption(
                        f"Reddit: {sentiment.get('sentiment_label')} "
                        f"({sentiment.get('post_count')} posts)"
                    )

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
            st.caption(f"Saved: `{report_path}`")
        except Exception as e:
            st.error(f"Research failed: {e}")
            st.code(traceback.format_exc())


tab_research, tab_portfolios, tab_alerts, tab_stocks = st.tabs(
    ["📊 Research", "💼 My Portfolios", "🔔 Alerts", "📋 Stock list"]
)

# ===== Research =====
with tab_research:
    st.header("Quick research")
    mode = st.radio("Mode", ["Single Stock", "Ad-hoc list"], horizontal=True)
    if mode == "Single Stock":
        t_in = st.text_input("NSE ticker", value="RELIANCE").upper().strip()
    else:
        t_in = st.text_input("Tickers (comma-separated)", value="RELIANCE,TCS,INFY").upper().strip()

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

# ===== Portfolios =====
with tab_portfolios:
    st.header("Saved portfolios (SQLite)")
    st.caption("File: `data/portfolios.db` — examples load on first run.")

    portfolios = list_portfolios()

    with st.expander("➕ Create portfolio", expanded=not portfolios):
        new_name = st.text_input("Name", placeholder="e.g. My SIP")
        new_notes = st.text_input("Notes (optional)")
        if st.button("Create"):
            try:
                create_portfolio(new_name, new_notes)
                st.success(f"Created **{new_name}**")
                st.rerun()
            except Exception as e:
                st.error(str(e))

    if not portfolios:
        st.info("No portfolios yet.")
    else:
        names = {f"{p['name']} (id {p['id']})": p for p in portfolios}
        choice = st.selectbox("Select portfolio", list(names.keys()), key="pf_select")
        selected = names[choice]
        pid = selected["id"]

        st.write(f"**Notes:** {selected.get('notes') or '—'}")
        holdings = get_holdings(pid)

        if holdings:
            st.dataframe(
                [
                    {
                        "Ticker": h["ticker"],
                        "Qty": h["qty"],
                        "Avg price": h["avg_price"],
                        "Notes": h["notes"],
                    }
                    for h in holdings
                ],
                use_container_width=True,
            )
        else:
            st.warning("No stocks yet.")

        st.subheader("Add stock")
        c1, c2, c3, c4 = st.columns([2, 1, 1, 2])
        with c1:
            suggested = [s["ticker"] for s in SUGGESTED_STOCKS]
            add_ticker = st.selectbox(
                "Pick from list",
                [""] + suggested,
                format_func=lambda x: x or "— or type below —",
                key="add_pick",
            )
            custom_ticker = st.text_input("Or type ticker", placeholder="RELIANCE", key="add_custom")
            ticker_to_add = (custom_ticker or add_ticker or "").upper().strip()
        with c2:
            qty = st.number_input("Qty", min_value=0.0, value=0.0, step=1.0)
        with c3:
            avg_px = st.number_input("Avg price", min_value=0.0, value=0.0, step=1.0)
        with c4:
            h_notes = st.text_input("Note", placeholder="optional", key="hnote")

        if st.button("Add to portfolio"):
            if not ticker_to_add:
                st.warning("Choose or type a ticker")
            else:
                try:
                    add_holding(
                        pid,
                        ticker_to_add,
                        qty=qty or None,
                        avg_price=avg_px or None,
                        notes=h_notes,
                    )
                    st.success(f"Added **{ticker_to_add}**")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

        if holdings:
            st.subheader("Remove stock")
            rm = st.selectbox("Ticker to remove", [h["ticker"] for h in holdings], key="rm")
            if st.button("Remove", type="secondary"):
                remove_holding(pid, rm)
                st.success(f"Removed **{rm}**")
                st.rerun()

        st.markdown("---")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if holdings and st.button("🚀 Research this portfolio", type="primary"):
                run_research(tickers_csv(pid))
        with col_b:
            st.download_button(
                "📥 Export JSON",
                data=export_json(),
                file_name="portfolios_backup.json",
                mime="application/json",
            )
        with col_c:
            if st.button("🗑️ Delete portfolio", type="secondary"):
                delete_portfolio(pid)
                st.success("Deleted")
                st.rerun()

# ===== Alerts =====
with tab_alerts:
    st.header("Watchlist alerts")
    st.caption(
        "Checks price, day % move, and RSI on a portfolio or a custom list. "
        "Run anytime (or schedule later with cron)."
    )

    portfolios = list_portfolios()
    source = st.radio(
        "Scan source",
        ["Saved portfolio", "Custom tickers"],
        horizontal=True,
    )

    tickers: list[str] = []
    if source == "Saved portfolio":
        if not portfolios:
            st.warning("Create a portfolio first.")
        else:
            label_map = {p["name"]: p["id"] for p in portfolios}
            pname = st.selectbox("Portfolio", list(label_map.keys()), key="alert_pf")
            tickers = [h["ticker"] for h in get_holdings(label_map[pname])]
            st.write("Tickers:", ", ".join(tickers) if tickers else "_(empty)_")
    else:
        custom = st.text_input(
            "Tickers",
            value="RELIANCE,TCS,HDFCBANK,INFY",
            key="alert_custom",
        ).upper()
        tickers = [p.strip() for p in custom.replace(";", ",").split(",") if p.strip()]

    st.subheader("Rules")
    r1, r2, r3 = st.columns(3)
    with r1:
        use_above = st.checkbox("Price above")
        price_above = st.number_input("Above ₹", min_value=0.0, value=0.0, step=10.0) if use_above else None
        if not use_above:
            price_above = None
    with r2:
        use_below = st.checkbox("Price below")
        price_below = st.number_input("Below ₹", min_value=0.0, value=0.0, step=10.0) if use_below else None
        if not use_below:
            price_below = None
    with r3:
        use_day = st.checkbox("Day move ±%", value=True)
        day_pct = st.number_input("Threshold %", min_value=0.5, value=2.0, step=0.5) if use_day else None
        if not use_day:
            day_pct = None

    c_rsi1, c_rsi2, c_rsi3 = st.columns(3)
    with c_rsi1:
        check_rsi = st.checkbox("RSI alerts", value=True)
    with c_rsi2:
        rsi_ob = st.number_input("Overbought ≥", min_value=50.0, value=70.0, step=1.0)
    with c_rsi3:
        rsi_os = st.number_input("Oversold ≤", min_value=1.0, value=30.0, step=1.0)

    if st.button("🔍 Run alert scan", type="primary"):
        if not tickers:
            st.warning("No tickers to scan")
        else:
            with st.spinner("Fetching prices & RSI..."):
                rows = evaluate_alerts(
                    tickers,
                    price_above=price_above if price_above and price_above > 0 else None,
                    price_below=price_below if price_below and price_below > 0 else None,
                    day_change_abs_pct=day_pct,
                    rsi_overbought=rsi_ob,
                    rsi_oversold=rsi_os,
                    check_rsi=check_rsi,
                )

            triggered = [r for r in rows if r.get("alerts")]
            quiet = [r for r in rows if not r.get("alerts")]

            st.subheader(f"Triggered ({len(triggered)})")
            if not triggered:
                st.success("No alerts fired with current rules.")
            else:
                for r in triggered:
                    with st.container():
                        st.markdown(
                            f"**{r['ticker']}** · ₹{r.get('price', 'N/A')} "
                            f"({r.get('day_change_pct', 0):+.2f}%) · RSI {r.get('rsi_14', 'N/A')}"
                        )
                        for a in r["alerts"]:
                            st.warning(a)

            with st.expander(f"All snapshots ({len(rows)})"):
                st.dataframe(
                    [
                        {
                            "Ticker": r.get("ticker"),
                            "Price": r.get("price"),
                            "Day %": r.get("day_change_pct"),
                            "RSI": r.get("rsi_14"),
                            "Alerts": "; ".join(r.get("alerts") or []) or "—",
                        }
                        for r in rows
                    ],
                    use_container_width=True,
                )

# ===== Stock list =====
with tab_stocks:
    st.header("Suggested NSE stocks")
    st.dataframe(SUGGESTED_STOCKS, use_container_width=True)
    st.markdown("Any NSE symbol works when adding holdings (e.g. `TATAPOWER`, `DMART`).")

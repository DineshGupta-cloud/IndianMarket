"""
IndianMarket – Single App for Everything
  - Research (single / ad-hoc portfolio)
  - Saved portfolios (SQLite)
  - Optional LLM synthesis
  - PDF / Markdown reports

Run:  streamlit run app.py
"""

import streamlit as st
import traceback

from agents.orchestrator import ResearchOrchestrator
from utils.llm_client import is_llm_available
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

# Init DB + example portfolios on first run
init_db(seed_examples=True)

# ---------------------------------------------------------------------------
# Sidebar: LLM + research settings
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🇮🇳 IndianMarket")
    st.caption("Research + saved portfolios")

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
    """Shared research runner + display."""
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


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_research, tab_portfolios, tab_stocks = st.tabs(
    ["📊 Research", "💼 My Portfolios", "📋 Stock list"]
)

# ===== Research tab =====
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

# ===== Portfolios tab =====
with tab_portfolios:
    st.header("Saved portfolios (SQLite)")
    st.caption("Data file: `data/portfolios.db` — example portfolios are loaded on first run.")

    portfolios = list_portfolios()

    # Create new
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
        st.info("No portfolios yet. Create one above (examples seed automatically on first run).")
    else:
        names = {f"{p['name']} (id {p['id']})": p for p in portfolios}
        choice = st.selectbox("Select portfolio", list(names.keys()))
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
            st.warning("No stocks in this portfolio yet.")

        # Add stock
        st.subheader("Add stock")
        c1, c2, c3, c4 = st.columns([2, 1, 1, 2])
        with c1:
            suggested = [s["ticker"] for s in SUGGESTED_STOCKS]
            add_ticker = st.selectbox(
                "Pick from list",
                [""] + suggested,
                format_func=lambda x: x or "— or type below —",
            )
            custom_ticker = st.text_input("Or type ticker", placeholder="e.g. RELIANCE")
            ticker_to_add = (custom_ticker or add_ticker or "").upper().strip()
        with c2:
            qty = st.number_input("Qty (optional)", min_value=0.0, value=0.0, step=1.0)
        with c3:
            avg_px = st.number_input("Avg price (optional)", min_value=0.0, value=0.0, step=1.0)
        with c4:
            h_notes = st.text_input("Note", placeholder="optional")

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

        # Remove stock
        if holdings:
            st.subheader("Remove stock")
            rm = st.selectbox("Ticker to remove", [h["ticker"] for h in holdings])
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
                "📥 Export all JSON",
                data=export_json(),
                file_name="portfolios_backup.json",
                mime="application/json",
            )
        with col_c:
            if st.button("🗑️ Delete portfolio", type="secondary"):
                delete_portfolio(pid)
                st.success("Deleted")
                st.rerun()

# ===== Stock list tab =====
with tab_stocks:
    st.header("Suggested NSE stocks to add")
    st.caption("Use these tickers in portfolios or quick research.")
    st.dataframe(SUGGESTED_STOCKS, use_container_width=True)
    st.markdown(
        "You can also type **any** NSE symbol (e.g. `TATAPOWER`, `DMART`) when adding holdings."
    )

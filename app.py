"""
IndianMarket – Single App for Everything
----------------------------------------
One Streamlit dashboard for:
  - Single stock research
  - Portfolio (multi-ticker) research
  - Markdown + PDF reports

Run:
    streamlit run app.py
"""

import streamlit as st
from pathlib import Path
import traceback

from agents.orchestrator import ResearchOrchestrator

st.set_page_config(
    page_title="IndianMarket",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🇮🇳 IndianMarket")
    st.caption("Multi-agent research for NSE/BSE")

    mode = st.radio(
        "Mode",
        ["Single Stock", "Portfolio"],
        help="Single = one ticker. Portfolio = comma-separated list.",
    )

    if mode == "Single Stock":
        ticker_input = st.text_input(
            "NSE Ticker",
            value="RELIANCE",
            help="Example: RELIANCE, TCS, HDFCBANK",
        ).upper().strip()
    else:
        ticker_input = st.text_input(
            "Tickers (comma-separated)",
            value="RELIANCE,TCS,INFY",
            help="Example: RELIANCE,TCS,INFY,HDFCBANK",
        ).upper().strip()

    period = st.selectbox("History period", ["6mo", "1y", "2y", "5y"], index=1)
    export_pdf = st.checkbox("Export PDF", value=True)

    run_btn = st.button("🚀 Run Research", type="primary", use_container_width=True)

    st.markdown("---")
    st.markdown("**Agents (parallel)**")
    st.markdown("""
    - Market Data
    - Fundamentals
    - Screener.in
    - Technicals
    - News
    - FII / DII
    - Reddit Sentiment
    - Macro & Risk
    - Synthesis
    """)
    st.markdown("---")
    st.caption("Educational use only • Not investment advice")

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
st.title("IndianMarket Research")
st.caption("One app for single-stock and portfolio analysis")

if not run_btn:
    st.info("Choose **Single Stock** or **Portfolio** in the sidebar, enter ticker(s), then click **Run Research**.")
    st.markdown("""
    ### Quick examples
    | Mode | Input |
    |------|--------|
    | Single | `RELIANCE` |
    | Single | `TCS` |
    | Portfolio | `RELIANCE,TCS,INFY` |
    | Portfolio | `HDFCBANK,ICICIBANK,SBIN` |
    """)
    st.stop()

if not ticker_input:
    st.warning("Please enter at least one ticker.")
    st.stop()

# Normalize tickers
parts = []
for p in ticker_input.replace(";", ",").split(","):
    p = p.strip()
    if p.endswith(".NS") or p.endswith(".BO"):
        p = p[:-3]
    if p:
        parts.append(p)
ticker_arg = ",".join(parts)

with st.spinner(f"Running multi-agent research on **{ticker_arg}** (parallel)..."):
    try:
        orch = ResearchOrchestrator(ticker=ticker_arg, period=period)
        report_path = orch.run(export_pdf=export_pdf)
        synthesis = orch.results.get("synthesis", {})

        # ---- Portfolio view ----
        if synthesis.get("portfolio_summaries"):
            st.success(f"Portfolio report ready for: {ticker_arg}")
            st.subheader("Portfolio Summary")
            st.dataframe(synthesis["portfolio_summaries"], use_container_width=True)

        # ---- Single stock metrics ----
        else:
            market = orch.results.get("market_data", {})
            fii = orch.results.get("fii_dii", {})
            tech = orch.results.get("technical", {})
            sentiment = orch.results.get("sentiment", {})

            st.success(f"Report ready for **{synthesis.get('company', ticker_arg)}**")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Company", synthesis.get("company", ticker_arg))
            c2.metric(
                "Price",
                f"₹{market.get('current_price', 'N/A')}",
                f"{market.get('day_change_pct', 0):+.2f}%",
            )
            c3.metric("Bias", synthesis.get("bias", "N/A"))
            c4.metric("RSI (14)", tech.get("rsi_14", "N/A"), tech.get("rsi_signal", ""))

            st.markdown("---")

            if not fii.get("error"):
                st.subheader("Institutional Flows (market-wide)")
                f1, f2, f3 = st.columns(3)
                latest = fii.get("latest", {})
                f1.metric("FII Net (₹ Cr)", latest.get("fii_net", "N/A"))
                f2.metric("DII Net (₹ Cr)", latest.get("dii_net", "N/A"))
                f3.write(f"**{fii.get('flow_bias', '')}**")
                st.caption(f"As of {fii.get('as_of', 'N/A')}")

            if sentiment.get("post_count", 0) > 0:
                st.subheader("Reddit Sentiment")
                s1, s2 = st.columns(2)
                s1.metric("Label", sentiment.get("sentiment_label", "N/A"))
                s2.metric("Posts analyzed", sentiment.get("post_count", 0))

        # ---- Full report ----
        st.subheader("Full Research Report")
        st.markdown(synthesis.get("report_markdown", "_No report generated_"))

        # ---- Downloads ----
        st.markdown("---")
        d1, d2 = st.columns(2)
        with d1:
            st.download_button(
                label="📄 Download Markdown",
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
                        label="📄 Download PDF",
                        data=f,
                        file_name=pdf_path.name,
                        mime="application/pdf",
                        use_container_width=True,
                    )

        st.caption(f"Saved on disk: `{report_path}`")

    except Exception as e:
        st.error(f"Research failed: {e}")
        st.code(traceback.format_exc())

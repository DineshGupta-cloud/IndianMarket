"""
IndianMarket – Streamlit Dashboard
Run with:  streamlit run streamlit_app.py
"""

import streamlit as st
from pathlib import Path
from datetime import datetime
import traceback

from agents.orchestrator import ResearchOrchestrator

st.set_page_config(
    page_title="IndianMarket Research",
    page_icon="🇮🇳",
    layout="wide",
)

st.title("🇮🇳 IndianMarket – Multi-Agent Equity Research")
st.caption("NSE/BSE focused research powered by specialized agents")

with st.sidebar:
    st.header("Settings")
    ticker = st.text_input("NSE Ticker", value="RELIANCE", help="e.g. RELIANCE, TCS, HDFCBANK, INFY").upper().strip()
    period = st.selectbox("History Period", ["6mo", "1y", "2y", "5y"], index=1)
    export_pdf = st.checkbox("Also export PDF", value=True)
    run_btn = st.button("🚀 Run Research", type="primary", use_container_width=True)

    st.markdown("---")
    st.markdown("**Agents**")
    st.markdown("""
    - Market Data
    - Fundamentals
    - Technicals
    - News
    - FII / DII Flows
    - Sentiment (placeholder)
    - Macro & Risk
    - Synthesis
    """)

if run_btn and ticker:
    with st.spinner(f"Running multi-agent research on **{ticker}** (parallel)..."):
        try:
            orch = ResearchOrchestrator(ticker=ticker, period=period)
            report_path = orch.run(export_pdf=export_pdf)

            synthesis = orch.results.get("synthesis", {})
            market = orch.results.get("market_data", {})
            fii = orch.results.get("fii_dii", {})
            tech = orch.results.get("technical", {})
            funda = orch.results.get("fundamental", {})

            # Header metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Company", synthesis.get("company", ticker))
            col2.metric("Price", f"₹{market.get('current_price', 'N/A')}", f"{market.get('day_change_pct', 0):+.2f}%")
            col3.metric("Bias", synthesis.get("bias", "N/A"))
            col4.metric("RSI (14)", tech.get("rsi_14", "N/A"), tech.get("rsi_signal", ""))

            st.markdown("---")

            # FII/DII highlight
            if not fii.get("error"):
                st.subheader("Institutional Flows (Market-wide)")
                fc1, fc2, fc3 = st.columns(3)
                latest = fii.get("latest", {})
                fc1.metric("FII Net (₹ Cr)", latest.get("fii_net", "N/A"))
                fc2.metric("DII Net (₹ Cr)", latest.get("dii_net", "N/A"))
                fc3.write(f"**{fii.get('flow_bias', '')}**")
                st.caption(f"As of {fii.get('as_of', 'N/A')} • Source: NSE via public feed")

            # Full report
            st.subheader("Full Research Report")
            st.markdown(synthesis.get("report_markdown", "_No report generated_"))

            # Downloads
            st.download_button(
                label="📄 Download Markdown",
                data=synthesis.get("report_markdown", ""),
                file_name=report_path.name,
                mime="text/markdown",
            )

            pdf_path = report_path.with_suffix(".pdf")
            if pdf_path.exists():
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label="📄 Download PDF",
                        data=f,
                        file_name=pdf_path.name,
                        mime="application/pdf",
                    )

        except Exception as e:
            st.error(f"Research failed: {e}")
            st.code(traceback.format_exc())
else:
    st.info("Enter an NSE ticker in the sidebar and click **Run Research** to generate a full multi-agent report.")
    st.markdown("""
    ### Example tickers
    `RELIANCE` · `TCS` · `HDFCBANK` · `INFY` · `ICICIBANK` · `SBIN` · `BHARTIARTL` · `ITC` · `LT` · `HINDUNILVR`
    """)

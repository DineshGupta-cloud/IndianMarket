"""
IndianMarket – Single App for Everything
----------------------------------------
One Streamlit dashboard for:
  - Single stock research
  - Portfolio (multi-ticker) research
  - Optional LLM synthesis (API key)
  - Markdown + PDF reports

Run:
    streamlit run app.py
"""

import streamlit as st
import traceback

from agents.orchestrator import ResearchOrchestrator
from utils.llm_client import is_llm_available, resolve_llm_config

st.set_page_config(
    page_title="IndianMarket",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded",
)

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

    st.markdown("---")
    st.markdown("**LLM Synthesis (optional)**")
    use_llm = st.checkbox("Enable LLM thesis", value=True)
    llm_key = st.text_input(
        "API key",
        type="password",
        help="Groq / OpenAI / any OpenAI-compatible key. Or set GROQ_API_KEY / OPENAI_API_KEY / LLM_API_KEY env var.",
        placeholder="Leave blank to use env var or rules only",
    )
    llm_provider = st.selectbox(
        "Provider preset",
        ["Groq (free tier)", "OpenAI", "Custom"],
        index=0,
    )
    if llm_provider == "Groq (free tier)":
        default_base = "https://api.groq.com/openai/v1"
        default_model = "llama-3.3-70b-versatile"
    elif llm_provider == "OpenAI":
        default_base = "https://api.openai.com/v1"
        default_model = "gpt-4o-mini"
    else:
        default_base = "https://api.groq.com/openai/v1"
        default_model = "llama-3.3-70b-versatile"

    llm_base = st.text_input("Base URL", value=default_base)
    llm_model = st.text_input("Model", value=default_model)

    env_ready = is_llm_available(api_key=llm_key or None)
    if use_llm and env_ready:
        st.success("LLM key detected — thesis will use LLM")
    elif use_llm:
        st.info("No API key — will use rule-based synthesis")
    else:
        st.info("LLM disabled — rule-based only")

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
    - Synthesis (+ optional LLM)
    """)
    st.markdown("---")
    st.caption("Educational use only • Not investment advice")

st.title("IndianMarket Research")
st.caption("One app for single-stock and portfolio analysis")

if not run_btn:
    st.info("Choose mode, enter ticker(s), optionally add an LLM API key, then click **Run Research**.")
    st.markdown("""
    ### LLM setup (optional)
    1. Get a free key from [Groq Console](https://console.groq.com/) (recommended)
    2. Paste it in the sidebar **or** set env var `GROQ_API_KEY`
    3. Enable **LLM thesis** and run

    Without a key, reports still work using rule-based synthesis.

    ### Quick examples
    | Mode | Input |
    |------|--------|
    | Single | `RELIANCE` |
    | Portfolio | `RELIANCE,TCS,INFY` |
    """)
    st.stop()

if not ticker_input:
    st.warning("Please enter at least one ticker.")
    st.stop()

parts = []
for p in ticker_input.replace(";", ",").split(","):
    p = p.strip()
    if p.endswith(".NS") or p.endswith(".BO"):
        p = p[:-3]
    if p:
        parts.append(p)
ticker_arg = ",".join(parts)

llm_config = {
    "enabled": use_llm,
    "api_key": llm_key or None,
    "base_url": llm_base or None,
    "model": llm_model or None,
}

with st.spinner(f"Running multi-agent research on **{ticker_arg}**..."):
    try:
        orch = ResearchOrchestrator(
            ticker=ticker_arg, period=period, llm_config=llm_config
        )
        report_path = orch.run(export_pdf=export_pdf)
        synthesis = orch.results.get("synthesis", {})

        if synthesis.get("portfolio_summaries"):
            st.success(f"Portfolio report ready for: {ticker_arg}")
            st.subheader("Portfolio Summary")
            st.dataframe(synthesis["portfolio_summaries"], use_container_width=True)
        else:
            market = orch.results.get("market_data", {})
            fii = orch.results.get("fii_dii", {})
            tech = orch.results.get("technical", {})
            sentiment = orch.results.get("sentiment", {})
            llm_out = synthesis.get("llm") or {}

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

            if llm_out and not llm_out.get("error") and llm_out.get("thesis"):
                st.subheader("LLM Thesis")
                st.write(llm_out["thesis"])
                m1, m2 = st.columns(2)
                m1.caption(f"Model: {llm_out.get('model', 'N/A')}")
                m2.caption(f"Confidence: {llm_out.get('confidence', 'N/A')}/10")

            st.markdown("---")

            if not fii.get("error"):
                st.subheader("Institutional Flows (market-wide)")
                f1, f2, f3 = st.columns(3)
                latest = fii.get("latest", {})
                f1.metric("FII Net (₹ Cr)", latest.get("fii_net", "N/A"))
                f2.metric("DII Net (₹ Cr)", latest.get("dii_net", "N/A"))
                f3.write(f"**{fii.get('flow_bias', '')}**")

            if sentiment.get("post_count", 0) > 0:
                st.subheader("Reddit Sentiment")
                s1, s2 = st.columns(2)
                s1.metric("Label", sentiment.get("sentiment_label", "N/A"))
                s2.metric("Posts analyzed", sentiment.get("post_count", 0))

        st.subheader("Full Research Report")
        st.markdown(synthesis.get("report_markdown", "_No report generated_"))

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

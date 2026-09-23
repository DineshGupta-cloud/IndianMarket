from typing import Any, Dict
from datetime import datetime
from .base import BaseAgent


class SynthesisAgent(BaseAgent):
    name = "SynthesisAgent"

    def run(self) -> Dict[str, Any]:
        data = self.context.get("all_results", {})
        llm_cfg = self.context.get("llm") or {}
        return self._build_report(data, llm_cfg)

    def _build_report(self, data: Dict[str, Any], llm_cfg: Dict[str, Any]) -> Dict[str, Any]:
        market = data.get("market_data", {})
        funda = data.get("fundamental", {})
        tech = data.get("technical", {})
        news = data.get("news", {})
        sentiment = data.get("sentiment", {})
        macro = data.get("macro_risk", {})
        fii_dii = data.get("fii_dii", {})
        screener = data.get("screener", {})

        company = (
            market.get("company_name")
            or screener.get("company_name")
            or self.ticker
        )
        price = market.get("current_price", "N/A")
        change = market.get("day_change_pct", 0) or 0

        bias = "Neutral"
        reasons = []

        if tech.get("trend_bias") == "Bullish":
            reasons.append("Technical trend is bullish")
        elif tech.get("trend_bias") == "Bearish":
            reasons.append("Technical trend is bearish")

        if tech.get("rsi_signal") == "Oversold":
            reasons.append("RSI indicates oversold conditions")
        elif tech.get("rsi_signal") == "Overbought":
            reasons.append("RSI indicates overbought conditions")

        div = tech.get("rsi_divergence") or {}
        for sig in div.get("signals") or []:
            reasons.append(sig)

        flags = funda.get("flags", [])
        if "Strong ROE (>15%)" in flags:
            reasons.append("Strong return on equity")
        if "High trailing P/E" in flags:
            reasons.append("Elevated valuation (high P/E)")

        flow_bias = fii_dii.get("flow_bias", "")
        if "Both FII & DII buying" in flow_bias:
            reasons.append("Institutional flows supportive (FII+DII buying)")
        elif "DII absorbing" in flow_bias:
            reasons.append("DII absorbing FII selling (domestic support)")

        sent_label = sentiment.get("sentiment_label", "")
        if "Positive" in sent_label:
            reasons.append(f"Reddit sentiment: {sent_label}")
        elif "Negative" in sent_label:
            reasons.append(f"Reddit sentiment: {sent_label}")

        if tech.get("trend_bias") == "Bullish" and "Strong ROE (>15%)" in flags:
            bias = "Constructive / Mildly Bullish"
        elif tech.get("trend_bias") == "Bearish" or "High trailing P/E" in flags:
            bias = "Cautious"

        llm_result = None
        use_llm = llm_cfg.get("enabled", True)
        if use_llm:
            try:
                from utils.llm_client import generate_llm_thesis, is_llm_available

                if is_llm_available(api_key=llm_cfg.get("api_key")):
                    self.log("Calling LLM for synthesis thesis...")
                    llm_result = generate_llm_thesis(
                        ticker=self.ticker,
                        company=company,
                        context=data,
                        api_key=llm_cfg.get("api_key"),
                        base_url=llm_cfg.get("base_url"),
                        model=llm_cfg.get("model"),
                    )
                    if llm_result and not llm_result.get("error") and llm_result.get("bias"):
                        bias = llm_result["bias"]
                        if llm_result.get("thesis"):
                            reasons = [llm_result["thesis"]] + reasons[:4]
                    elif llm_result and llm_result.get("error"):
                        self.log(f"LLM error (using rules): {llm_result['error']}")
            except Exception as e:
                self.log(f"LLM unavailable (using rules): {e}")
                llm_result = {"error": str(e)}

        report_md = self._render_markdown(
            company=company,
            price=price,
            change=change,
            bias=bias,
            reasons=reasons,
            market=market,
            funda=funda,
            tech=tech,
            news=news,
            sentiment=sentiment,
            macro=macro,
            fii_dii=fii_dii,
            screener=screener,
            llm_result=llm_result,
        )

        return {
            "ticker": self.ticker,
            "company": company,
            "bias": bias,
            "reasons": reasons,
            "llm": llm_result,
            "report_markdown": report_md,
            "generated_at": datetime.now().isoformat(),
            "raw_results": data,
        }

    def _render_markdown(self, **kwargs) -> str:
        company = kwargs["company"]
        price = kwargs["price"]
        change = kwargs["change"]
        bias = kwargs["bias"]
        reasons = kwargs["reasons"]
        market = kwargs["market"]
        funda = kwargs["funda"]
        tech = kwargs["tech"]
        news = kwargs["news"]
        sentiment = kwargs["sentiment"]
        macro = kwargs["macro"]
        fii_dii = kwargs["fii_dii"]
        screener = kwargs["screener"]
        llm_result = kwargs.get("llm_result")

        lines = []
        lines.append(f"# Equity Research Report: {company} ({self.ticker})")
        lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M IST')}  ")
        lines.append(f"**Current Price:** ₹{price} ({change:+.2f}%)  ")
        source = "LLM + rules" if (llm_result and not llm_result.get("error") and llm_result.get("thesis")) else "rules"
        lines.append(f"**Overall Bias ({source}):** {bias}\n")
        lines.append("---\n")

        if llm_result and not llm_result.get("error") and llm_result.get("thesis"):
            lines.append("## 1. LLM Investment Thesis")
            lines.append(llm_result["thesis"])
            lines.append("")
            for key, title in [("bull_case", "Bull case"), ("bear_case", "Bear case"), ("key_risks", "Key risks"), ("what_to_watch", "What to watch")]:
                if llm_result.get(key):
                    lines.append(f"**{title}**")
                    for b in llm_result[key]:
                        lines.append(f"- {b}")
                    lines.append("")
            lines.append(f"_Confidence: {llm_result.get('confidence')}/10 · Model: {llm_result.get('model', '')}_\n")
            lines.append("## 2. Rule-based Highlights")
        else:
            lines.append("## 1. Executive Summary")
            if llm_result and llm_result.get("error"):
                lines.append(f"_LLM synthesis skipped: {llm_result['error']}_\n")

        if reasons:
            lines.append("Key points:")
            for r in reasons:
                if llm_result and r == llm_result.get("thesis"):
                    continue
                lines.append(f"- {r}")
        else:
            lines.append("- Mixed signals; further detailed analysis recommended.")
        lines.append("")

        lines.append("## Market Snapshot")
        lines.append(f"- **Sector / Industry:** {market.get('sector', 'N/A')} / {market.get('industry', 'N/A')}")
        lines.append(f"- **Market Cap:** {self._fmt_cr(market.get('market_cap'))}")
        lines.append(f"- **52-Week Range:** ₹{market.get('fifty_two_week_low', 'N/A')} – ₹{market.get('fifty_two_week_high', 'N/A')}")
        vol = market.get("volume")
        lines.append(f"- **Volume (latest):** {vol:,}" if isinstance(vol, int) else "- **Volume:** N/A")
        rets = market.get("returns", {})
        if rets:
            lines.append("- **Performance:**")
            for k, v in rets.items():
                lines.append(f"  - {k}: {v:+.2f}%")
        lines.append("")

        lines.append("## Institutional Flows (FII / DII)")
        if fii_dii.get("error"):
            lines.append(f"_Could not fetch flows: {fii_dii.get('error')}_")
        else:
            latest = fii_dii.get("latest", {})
            lines.append(f"**As of:** {fii_dii.get('as_of', 'N/A')}  ")
            lines.append(f"**Flow Bias:** {fii_dii.get('flow_bias', 'N/A')}\n")
            lines.append("| Participant | Buy (₹ Cr) | Sell (₹ Cr) | Net (₹ Cr) |")
            lines.append("|-------------|------------|-------------|------------|")
            lines.append(f"| FII | {latest.get('fii_buy', 'N/A')} | {latest.get('fii_sell', 'N/A')} | {latest.get('fii_net', 'N/A')} |")
            lines.append(f"| DII | {latest.get('dii_buy', 'N/A')} | {latest.get('dii_sell', 'N/A')} | {latest.get('dii_net', 'N/A')} |")
            lines.append("")

        lines.append("## Fundamental Snapshot")
        val = funda.get("valuation", {})
        prof = funda.get("profitability", {})
        health = funda.get("financial_health", {})
        lines.append(f"- Trailing P/E: {val.get('trailing_pe', 'N/A')} | Forward P/E: {val.get('forward_pe', 'N/A')}")
        lines.append(f"- ROE: {self._pct(prof.get('return_on_equity'))} | Debt/Equity: {health.get('debt_to_equity', 'N/A')}")
        if funda.get("flags"):
            lines.append("**Flags:** " + ", ".join(funda["flags"]))
        if screener and not screener.get("error"):
            if screener.get("pros"):
                lines.append("**Screener pros:** " + "; ".join(screener["pros"][:4]))
            if screener.get("cons"):
                lines.append("**Screener cons:** " + "; ".join(screener["cons"][:4]))
        lines.append("")

        lines.append("## Technical Analysis")
        lines.append(f"- **Trend Bias:** {tech.get('trend_bias', 'N/A')}")
        lines.append(f"- **RSI (14):** {tech.get('rsi_14', 'N/A')} ({tech.get('rsi_signal', '')})")
        lines.append(f"- **SMA 20 / 50 / 200:** {tech.get('sma_20')} / {tech.get('sma_50')} / {tech.get('sma_200')}")
        lines.append(f"- **MACD:** {tech.get('macd')} | Signal: {tech.get('macd_signal')}")
        lines.append(f"- **Support / Resistance (60d):** ₹{tech.get('support_60d')} / ₹{tech.get('resistance_60d')}")

        div = tech.get("rsi_divergence") or {}
        lines.append("- **RSI divergence:**")
        if div.get("signals"):
            for s in div["signals"]:
                lines.append(f"  - {s}")
        else:
            lines.append("  - None detected on recent swings")
        lines.append("")

        lines.append("## Social Sentiment (Reddit)")
        lines.append(f"- **Label:** {sentiment.get('sentiment_label', 'N/A')} | Posts: {sentiment.get('post_count', 0)}")
        lines.append("")

        lines.append("## Recent News")
        items = news.get("items", [])
        if items:
            for i, item in enumerate(items[:5], 1):
                lines.append(f"{i}. **{item.get('title')}** ({item.get('publisher')})")
        else:
            lines.append("_No recent news items retrieved._")
        lines.append("")

        lines.append("---")
        lines.append("## Disclaimer")
        lines.append(
            "Educational / informational only. Not investment advice. "
            "Consult a SEBI-registered advisor before investing."
        )
        lines.append("\n*Powered by IndianMarket multi-agent system*")
        return "\n".join(lines)

    def _fmt_cr(self, value):
        if not value or not isinstance(value, (int, float)):
            return "N/A"
        cr = value / 1e7
        if cr >= 100000:
            return f"₹{cr/100000:.2f} Lakh Cr"
        return f"₹{cr:,.0f} Cr"

    def _pct(self, value):
        if value is None:
            return "N/A"
        try:
            return f"{float(value)*100:.2f}%"
        except Exception:
            return str(value)

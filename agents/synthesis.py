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

        # Prefer technical action when available
        rec = tech.get("recommendation") or {}
        tech_action = rec.get("action") or tech.get("action") or "HOLD"

        bias = tech_action  # surface BUY/SELL/HOLD as primary label when from technicals
        reasons = []

        if rec.get("summary"):
            reasons.append(rec["summary"])
        for r in (rec.get("reasons") or [])[:6]:
            reasons.append(r)

        if tech.get("trend_bias") == "Bullish" and "trend" not in " ".join(reasons).lower():
            reasons.append("Technical trend is bullish")
        elif tech.get("trend_bias") == "Bearish":
            reasons.append("Technical trend is bearish")

        flags = funda.get("flags", [])
        if "Strong ROE (>15%)" in flags:
            reasons.append("Strong return on equity (fundamental)")
        if "High trailing P/E" in flags:
            reasons.append("Elevated valuation (high P/E)")

        flow_bias = fii_dii.get("flow_bias", "")
        if "Both FII & DII buying" in flow_bias:
            reasons.append("Institutional flows supportive (FII+DII buying)")
        elif "DII absorbing" in flow_bias:
            reasons.append("DII absorbing FII selling (domestic support)")

        sent_label = sentiment.get("sentiment_label", "")
        if "Positive" in sent_label or "Negative" in sent_label:
            reasons.append(f"Reddit sentiment: {sent_label}")

        # Overall label: technical action, tempered by extreme fundamental flags
        overall = tech_action
        if tech_action == "BUY" and "High trailing P/E" in flags:
            overall = "HOLD"
            reasons.insert(0, "Technical BUY tempered to HOLD due to rich valuation")
        if tech_action == "SELL" and "Strong ROE (>15%)" in flags:
            reasons.append("Quality fundamentals still constructive despite technical SELL")

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
                    if llm_result and not llm_result.get("error") and llm_result.get("thesis"):
                        reasons = [llm_result["thesis"]] + reasons[:5]
            except Exception as e:
                self.log(f"LLM unavailable (using rules): {e}")
                llm_result = {"error": str(e)}

        report_md = self._render_markdown(
            company=company,
            price=price,
            change=change,
            bias=overall,
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
            rec=rec,
        )

        return {
            "ticker": self.ticker,
            "company": company,
            "bias": overall,
            "action": overall,
            "technical_action": tech_action,
            "technical_score": rec.get("score"),
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
        rec = kwargs.get("rec") or {}

        lines = []
        lines.append(f"# Equity Research Report: {company} ({self.ticker})")
        lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M IST')}  ")
        lines.append(f"**Current Price:** ₹{price} ({change:+.2f}%)  ")
        lines.append(f"**Recommendation: {bias}**  ")
        if rec:
            lines.append(
                f"**Technical score:** {rec.get('score', 'N/A'):+d} · "
                f"Confidence: {rec.get('confidence', 'N/A')}\n"
            )
        lines.append("---\n")

        lines.append("## Technical recommendation (BUY / SELL / HOLD)")
        lines.append(f"- **Action:** {rec.get('action', bias)}")
        lines.append(f"- **Score:** {rec.get('score', 'N/A')}")
        lines.append(f"- **Confidence:** {rec.get('confidence', 'N/A')}")
        if rec.get("reasons"):
            lines.append("- **Why:**")
            for r in rec["reasons"]:
                lines.append(f"  - {r}")
        lines.append(f"\n_{rec.get('disclaimer', 'Educational only. Not investment advice.')}_\n")

        if llm_result and not llm_result.get("error") and llm_result.get("thesis"):
            lines.append("## LLM thesis")
            lines.append(llm_result["thesis"])
            lines.append("")

        lines.append("## Key points")
        for r in reasons[:10]:
            if llm_result and r == llm_result.get("thesis"):
                continue
            lines.append(f"- {r}")
        lines.append("")

        lines.append("## Market Snapshot")
        lines.append(f"- **Sector / Industry:** {market.get('sector', 'N/A')} / {market.get('industry', 'N/A')}")
        lines.append(f"- **Market Cap:** {self._fmt_cr(market.get('market_cap'))}")
        lines.append(f"- **52-Week Range:** ₹{market.get('fifty_two_week_low', 'N/A')} – ₹{market.get('fifty_two_week_high', 'N/A')}")
        lines.append("")

        lines.append("## Technical detail")
        lines.append(f"- Trend: {tech.get('trend_bias')} | RSI: {tech.get('rsi_14')} ({tech.get('rsi_signal')})")
        lines.append(f"- SMA 20/50/200: {tech.get('sma_20')} / {tech.get('sma_50')} / {tech.get('sma_200')}")
        lines.append(f"- MACD hist: {tech.get('macd_hist')} | S/R: ₹{tech.get('support_60d')} / ₹{tech.get('resistance_60d')}")
        div = tech.get("rsi_divergence") or {}
        if div.get("signals"):
            lines.append("- Divergence: " + "; ".join(div["signals"]))
        else:
            lines.append("- Divergence: none on recent swings")
        lines.append("")

        lines.append("## Fundamentals (brief)")
        val = funda.get("valuation", {})
        prof = funda.get("profitability", {})
        lines.append(f"- P/E: {val.get('trailing_pe', 'N/A')} | ROE: {self._pct(prof.get('return_on_equity'))}")
        if funda.get("flags"):
            lines.append("- Flags: " + ", ".join(funda["flags"]))
        lines.append("")

        lines.append("## FII/DII")
        if not fii_dii.get("error"):
            lines.append(f"- {fii_dii.get('flow_bias', 'N/A')} (as of {fii_dii.get('as_of')})")
        lines.append("")

        lines.append("## News (top)")
        for i, item in enumerate((news.get("items") or [])[:4], 1):
            lines.append(f"{i}. {item.get('title')}")
        lines.append("")

        lines.append("---")
        lines.append(
            "**Disclaimer:** Automated technical + multi-agent research for education only. "
            "**Not investment advice.** Do your own due diligence; consult a SEBI-registered advisor."
        )
        return "\n".join(lines)

    def _fmt_cr(self, value):
        if not value or not isinstance(value, (int, float)):
            return "N/A"
        cr = value / 1e7
        return f"₹{cr/100000:.2f} Lakh Cr" if cr >= 100000 else f"₹{cr:,.0f} Cr"

    def _pct(self, value):
        if value is None:
            return "N/A"
        try:
            return f"{float(value)*100:.2f}%"
        except Exception:
            return str(value)

from typing import Any, Dict
from datetime import datetime
from .base import BaseAgent


class SynthesisAgent(BaseAgent):
    name = "SynthesisAgent"

    def run(self) -> Dict[str, Any]:
        data = self.context.get("all_results", {})
        return self._build_report(data)

    def _build_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        market = data.get("market_data", {})
        funda = data.get("fundamental", {})
        tech = data.get("technical", {})
        news = data.get("news", {})
        sentiment = data.get("sentiment", {})
        macro = data.get("macro_risk", {})
        fii_dii = data.get("fii_dii", {})

        company = market.get("company_name", self.ticker)
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

        if tech.get("trend_bias") == "Bullish" and "Strong ROE (>15%)" in flags:
            bias = "Constructive / Mildly Bullish"
        elif tech.get("trend_bias") == "Bearish" or "High trailing P/E" in flags:
            bias = "Cautious"

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
        )

        return {
            "ticker": self.ticker,
            "company": company,
            "bias": bias,
            "reasons": reasons,
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

        lines = []
        lines.append(f"# Equity Research Report: {company} ({self.ticker})")
        lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M IST')}  ")
        lines.append(f"**Current Price:** ₹{price} ({change:+.2f}%)  ")
        lines.append(f"**Overall Bias (v1 rules):** {bias}\n")
        lines.append("---\n")

        lines.append("## 1. Executive Summary")
        if reasons:
            lines.append("Key points:")
            for r in reasons:
                lines.append(f"- {r}")
        else:
            lines.append("- Mixed signals; further detailed analysis recommended.")
        lines.append("")

        lines.append("## 2. Market Snapshot")
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

        # FII / DII section
        lines.append("## 3. Institutional Flows (FII / DII)")
        if fii_dii.get("error"):
            lines.append(f"_Could not fetch flows: {fii_dii.get('error')}_")
        else:
            latest = fii_dii.get("latest", {})
            lines.append(f"**As of:** {fii_dii.get('as_of', 'N/A')}  ")
            lines.append(f"**Flow Bias:** {fii_dii.get('flow_bias', 'N/A')}\n")
            lines.append("| Participant | Buy (₹ Cr) | Sell (₹ Cr) | Net (₹ Cr) |")
            lines.append("|-------------|------------|-------------|------------|")
            lines.append(
                f"| FII | {latest.get('fii_buy', 'N/A')} | {latest.get('fii_sell', 'N/A')} | {latest.get('fii_net', 'N/A')} |"
            )
            lines.append(
                f"| DII | {latest.get('dii_buy', 'N/A')} | {latest.get('dii_sell', 'N/A')} | {latest.get('dii_net', 'N/A')} |"
            )
            lines.append("")
            recent = fii_dii.get("recent_5_sessions", [])
            if recent:
                lines.append("**Recent 5 sessions (Net ₹ Cr):**")
                for row in recent:
                    lines.append(
                        f"- {row.get('date')}: FII {row.get('fii_net')} | DII {row.get('dii_net')}"
                    )
            lines.append(f"\n_{fii_dii.get('note', '')}_\n")

        lines.append("## 4. Fundamental Snapshot")
        val = funda.get("valuation", {})
        prof = funda.get("profitability", {})
        health = funda.get("financial_health", {})
        lines.append("### Valuation")
        lines.append(f"- Trailing P/E: {val.get('trailing_pe', 'N/A')}")
        lines.append(f"- Forward P/E: {val.get('forward_pe', 'N/A')}")
        lines.append(f"- Price to Book: {val.get('price_to_book', 'N/A')}")
        lines.append(f"- EV/EBITDA: {val.get('enterprise_to_ebitda', 'N/A')}")
        lines.append("\n### Profitability & Quality")
        lines.append(f"- ROE: {self._pct(prof.get('return_on_equity'))}")
        lines.append(f"- ROA: {self._pct(prof.get('return_on_assets'))}")
        lines.append(f"- Operating Margin: {self._pct(prof.get('operating_margins'))}")
        lines.append(f"- Profit Margin: {self._pct(prof.get('profit_margins'))}")
        lines.append("\n### Balance Sheet Health")
        lines.append(f"- Debt to Equity: {health.get('debt_to_equity', 'N/A')}")
        lines.append(f"- Current Ratio: {health.get('current_ratio', 'N/A')}")
        if funda.get("flags"):
            lines.append("\n**Flags:** " + ", ".join(funda["flags"]))
        if funda.get("summary"):
            lines.append(f"\n**Business Summary:**\n{funda['summary']}\n")
        lines.append("")

        lines.append("## 5. Technical Analysis")
        lines.append(f"- **Trend Bias:** {tech.get('trend_bias', 'N/A')}")
        lines.append(f"- **RSI (14):** {tech.get('rsi_14', 'N/A')} ({tech.get('rsi_signal', '')})")
        lines.append(f"- **SMA 20 / 50 / 200:** {tech.get('sma_20')} / {tech.get('sma_50')} / {tech.get('sma_200')}")
        lines.append(f"- **MACD:** {tech.get('macd')} | Signal: {tech.get('macd_signal')} | Hist: {tech.get('macd_hist')}")
        lines.append(f"- **Support (60d):** ₹{tech.get('support_60d')} | **Resistance (60d):** ₹{tech.get('resistance_60d')}")
        lines.append(f"- **Price vs SMA50:** {tech.get('price_vs_sma50')}")
        lines.append("")

        lines.append("## 6. Recent News")
        items = news.get("items", [])
        if items:
            for i, item in enumerate(items[:6], 1):
                lines.append(f"{i}. **{item.get('title')}** ({item.get('publisher')})")
                if item.get("summary"):
                    lines.append(f"   {item['summary']}")
                if item.get("link"):
                    lines.append(f"   [Link]({item['link']})")
                lines.append("")
        else:
            lines.append("_No recent news items retrieved._\n")

        lines.append("## 7. Sentiment & Macro Context")
        lines.append(f"*{sentiment.get('note', '')}*\n")
        lines.append("**Key India Macro Factors to Monitor:**")
        for f in macro.get("india_macro_factors", []):
            lines.append(f"- {f}")
        lines.append("\n**Risk Checklist:**")
        for r in macro.get("risk_checklist", []):
            lines.append(f"- {r}")
        lines.append("")

        lines.append("---")
        lines.append("## Disclaimer")
        lines.append(
            "This report is generated by an automated multi-agent research system for educational "
            "and informational purposes only. It does **not** constitute investment advice, "
            "a recommendation, or an offer to buy/sell any securities. Always conduct your own "
            "due diligence and consult a SEBI-registered advisor before making investment decisions."
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

from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from .market_data import MarketDataAgent
from .fundamental import FundamentalAgent
from .technical import TechnicalAgent
from .news import NewsAgent
from .sentiment import SentimentAgent
from .macro_risk import MacroRiskAgent
from .fii_dii import FIIDIIAgent
from .screener import ScreenerAgent
from .synthesis import SynthesisAgent


class ResearchOrchestrator:
    """
    Coordinates all agents in a LangGraph-style parallel fan-out,
    then synthesizes the final research report.
    Supports single ticker or multi-ticker portfolio mode.
    """

    def __init__(self, ticker: Union[str, List[str]], period: str = "1y"):
        if isinstance(ticker, str):
            # Allow comma-separated string
            parts = [t.strip().upper() for t in ticker.replace(";", ",").split(",") if t.strip()]
            self.tickers = parts
        else:
            self.tickers = [t.upper().strip() for t in ticker]

        self.ticker = self.tickers[0]  # primary for single-stock compatibility
        self.period = period
        self.results: Dict[str, Any] = {}
        self.portfolio_results: Dict[str, Dict[str, Any]] = {}

    def run(self, output_path: Optional[str] = None, export_pdf: bool = False) -> Path:
        if len(self.tickers) == 1:
            return self._run_single(self.tickers[0], output_path, export_pdf)
        return self._run_portfolio(output_path, export_pdf)

    def _run_single(self, ticker: str, output_path: Optional[str], export_pdf: bool) -> Path:
        print(f"🤖 Launching research agents for {ticker} (parallel)...\n")
        self.results = self._execute_agents(ticker)

        if self.results.get("market_data", {}).get("error"):
            print(f"❌ Failed to fetch market data: {self.results['market_data']['error']}")
            raise RuntimeError("Market data unavailable")

        print("\n📝 Synthesizing research report...")
        synth_agent = SynthesisAgent(ticker, all_results=self.results)
        synthesis = synth_agent.run()
        self.results["synthesis"] = synthesis

        return self._save_report(ticker, synthesis, output_path, export_pdf)

    def _run_portfolio(self, output_path: Optional[str], export_pdf: bool) -> Path:
        print(f"💼 Portfolio mode: {', '.join(self.tickers)}\n")
        summaries = []

        for t in self.tickers:
            print(f"\n--- Analyzing {t} ---")
            try:
                res = self._execute_agents(t)
                synth = SynthesisAgent(t, all_results=res).run()
                res["synthesis"] = synth
                self.portfolio_results[t] = res
                summaries.append({
                    "ticker": t,
                    "company": synth.get("company", t),
                    "price": res.get("market_data", {}).get("current_price"),
                    "change_pct": res.get("market_data", {}).get("day_change_pct"),
                    "bias": synth.get("bias"),
                    "reasons": synth.get("reasons", []),
                })
            except Exception as e:
                print(f"  ⚠️  {t} failed: {e}")
                summaries.append({"ticker": t, "error": str(e)})

        # Combined portfolio markdown
        lines = [
            f"# Portfolio Research Report",
            f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M IST')}  ",
            f"**Tickers:** {', '.join(self.tickers)}\n",
            "---\n",
            "## Summary Table\n",
            "| Ticker | Company | Price | Day % | Bias |",
            "|--------|---------|-------|-------|------|",
        ]
        for s in summaries:
            if s.get("error"):
                lines.append(f"| {s['ticker']} | ERROR | - | - | {s['error'][:40]} |")
            else:
                lines.append(
                    f"| {s['ticker']} | {s.get('company', '')[:25]} | "
                    f"₹{s.get('price', 'N/A')} | {s.get('change_pct', 0):+.2f}% | {s.get('bias', '')} |"
                )

        lines.append("\n---\n")
        for t, res in self.portfolio_results.items():
            synth = res.get("synthesis", {})
            lines.append(f"\n# {synth.get('company', t)} ({t})\n")
            lines.append(synth.get("report_markdown", "_No report_"))
            lines.append("\n\n---\n")

        combined_md = "\n".join(lines)
        synthesis = {
            "ticker": "+".join(self.tickers),
            "company": "Portfolio",
            "bias": "See individual stocks",
            "reasons": [],
            "report_markdown": combined_md,
            "portfolio_summaries": summaries,
        }
        self.results = {"synthesis": synthesis, "portfolio": self.portfolio_results}

        return self._save_report("PORTFOLIO", synthesis, output_path, export_pdf)

    def _execute_agents(self, ticker: str) -> Dict[str, Any]:
        agent_nodes = {
            "market_data": MarketDataAgent(ticker, period=self.period),
            "fundamental": FundamentalAgent(ticker),
            "technical": TechnicalAgent(ticker, period=self.period),
            "news": NewsAgent(ticker),
            "sentiment": SentimentAgent(ticker),
            "macro_risk": MacroRiskAgent(ticker),
            "fii_dii": FIIDIIAgent(ticker),
            "screener": ScreenerAgent(ticker),
        }

        results: Dict[str, Any] = {}
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_name = {
                executor.submit(agent.run): name
                for name, agent in agent_nodes.items()
            }
            for future in as_completed(future_to_name):
                name = future_to_name[future]
                try:
                    results[name] = future.result()
                except Exception as e:
                    print(f"  ⚠️  Agent '{name}' failed: {e}")
                    results[name] = {"error": str(e)}
        return results

    def _save_report(
        self,
        label: str,
        synthesis: Dict[str, Any],
        output_path: Optional[str],
        export_pdf: bool,
    ) -> Path:
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        md_filename = f"{label}_{timestamp}.md"
        report_path = Path(output_path) if output_path else reports_dir / md_filename

        report_path.write_text(synthesis["report_markdown"], encoding="utf-8")

        if export_pdf:
            pdf_path = report_path.with_suffix(".pdf")
            try:
                from utils.pdf_export import markdown_to_pdf
                markdown_to_pdf(synthesis["report_markdown"], pdf_path)
                print(f"📄 PDF also saved to: {pdf_path}")
            except Exception as e:
                print(f"⚠️  PDF export failed: {e}")

        print(f"\n📊 Quick Summary for {synthesis.get('company', label)}")
        print(f"   Bias     : {synthesis.get('bias')}")
        if synthesis.get("reasons"):
            for r in synthesis["reasons"]:
                print(f"   • {r}")

        return report_path

from typing import Any, Dict, Optional
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
from .synthesis import SynthesisAgent


class ResearchOrchestrator:
    """
    Coordinates all agents in a LangGraph-style parallel fan-out,
    then synthesizes the final research report.
    """

    def __init__(self, ticker: str, period: str = "1y"):
        self.ticker = ticker.upper()
        self.period = period
        self.results: Dict[str, Any] = {}

    def run(self, output_path: Optional[str] = None, export_pdf: bool = False) -> Path:
        print("🤖 Launching research agents (parallel)...\n")

        # Define agent nodes (LangGraph-style)
        agent_nodes = {
            "market_data": MarketDataAgent(self.ticker, period=self.period),
            "fundamental": FundamentalAgent(self.ticker),
            "technical": TechnicalAgent(self.ticker, period=self.period),
            "news": NewsAgent(self.ticker),
            "sentiment": SentimentAgent(self.ticker),
            "macro_risk": MacroRiskAgent(self.ticker),
            "fii_dii": FIIDIIAgent(self.ticker),
        }

        # Parallel execution
        with ThreadPoolExecutor(max_workers=6) as executor:
            future_to_name = {
                executor.submit(agent.run): name
                for name, agent in agent_nodes.items()
            }

            for future in as_completed(future_to_name):
                name = future_to_name[future]
                try:
                    self.results[name] = future.result()
                except Exception as e:
                    print(f"  ⚠️  Agent '{name}' failed: {e}")
                    self.results[name] = {"error": str(e)}

        # Critical path check
        if self.results.get("market_data", {}).get("error"):
            print(f"❌ Failed to fetch market data: {self.results['market_data']['error']}")
            raise RuntimeError("Market data unavailable")

        # Synthesis node (runs after all others)
        print("\n📝 Synthesizing research report...")
        synth_agent = SynthesisAgent(self.ticker, all_results=self.results)
        synthesis = synth_agent.run()
        self.results["synthesis"] = synthesis

        # Save Markdown report
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        md_filename = f"{self.ticker}_{timestamp}.md"
        report_path = Path(output_path) if output_path else reports_dir / md_filename

        report_path.write_text(synthesis["report_markdown"], encoding="utf-8")

        # Optional PDF export
        if export_pdf:
            pdf_path = report_path.with_suffix(".pdf")
            try:
                from utils.pdf_export import markdown_to_pdf
                markdown_to_pdf(synthesis["report_markdown"], pdf_path)
                print(f"📄 PDF also saved to: {pdf_path}")
            except Exception as e:
                print(f"⚠️  PDF export failed: {e}")

        # Console summary
        print(f"\n📊 Quick Summary for {synthesis.get('company', self.ticker)}")
        print(f"   Bias     : {synthesis.get('bias')}")
        if synthesis.get("reasons"):
            for r in synthesis["reasons"]:
                print(f"   • {r}")

        return report_path

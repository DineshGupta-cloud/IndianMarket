from typing import Any, Dict, Optional
from pathlib import Path
from datetime import datetime

from .market_data import MarketDataAgent
from .fundamental import FundamentalAgent
from .technical import TechnicalAgent
from .news import NewsAgent
from .sentiment import SentimentAgent
from .macro_risk import MacroRiskAgent
from .synthesis import SynthesisAgent


class ResearchOrchestrator:
    """Coordinates all agents and produces the final research report."""

    def __init__(self, ticker: str, period: str = "1y"):
        self.ticker = ticker.upper()
        self.period = period
        self.results: Dict[str, Any] = {}

    def run(self, output_path: Optional[str] = None) -> Path:
        print("🤖 Launching research agents...\n")

        # 1. Market Data
        market_agent = MarketDataAgent(self.ticker, period=self.period)
        self.results["market_data"] = market_agent.run()

        if self.results["market_data"].get("error"):
            print(f"❌ Failed to fetch market data: {self.results['market_data']['error']}")
            raise RuntimeError("Market data unavailable")

        # 2. Fundamental
        funda_agent = FundamentalAgent(self.ticker)
        self.results["fundamental"] = funda_agent.run()

        # 3. Technical
        tech_agent = TechnicalAgent(self.ticker, period=self.period)
        self.results["technical"] = tech_agent.run()

        # 4. News
        news_agent = NewsAgent(self.ticker)
        self.results["news"] = news_agent.run()

        # 5. Sentiment (placeholder)
        sent_agent = SentimentAgent(self.ticker)
        self.results["sentiment"] = sent_agent.run()

        # 6. Macro / Risk
        macro_agent = MacroRiskAgent(self.ticker)
        self.results["macro_risk"] = macro_agent.run()

        # 7. Synthesis
        print("\n📝 Synthesizing research report...")
        synth_agent = SynthesisAgent(self.ticker, all_results=self.results)
        synthesis = synth_agent.run()
        self.results["synthesis"] = synthesis

        # Save report
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"{self.ticker}_{timestamp}.md"
        report_path = Path(output_path) if output_path else reports_dir / filename

        report_path.write_text(synthesis["report_markdown"], encoding="utf-8")

        # Also print a short summary to console
        print(f"\n📊 Quick Summary for {synthesis.get('company', self.ticker)}")
        print(f"   Bias     : {synthesis.get('bias')}")
        if synthesis.get("reasons"):
            for r in synthesis["reasons"]:
                print(f"   • {r}")

        return report_path

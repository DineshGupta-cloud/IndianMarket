from typing import Any, Dict
from .base import BaseAgent


class MacroRiskAgent(BaseAgent):
    """
    High-level macro and sector risk context for Indian equities.
    """
    name = "MacroRiskAgent"

    def run(self) -> Dict[str, Any]:
        self.log("Assessing macro & sector risks...")

        # Static high-level checklist that can later be made dynamic
        result = {
            "ticker": self.ticker,
            "india_macro_factors": [
                "RBI monetary policy & interest rate trajectory",
                "CPI inflation and food price trends",
                "INR vs USD movement and imported inflation",
                "Monsoon progress (agriculture & rural demand)",
                "Global crude oil prices (current account & inflation impact)",
                "FII/DII flow trends",
                "Union Budget / policy announcements",
                "Geopolitical risks affecting trade & energy",
            ],
            "sector_specific_note": (
                "Always cross-check the stock's sector exposure "
                "(Banking, IT, Energy, Pharma, Auto, FMCG, etc.) "
                "against current macro drivers."
            ),
            "risk_checklist": [
                "High promoter pledging?",
                "Regulatory or legal overhang?",
                "Heavy dependence on a single product/geography?",
                "Rising competitive intensity?",
                "Currency or commodity input cost risk?",
            ],
        }
        return result

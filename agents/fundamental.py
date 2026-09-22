from typing import Any, Dict
import yfinance as yf
from .base import BaseAgent


class FundamentalAgent(BaseAgent):
    name = "FundamentalAgent"

    def run(self) -> Dict[str, Any]:
        self.log(f"Analyzing fundamentals for {self.ns_ticker}...")

        try:
            stock = yf.Ticker(self.ns_ticker)
            info = stock.info or {}

            def safe(key, default=None):
                val = info.get(key, default)
                if isinstance(val, (int, float)) and val is not None:
                    return val
                return default

            result = {
                "ticker": self.ticker,
                "valuation": {
                    "trailing_pe": safe("trailingPE"),
                    "forward_pe": safe("forwardPE"),
                    "peg_ratio": safe("pegRatio"),
                    "price_to_book": safe("priceToBook"),
                    "enterprise_to_ebitda": safe("enterpriseToEbitda"),
                    "price_to_sales": safe("priceToSalesTrailing12Months"),
                },
                "profitability": {
                    "profit_margins": safe("profitMargins"),
                    "operating_margins": safe("operatingMargins"),
                    "return_on_equity": safe("returnOnEquity"),
                    "return_on_assets": safe("returnOnAssets"),
                    "gross_margins": safe("grossMargins"),
                },
                "growth": {
                    "revenue_growth": safe("revenueGrowth"),
                    "earnings_growth": safe("earningsGrowth"),
                    "earnings_quarterly_growth": safe("earningsQuarterlyGrowth"),
                },
                "financial_health": {
                    "total_cash": safe("totalCash"),
                    "total_debt": safe("totalDebt"),
                    "debt_to_equity": safe("debtToEquity"),
                    "current_ratio": safe("currentRatio"),
                    "quick_ratio": safe("quickRatio"),
                    "free_cashflow": safe("freeCashflow"),
                },
                "dividends": {
                    "dividend_yield": safe("dividendYield"),
                    "dividend_rate": safe("dividendRate"),
                    "payout_ratio": safe("payoutRatio"),
                    "ex_dividend_date": info.get("exDividendDate"),
                },
                "shareholding_hint": {
                    "held_percent_insiders": safe("heldPercentInsiders"),
                    "held_percent_institutions": safe("heldPercentInstitutions"),
                },
                "employees": safe("fullTimeEmployees"),
                "website": info.get("website"),
                "summary": info.get("longBusinessSummary", "")[:800] if info.get("longBusinessSummary") else None,
            }

            # Simple health flags
            flags = []
            pe = result["valuation"]["trailing_pe"]
            if pe and pe > 50:
                flags.append("High trailing P/E")
            if pe and pe < 10 and pe > 0:
                flags.append("Low trailing P/E (possible value)")
            de = result["financial_health"]["debt_to_equity"]
            if de and de > 100:
                flags.append("Elevated Debt/Equity")
            roe = result["profitability"]["return_on_equity"]
            if roe and roe > 0.15:
                flags.append("Strong ROE (>15%)")

            result["flags"] = flags
            self.log(f"Valuation & quality metrics extracted. Flags: {flags or 'None'}")
            return result

        except Exception as e:
            self.log(f"Error: {e}")
            return {"error": str(e), "ticker": self.ticker}

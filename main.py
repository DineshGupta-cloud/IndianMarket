#!/usr/bin/env python3
"""
IndianMarket - Multi-Agent Equity Research System
Entry point for running research on NSE/BSE stocks.
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

from agents.orchestrator import ResearchOrchestrator


def main():
    parser = argparse.ArgumentParser(
        description="IndianMarket - Multi-Agent Research for NSE/BSE stocks"
    )
    parser.add_argument(
        "ticker",
        type=str,
        help="NSE ticker symbol (e.g. RELIANCE, TCS, HDFCBANK)"
    )
    parser.add_argument(
        "--period",
        type=str,
        default="1y",
        help="Historical data period (default: 1y). Examples: 6mo, 1y, 2y, 5y"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Custom output path for the report (optional)"
    )

    args = parser.parse_args()

    ticker = args.ticker.upper().strip()
    if ticker.endswith(".NS") or ticker.endswith(".BO"):
        ticker = ticker[:-3]

    print(f"\n🇮🇳 IndianMarket Research System")
    print(f"{'='*50}")
    print(f"Analyzing: {ticker}")
    print(f"Period   : {args.period}")
    print(f"Time     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
    print(f"{'='*50}\n")

    orchestrator = ResearchOrchestrator(ticker=ticker, period=args.period)
    report_path = orchestrator.run(output_path=args.output)

    print(f"\n✅ Research complete!")
    print(f"📄 Report saved to: {report_path}")
    print(f"\nOpen the Markdown file to view the full analysis.\n")


if __name__ == "__main__":
    main()

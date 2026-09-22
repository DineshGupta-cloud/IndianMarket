#!/usr/bin/env python3
"""
IndianMarket - Multi-Agent Equity Research System
Entry point for running research on NSE/BSE stocks.
Supports single ticker or comma-separated portfolio.
"""

import argparse
from datetime import datetime

from agents.orchestrator import ResearchOrchestrator


def main():
    parser = argparse.ArgumentParser(
        description="IndianMarket - Multi-Agent Research for NSE/BSE stocks"
    )
    parser.add_argument(
        "ticker",
        type=str,
        help="NSE ticker(s). Single: RELIANCE  |  Portfolio: RELIANCE,TCS,INFY"
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
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Also export a PDF version of the report"
    )

    args = parser.parse_args()

    raw = args.ticker.upper().strip()
    # Clean .NS / .BO suffixes if user included them
    parts = []
    for p in raw.replace(";", ",").split(","):
        p = p.strip()
        if p.endswith(".NS") or p.endswith(".BO"):
            p = p[:-3]
        if p:
            parts.append(p)

    ticker_arg = ",".join(parts)

    print(f"\n🇮🇳 IndianMarket Research System")
    print(f"{'='*50}")
    print(f"Analyzing : {ticker_arg}")
    print(f"Period    : {args.period}")
    print(f"PDF export: {'Yes' if args.pdf else 'No'}")
    print(f"Time      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
    print(f"{'='*50}\n")

    orchestrator = ResearchOrchestrator(ticker=ticker_arg, period=args.period)
    report_path = orchestrator.run(output_path=args.output, export_pdf=args.pdf)

    print(f"\n✅ Research complete!")
    print(f"📄 Report saved to: {report_path}")
    print(f"\nOpen the Markdown file to view the full analysis.\n")


if __name__ == "__main__":
    main()

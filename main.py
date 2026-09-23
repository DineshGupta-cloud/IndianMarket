#!/usr/bin/env python3
"""
IndianMarket - Multi-Agent Equity Research System
CLI entry point. Optional LLM via env vars or flags.
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
        help="NSE ticker(s). Single: RELIANCE  |  Portfolio: RELIANCE,TCS,INFY",
    )
    parser.add_argument("--period", type=str, default="1y")
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--pdf", action="store_true")
    parser.add_argument(
        "--llm-key",
        type=str,
        default=None,
        help="Optional LLM API key (or set GROQ_API_KEY / OPENAI_API_KEY / LLM_API_KEY)",
    )
    parser.add_argument(
        "--llm-base",
        type=str,
        default=None,
        help="OpenAI-compatible base URL (default: Groq)",
    )
    parser.add_argument(
        "--llm-model",
        type=str,
        default=None,
        help="Model name (default: llama-3.3-70b-versatile)",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable LLM synthesis even if a key is available",
    )

    args = parser.parse_args()

    raw = args.ticker.upper().strip()
    parts = []
    for p in raw.replace(";", ",").split(","):
        p = p.strip()
        if p.endswith(".NS") or p.endswith(".BO"):
            p = p[:-3]
        if p:
            parts.append(p)
    ticker_arg = ",".join(parts)

    llm_config = {
        "enabled": not args.no_llm,
        "api_key": args.llm_key,
        "base_url": args.llm_base,
        "model": args.llm_model,
    }

    print(f"\n🇮🇳 IndianMarket Research System")
    print(f"{'='*50}")
    print(f"Analyzing : {ticker_arg}")
    print(f"Period    : {args.period}")
    print(f"PDF export: {'Yes' if args.pdf else 'No'}")
    print(f"LLM       : {'Off' if args.no_llm else 'On (if key available)'}")
    print(f"Time      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
    print(f"{'='*50}\n")

    orchestrator = ResearchOrchestrator(
        ticker=ticker_arg, period=args.period, llm_config=llm_config
    )
    report_path = orchestrator.run(output_path=args.output, export_pdf=args.pdf)

    print(f"\n✅ Research complete!")
    print(f"📄 Report saved to: {report_path}\n")


if __name__ == "__main__":
    main()

"""
Optional LLM client for synthesis.
Works with any OpenAI-compatible API (Groq, OpenAI, Together, local, etc.).

Easiest setup: put this in a local .env file (never commit it):

  GROQ_API_KEY=gsk_your_key_here

If no API key is set, returns None and the system falls back to rule-based synthesis.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

import requests

from utils.env_loader import load_env

load_env()


def resolve_llm_config(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, Optional[str]]:
    load_env()
    key = (
        api_key
        or os.getenv("LLM_API_KEY")
        or os.getenv("GROQ_API_KEY")
        or os.getenv("OPENAI_API_KEY")
    )
    url = (
        base_url
        or os.getenv("LLM_BASE_URL")
        or "https://api.groq.com/openai/v1"
    )
    mdl = (
        model
        or os.getenv("LLM_MODEL")
        or "llama-3.3-70b-versatile"
    )
    return {"api_key": key, "base_url": url.rstrip("/"), "model": mdl}


def is_llm_available(api_key: Optional[str] = None) -> bool:
    return bool(resolve_llm_config(api_key=api_key)["api_key"])


def generate_llm_thesis(
    ticker: str,
    company: str,
    context: Dict[str, Any],
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    timeout: int = 60,
) -> Optional[Dict[str, Any]]:
    cfg = resolve_llm_config(api_key=api_key, base_url=base_url, model=model)
    if not cfg["api_key"]:
        return None

    slim = {
        "ticker": ticker,
        "company": company,
        "market_data": _slim(context.get("market_data")),
        "fundamental": _slim(context.get("fundamental")),
        "technical": _slim(context.get("technical")),
        "fii_dii": _slim(context.get("fii_dii")),
        "sentiment": _slim(context.get("sentiment")),
        "screener": _slim(context.get("screener")),
        "news_titles": [
            i.get("title") for i in (context.get("news") or {}).get("items", [])[:5]
        ],
    }

    system = (
        "You are an equity research analyst focused on Indian listed companies (NSE/BSE). "
        "Write a concise, balanced research thesis. Be factual. Do not give personalized "
        "investment advice. Flag uncertainty. Use INR context where relevant."
    )

    user = f"""Based on the following structured data for {company} ({ticker}), produce a JSON object with exactly these keys:

- "bias": one of ["Bullish", "Mildly Bullish", "Neutral", "Cautious", "Bearish"]
- "thesis": 3-6 sentence investment thesis (balanced, evidence-based)
- "bull_case": 2-4 short bullet points (as a JSON array of strings)
- "bear_case": 2-4 short bullet points (as a JSON array of strings)
- "key_risks": 2-4 short bullet points (as a JSON array of strings)
- "confidence": integer 1-10 (how confident you are given data quality/coverage)
- "what_to_watch": 2-3 near-term monitors (as a JSON array of strings)

Data:
{json.dumps(slim, default=str, indent=2)[:12000]}

Return ONLY valid JSON, no markdown fences."""

    try:
        resp = requests.post(
            f"{cfg['base_url']}/chat/completions",
            headers={
                "Authorization": f"Bearer {cfg['api_key']}",
                "Content-Type": "application/json",
            },
            json={
                "model": cfg["model"],
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.3,
                "max_tokens": 1200,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"].strip()

        if content.startswith("```"):
            content = content.strip("`")
            if content.startswith("json"):
                content = content[4:].strip()

        parsed = json.loads(content)
        return {
            "bias": parsed.get("bias", "Neutral"),
            "thesis": parsed.get("thesis", ""),
            "bull_case": parsed.get("bull_case", []),
            "bear_case": parsed.get("bear_case", []),
            "key_risks": parsed.get("key_risks", []),
            "confidence": parsed.get("confidence"),
            "what_to_watch": parsed.get("what_to_watch", []),
            "model": cfg["model"],
            "raw_text": content,
        }
    except Exception as e:
        return {"error": str(e)}


def _slim(obj: Any, max_depth: int = 3) -> Any:
    if obj is None:
        return None
    if max_depth <= 0:
        return str(obj)[:200]
    if isinstance(obj, dict):
        skip = {"history_tail", "raw_results", "report_markdown", "summary"}
        return {
            k: _slim(v, max_depth - 1)
            for k, v in obj.items()
            if k not in skip and not str(k).startswith("_")
        }
    if isinstance(obj, list):
        return [_slim(x, max_depth - 1) for x in obj[:8]]
    if isinstance(obj, (str, int, float, bool)):
        return obj
    return str(obj)[:300]

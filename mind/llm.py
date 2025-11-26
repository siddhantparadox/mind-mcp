"""LLM helpers for classification and summaries via OpenRouter."""
from __future__ import annotations

import json
from typing import Any, Dict, List

import httpx

from .config import OPENROUTER_API_KEY, OPENROUTER_BASE, MIND_LLM_MODEL


class LLMError(Exception):
    pass


async def call_llm(messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
    if not OPENROUTER_API_KEY:
        raise LLMError("OPENROUTER_API_KEY is not set")

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{OPENROUTER_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            json={
                "model": MIND_LLM_MODEL,
                "messages": messages,
                "temperature": temperature,
            },
        )
        resp.raise_for_status()

    data = resp.json()
    return data["choices"][0]["message"]["content"]


async def classify_memory(text: str) -> Dict[str, Any]:
    """Ask the LLM to propose type/tags/importance/summary."""
    system_prompt = (
        'You are a classifier for a personal long-term memory store called "Mind". '
        'Return ONLY JSON with keys: "type", "tags", "importance", "summary".'
        ' "type" must be one of ["fact", "preference", "task", "journal", "note"]. '
        'Tags must be a lowercase array. Importance is 0.0-1.0.'
    )
    user_prompt = f'TEXT:\\n\"\"\"{text}\"\"\"'

    raw = await call_llm(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LLMError("LLM did not return valid JSON") from exc

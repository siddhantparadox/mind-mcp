"""Embedding client for OpenRouter (OpenAI-compatible API)."""
from __future__ import annotations

from typing import List

import httpx

from .config import OPENROUTER_API_KEY, OPENROUTER_BASE, MIND_EMBEDDING_MODEL


class EmbeddingError(Exception):
    pass


async def embed_texts(texts: list[str]) -> List[List[float]]:
    """Return embeddings for provided texts using OpenRouter's /embeddings."""
    if not texts:
        return []
    if not OPENROUTER_API_KEY:
        raise EmbeddingError("OPENROUTER_API_KEY is not set")

    payload = {"model": MIND_EMBEDDING_MODEL, "input": texts}
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{OPENROUTER_BASE}/embeddings", json=payload, headers=headers)
        resp.raise_for_status()

    data = resp.json()
    return [item["embedding"] for item in data["data"]]

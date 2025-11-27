"""Core memory operations for Mind."""
from __future__ import annotations

import json
from typing import Any, Iterable, List, Optional
from uuid import uuid4

from .config import AI_ASSIST_ENABLED
from .db import db_conn, now_ts
from .embeddings import embed_texts
from .llm import LLMError, classify_memory


def _normalize_tags(tags: Optional[Iterable[str]]) -> Optional[str]:
    if tags is None:
        return None
    cleaned = [t.strip() for t in tags if t and t.strip()]
    if not cleaned:
        return None
    # Remove duplicates while preserving order.
    seen = dict.fromkeys(cleaned)
    return ",".join(seen.keys())


def _parse_tags(tags_text: Optional[str]) -> List[str]:
    if not tags_text:
        return []
    return [t for t in (part.strip() for part in tags_text.split(",")) if t]


def _row_to_memory(row: Any) -> Optional[dict]:
    if row is None:
        return None
    data = {
        "id": row["id"],
        "uuid": row["uuid"],
        "user_id": row["user_id"],
        "agent_id": row["agent_id"],
        "source": row["source"],
        "type": row["type"],
        "text": row["text"],
        "summary": row["summary"],
        "tags": _parse_tags(row["tags"]),
        "importance": row["importance"],
        "conversation_id": row["conversation_id"],
        "cluster_id": row["cluster_id"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "last_accessed_at": row["last_accessed_at"],
        "deleted_at": row["deleted_at"],
        "extra_json": json.loads(row["extra_json"]) if row["extra_json"] else None,
    }
    if "distance" in row.keys():
        data["distance"] = row["distance"]
    return data


async def create_memory(
    text: str,
    *,
    type_: Optional[str] = None,
    tags: Optional[List[str]] = None,
    importance: Optional[float] = None,
    user_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    source: str = "ui",
    conversation_id: Optional[str] = None,
    cluster_id: Optional[int] = None,
    extra_json: Optional[dict] = None,
    summary: Optional[str] = None,
    use_ai: Optional[bool] = None,
) -> dict:
    ai_enabled = AI_ASSIST_ENABLED if use_ai is None else use_ai
    ai_guess: dict[str, Any] = {}
    if ai_enabled and (type_ in (None, "auto") or tags is None or importance is None or summary is None):
        try:
            ai_guess = await classify_memory(text)
        except LLMError:
            ai_guess = {}

    resolved_type = type_ if type_ not in (None, "auto") else ai_guess.get("type")
    if not resolved_type:
        # Fallback so every memory has a reasonable type
        resolved_type = "note"

    resolved_tags = tags if tags is not None else ai_guess.get("tags")
    resolved_importance = importance if importance is not None else ai_guess.get("importance")
    resolved_summary = summary if summary is not None else ai_guess.get("summary")


    ts = now_ts()
    memory_uuid = str(uuid4())

    tags_text = _normalize_tags(resolved_tags)
    extra_json_text = json.dumps(extra_json) if extra_json else None

    embedding = (await embed_texts([text]))[0]

    with db_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO memories (
              uuid, user_id, agent_id, source, type, text, summary,
              tags, importance, conversation_id, cluster_id,
              created_at, updated_at, last_accessed_at, extra_json
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                memory_uuid,
                user_id,
                agent_id,
                source,
                resolved_type,
                text,
                resolved_summary,
                tags_text,
                resolved_importance,
                conversation_id,
                cluster_id,
                ts,
                ts,
                None,
                extra_json_text,
            ),
        )
        memory_id = cur.lastrowid
        conn.execute(
            "INSERT INTO vec_memories(rowid, embedding) VALUES (?, ?)",
            (memory_id, json.dumps(embedding)),
        )
        row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
        return _row_to_memory(row) or {}


async def get_memory(memory_id: int) -> Optional[dict]:
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
    return _row_to_memory(row)


async def search_memories(
    query: str,
    *,
    top_k: int = 20,
    type_filter: Optional[str] = None,
    tags: Optional[List[str]] = None,
    since: Optional[int] = None,
    until: Optional[int] = None,
) -> List[dict]:
    query_embedding = (await embed_texts([query]))[0]
    embedding_json = json.dumps(query_embedding)

    filters = ["m.deleted_at IS NULL"]
    params: list[Any] = [embedding_json, top_k]

    if type_filter:
        filters.append("m.type = ?")
        params.append(type_filter)

    if tags:
        for tag in tags:
            filters.append("m.tags LIKE ?")
            params.append(f"%{tag}%")

    if since is not None:
        filters.append("m.created_at >= ?")
        params.append(since)
    if until is not None:
        filters.append("m.created_at <= ?")
        params.append(until)

    where_clause = " AND ".join(filters)

    with db_conn() as conn:
        rows = conn.execute(
            f"""
            WITH matches AS (
              SELECT rowid, distance
              FROM vec_memories
              WHERE embedding MATCH ?
              ORDER BY distance
              LIMIT ?
            )
            SELECT m.*, matches.distance
            FROM matches
            JOIN memories m ON m.id = matches.rowid
            WHERE {where_clause}
            ORDER BY matches.distance
            """,
            params,
        ).fetchall()

    return [_row_to_memory(r) for r in rows if r]


async def update_memory(
    memory_id: int,
    *,
    text: Optional[str] = None,
    type_: Optional[str] = None,
    tags: Optional[List[str]] = None,
    importance: Optional[float] = None,
    summary: Optional[str] = None,
    cluster_id: Optional[int] = None,
) -> Optional[dict]:
    with db_conn() as conn:
        existing = conn.execute(
            "SELECT * FROM memories WHERE id = ? AND deleted_at IS NULL", (memory_id,)
        ).fetchone()
        if existing is None:
            return None

        new_text = text if text is not None else existing["text"]
        new_type = type_ if type_ is not None else existing["type"]
        new_tags_text = _normalize_tags(tags) if tags is not None else existing["tags"]
        new_importance = importance if importance is not None else existing["importance"]
        new_summary = summary if summary is not None else existing["summary"]
        new_cluster = cluster_id if cluster_id is not None else existing["cluster_id"]

        conn.execute(
            """
            UPDATE memories
            SET text = ?, type = ?, tags = ?, importance = ?, summary = ?, cluster_id = ?, updated_at = ?
            WHERE id = ?
            """,
            (new_text, new_type, new_tags_text, new_importance, new_summary, new_cluster, now_ts(), memory_id),
        )

        if text is not None:
            embedding = (await embed_texts([new_text]))[0]
            conn.execute(
                "INSERT OR REPLACE INTO vec_memories(rowid, embedding) VALUES (?, ?)",
                (memory_id, json.dumps(embedding)),
            )

        row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
        return _row_to_memory(row)


def delete_memory(memory_id: int) -> None:
    ts = now_ts()
    with db_conn() as conn:
        conn.execute("UPDATE memories SET deleted_at = ? WHERE id = ?", (ts, memory_id))
        conn.execute("DELETE FROM vec_memories WHERE rowid = ?", (memory_id,))

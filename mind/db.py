"""SQLite + sqlite-vec helpers and schema management."""
from __future__ import annotations

import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from .config import DB_PATH, SQLITE_VEC_PATH, MIND_EMBEDDING_DIM


def now_ts() -> int:
    return int(time.time())


def get_connection() -> sqlite3.Connection:
    """Open a SQLite connection with sqlite-vec loaded."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")

    conn.enable_load_extension(True)
    _load_sqlite_vec(conn)
    conn.enable_load_extension(False)
    return conn


def _load_sqlite_vec(conn: sqlite3.Connection) -> None:
    """Try known sqlite-vec library locations and entrypoints for resilience."""
    base = Path(SQLITE_VEC_PATH)
    home = Path.home()
    candidates = [
        base,
        base.with_suffix(""),
        base.with_suffix(".so"),
        base.with_suffix(".dylib"),
        Path("/usr/local/lib/vec0"),
        Path("/usr/local/lib/vec0.so"),
        Path("/usr/local/lib/sqlite-vec/vec0.so"),
        Path("/usr/lib/sqlite3/vec0.so"),
        home / ".local/lib/vec0.so",
        home / ".local/lib/sqlite-vec/vec0.so",
    ]

    tried = []
    last_err: Exception | None = None
    seen = set()

    for path in candidates:
        if path in seen:
            continue
        seen.add(path)
        if not path.exists():
            continue
        # Prefer direct API when available.
        try:
            conn.load_extension(str(path))
            return
        except TypeError:
            # Some builds only accept one arg; fall back to SQL function below.
            pass
        except sqlite3.OperationalError as exc:
            tried.append(f"{path} -> {exc}")
            last_err = exc

        # Try explicit entrypoints via SQL load_extension function.
        for entry in ("sqlite3_extension_init", "sqlite3_vec_init", "sqlite3_vec0_init", "sqlite3_sqlitevec_init"):
            try:
                conn.execute("SELECT load_extension(?, ?)", (str(path), entry))
                return
            except sqlite3.OperationalError as exc:
                tried.append(f"{path} ({entry}) -> {exc}")
                last_err = exc
                continue
    details = "; ".join(tried) if tried else "no candidate paths found"
    raise sqlite3.OperationalError(f"Could not load sqlite-vec. Tried: {details}") from last_err


@contextmanager
def db_conn():
    """Context manager for DB connections that commits on success."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def create_schema(conn: sqlite3.Connection) -> None:
    """Create all tables and virtual tables if they do not exist."""
    conn.executescript(
        f"""
        CREATE TABLE IF NOT EXISTS memories (
          id               INTEGER PRIMARY KEY AUTOINCREMENT,
          uuid             TEXT UNIQUE NOT NULL,
          user_id          TEXT,
          agent_id         TEXT,
          source           TEXT,
          type             TEXT,
          text             TEXT NOT NULL,
          summary          TEXT,
          tags             TEXT,
          importance       REAL,
          conversation_id  TEXT,
          cluster_id       INTEGER,
          created_at       INTEGER NOT NULL,
          updated_at       INTEGER NOT NULL,
          last_accessed_at INTEGER,
          extra_json       TEXT,
          deleted_at       INTEGER,
          FOREIGN KEY(cluster_id) REFERENCES clusters(id)
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS vec_memories
        USING vec0(
          embedding FLOAT[{MIND_EMBEDDING_DIM}]
        );

        CREATE TABLE IF NOT EXISTS clusters (
          id         INTEGER PRIMARY KEY AUTOINCREMENT,
          label      TEXT,
          summary    TEXT,
          created_at INTEGER NOT NULL,
          updated_at INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS memory_relations (
          id         INTEGER PRIMARY KEY AUTOINCREMENT,
          from_id    INTEGER NOT NULL,
          to_id      INTEGER NOT NULL,
          kind       TEXT NOT NULL,
          created_at INTEGER NOT NULL,
          FOREIGN KEY(from_id) REFERENCES memories(id),
          FOREIGN KEY(to_id) REFERENCES memories(id)
        );

        CREATE INDEX IF NOT EXISTS idx_memories_cluster_id ON memories(cluster_id);
        CREATE INDEX IF NOT EXISTS idx_memories_deleted_at ON memories(deleted_at);
        """
    )


def init_db() -> None:
    """Initialize the database on startup."""
    with db_conn() as conn:
        create_schema(conn)

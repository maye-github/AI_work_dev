"""SQLite ストア。

Oracle 版 DDL と同じ列構成にしてあるので、本番移行時に
テーブル定義とクエリの形をそのまま持ち上げられる。
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import numpy as np

SCHEMA = """
CREATE TABLE IF NOT EXISTS kb_doc (
    doc_id      TEXT PRIMARY KEY,
    scope       TEXT NOT NULL,              -- company | project
    project_id  TEXT,
    title       TEXT NOT NULL,
    doc_type    TEXT NOT NULL,
    phase       TEXT,
    version     TEXT,
    status      TEXT NOT NULL,              -- draft | review | active | deprecated
    conf_level  INTEGER NOT NULL DEFAULT 20,-- 10:公開 20:社内 30:案件 40:機密
    owner       TEXT,
    path        TEXT NOT NULL,
    sha256      TEXT NOT NULL,
    updated_at  TEXT,
    indexed_at  TEXT
);

CREATE TABLE IF NOT EXISTS kb_chunk (
    chunk_id    TEXT PRIMARY KEY,
    doc_id      TEXT NOT NULL REFERENCES kb_doc(doc_id) ON DELETE CASCADE,
    ord         INTEGER NOT NULL,
    heading     TEXT,
    kind        TEXT,                       -- para | row | code
    text        TEXT NOT NULL,
    embedding   BLOB NOT NULL,
    emb_model   TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_kb_chunk_doc   ON kb_chunk(doc_id);
CREATE INDEX IF NOT EXISTS idx_kb_doc_scope   ON kb_doc(scope, project_id);
CREATE INDEX IF NOT EXISTS idx_kb_doc_status  ON kb_doc(status);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def connect(db_path: str | Path) -> sqlite3.Connection:
    p = Path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def get_doc(conn: sqlite3.Connection, doc_id: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM kb_doc WHERE doc_id = ?", (doc_id,)).fetchone()


def doc_exists_at_path(conn: sqlite3.Connection, path: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM kb_doc WHERE path = ?", (path,)).fetchone()


def upsert_doc(conn: sqlite3.Connection, doc: dict) -> None:
    conn.execute(
        """
        INSERT INTO kb_doc (doc_id, scope, project_id, title, doc_type, phase,
                            version, status, conf_level, owner, path, sha256,
                            updated_at, indexed_at)
        VALUES (:doc_id, :scope, :project_id, :title, :doc_type, :phase,
                :version, :status, :conf_level, :owner, :path, :sha256,
                :updated_at, :indexed_at)
        ON CONFLICT(doc_id) DO UPDATE SET
            scope=excluded.scope, project_id=excluded.project_id,
            title=excluded.title, doc_type=excluded.doc_type,
            phase=excluded.phase, version=excluded.version,
            status=excluded.status, conf_level=excluded.conf_level,
            owner=excluded.owner, path=excluded.path, sha256=excluded.sha256,
            updated_at=excluded.updated_at, indexed_at=excluded.indexed_at
        """,
        doc,
    )


def delete_doc(conn: sqlite3.Connection, doc_id: str) -> None:
    conn.execute("DELETE FROM kb_chunk WHERE doc_id = ?", (doc_id,))
    conn.execute("DELETE FROM kb_doc WHERE doc_id = ?", (doc_id,))


def replace_chunks(
    conn: sqlite3.Connection,
    doc_id: str,
    chunks: Iterable[dict],
    vectors: np.ndarray,
    emb_model: str,
) -> int:
    conn.execute("DELETE FROM kb_chunk WHERE doc_id = ?", (doc_id,))
    n = 0
    for n, (ch, vec) in enumerate(zip(chunks, vectors)):
        conn.execute(
            """
            INSERT INTO kb_chunk (chunk_id, doc_id, ord, heading, kind, text,
                                  embedding, emb_model)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"{doc_id}#{n:04d}",
                doc_id,
                n,
                ch.get("heading"),
                ch.get("kind"),
                ch["text"],
                np.asarray(vec, dtype=np.float32).tobytes(),
                emb_model,
            ),
        )
    return n + 1 if n or chunks else 0


def all_doc_ids(conn: sqlite3.Connection) -> set[str]:
    return {r[0] for r in conn.execute("SELECT doc_id FROM kb_doc")}


def stats(conn: sqlite3.Connection) -> dict:
    docs = conn.execute("SELECT COUNT(*) FROM kb_doc").fetchone()[0]
    chunks = conn.execute("SELECT COUNT(*) FROM kb_chunk").fetchone()[0]
    by_scope = {
        r[0]: r[1]
        for r in conn.execute("SELECT scope, COUNT(*) FROM kb_doc GROUP BY scope")
    }
    models = [r[0] for r in conn.execute("SELECT DISTINCT emb_model FROM kb_chunk")]
    return {"docs": docs, "chunks": chunks, "by_scope": by_scope, "emb_models": models}

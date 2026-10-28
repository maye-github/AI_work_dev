# -*- coding: utf-8 -*-
"""SQLite index build and hybrid retrieval.

First version uses SQLite FTS5 (trigram) plus a deterministic character
n-gram scorer.  The n-gram scorer exists because FTS5 trigram cannot match
2-character Japanese terms such as "排他" or "登録".
"""
from __future__ import annotations

import math
import os
import re
import sqlite3
import unicodedata

from .loader import corpus_digest

SCHEMA_VERSION = "1"

# Japanese particles used as soft separators for query segmentation.
_PARTICLES = "のはがをにでとやかもへ"

# Question boilerplate removed before n-gram generation.
_STOP_PHRASES = (
    "教えてください",
    "教えて",
    "ください",
    "ですか",
    "ますか",
    "でしょうか",
    "について",
    "どのように",
    "どの",
    "この",
    "その",
    "何を",
    "何が",
    "何",
    "どれ",
    "どこ",
    "なぜ",
    "どう",
    "ありますか",
)

_RUN_RE = re.compile(r"[0-9a-z_]+|[぀-ヿ㐀-䶿一-鿿]+")


def normalize(text):
    return unicodedata.normalize("NFKC", text).casefold()


def _segments(query):
    s = normalize(query)
    for phrase in _STOP_PHRASES:
        s = s.replace(phrase, " ")
    s = re.sub("[%s]" % _PARTICLES, " ", s)
    # Module names are routing hints, not content.  They appear in every chunk
    # of a module and would otherwise swamp the lexical score.
    return [
        t for t in _RUN_RE.findall(s)
        if len(t) >= 2 and not t.startswith("r60")
    ]


def _grams(text, n):
    return {text[i:i + n] for i in range(len(text) - n + 1)}


def _all_grams(text):
    return _grams(text, 2) | _grams(text, 3)


def default_db_path(scope):
    return os.path.join("build", "rag", "r60-%s.sqlite" % scope)


def build_index(rows, scope, db_path=None):
    """Build a fresh index.  Existing file is replaced (deterministic)."""
    db_path = db_path or default_db_path(scope)
    parent = os.path.dirname(db_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE chunks (
                chunk_id TEXT PRIMARY KEY,
                module TEXT NOT NULL,
                artifact_type TEXT NOT NULL,
                ids TEXT NOT NULL,
                title TEXT NOT NULL,
                source_path TEXT NOT NULL,
                source_locator TEXT NOT NULL,
                sensitivity TEXT NOT NULL,
                corpus_scope TEXT NOT NULL,
                text TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                version TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE VIRTUAL TABLE chunks_fts USING fts5(
                chunk_id UNINDEXED,
                title,
                text,
                tokenize='trigram'
            )
            """
        )
        conn.execute(
            "CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        for row in rows:
            conn.execute(
                "INSERT INTO chunks VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    row["chunk_id"], row["module"], row["artifact_type"],
                    ",".join(row["ids"]), row["title"], row["source_path"],
                    row["source_locator"], row["sensitivity"],
                    row["corpus_scope"], row["text"], row["sha256"],
                    row["version"],
                ),
            )
            conn.execute(
                "INSERT INTO chunks_fts (chunk_id, title, text) VALUES (?,?,?)",
                (row["chunk_id"], row["title"], row["text"]),
            )
        meta = {
            "scope": scope,
            "chunk_count": str(len(rows)),
            "corpus_sha256": corpus_digest(rows),
            "schema_version": SCHEMA_VERSION,
        }
        conn.executemany(
            "INSERT INTO meta (key, value) VALUES (?,?)", sorted(meta.items())
        )
        conn.commit()
    finally:
        conn.close()
    return db_path


def _connect(db_path):
    if not os.path.exists(db_path):
        raise FileNotFoundError(
            "index not found: %s (run `py -3 -m tools.rag build --scope ...`)" % db_path
        )
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _fetch_rows(conn, module=None):
    sql = "SELECT * FROM chunks"
    args = ()
    if module:
        sql += " WHERE module = ?"
        args = (module,)
    return [dict(r) for r in conn.execute(sql, args)]


def _fts_ranks(conn, segments, module=None):
    terms = sorted({t for t in segments if len(t) >= 3})
    if not terms:
        return {}
    match = " OR ".join('"%s"' % t.replace('"', '""') for t in terms)
    sql = (
        "SELECT chunk_id, bm25(chunks_fts) AS score "
        "FROM chunks_fts WHERE chunks_fts MATCH ? ORDER BY score LIMIT 100"
    )
    try:
        ranked = conn.execute(sql, (match,)).fetchall()
    except sqlite3.OperationalError:
        return {}
    ranks = {}
    pos = 0
    for r in ranked:
        cid = r["chunk_id"]
        pos += 1
        ranks[cid] = pos
    if module:
        allowed = {r["chunk_id"] for r in _fetch_rows(conn, module)}
        ranks = {c: p for c, p in ranks.items() if c in allowed}
    return ranks


def _lexical_scores(rows, query):
    segments = _segments(query)
    if not segments:
        return {}, segments

    query_grams = {}
    for seg in segments:
        for g in _grams(seg, 3):
            query_grams[g] = 2.0
        for g in _grams(seg, 2):
            query_grams.setdefault(g, 1.0)

    prepared = []
    for row in rows:
        title = normalize(row["title"])
        text = normalize(row["text"])
        prepared.append((row, title, text, _all_grams(title) | _all_grams(text)))

    n = len(prepared) or 1
    df = {}
    for g in query_grams:
        df[g] = sum(1 for _, _, _, grams in prepared if g in grams)
    idf = {g: math.log((n + 1.0) / (df[g] + 1.0)) + 1.0 for g in query_grams}

    scores = {}
    for row, title, text, grams in prepared:
        score = 0.0
        for g, base in query_grams.items():
            if g in grams:
                weight = base * idf[g]
                if g in title:
                    weight *= 2.0
                score += weight
        for seg in segments:
            if seg in title:
                score += 8.0
            score += 3.0 * title.count(seg) + text.count(seg)
        scores[row["chunk_id"]] = score
    return scores, segments


def search(db_path, query, k=5, module=None):
    """Return the top-k chunks as dicts with ``score`` added."""
    conn = _connect(db_path)
    try:
        rows = _fetch_rows(conn, module)
        if not rows:
            return []
        by_id = {r["chunk_id"]: r for r in rows}
        lex_scores, segments = _lexical_scores(rows, query)
        fts_ranks = _fts_ranks(conn, segments, module)
    finally:
        conn.close()

    lex_order = sorted(
        (cid for cid, s in lex_scores.items() if s > 0),
        key=lambda cid: (-lex_scores[cid], cid),
    )
    lex_rank = {cid: i + 1 for i, cid in enumerate(lex_order)}

    # Lexical rank is the primary signal; FTS is a secondary confirmation.
    # A small rank constant keeps the head of the lexical ranking separated.
    fused = {}
    for cid, rank in lex_rank.items():
        fused[cid] = fused.get(cid, 0.0) + 3.0 / (10.0 + rank)
    for cid, rank in fts_ranks.items():
        fused[cid] = fused.get(cid, 0.0) + 0.5 / (60.0 + rank)

    ordered = sorted(fused.items(), key=lambda kv: (-kv[1], kv[0]))[:k]
    results = []
    for cid, score in ordered:
        row = dict(by_id[cid])
        row["score"] = round(score, 6)
        results.append(row)
    return results


def stats(db_path):
    conn = _connect(db_path)
    try:
        meta = dict(conn.execute("SELECT key, value FROM meta").fetchall())
        counts = [
            dict(r) for r in conn.execute(
                "SELECT module, COUNT(*) AS n FROM chunks GROUP BY module ORDER BY module"
            )
        ]
        types = [
            dict(r) for r in conn.execute(
                "SELECT artifact_type, COUNT(*) AS n FROM chunks "
                "GROUP BY artifact_type ORDER BY artifact_type"
            )
        ]
        return {"meta": meta, "modules": counts, "artifact_types": types}
    finally:
        conn.close()

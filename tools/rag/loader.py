# -*- coding: utf-8 -*-
"""Load and validate chunk JSONL files."""
from __future__ import annotations

import hashlib
import json
import os

REQUIRED_KEYS = {
    "chunk_id",
    "module",
    "artifact_type",
    "ids",
    "title",
    "source_path",
    "source_locator",
    "sensitivity",
    "corpus_scope",
    "text",
    "sha256",
    "version",
}

DEFAULT_CHUNKS_DIR = os.path.join("docs", "95_legacy", "r60", "chunks")


class ChunkError(ValueError):
    """Raised when a chunk file violates the schema."""


def _check_one(row, path, lineno):
    missing = REQUIRED_KEYS - set(row)
    if missing:
        raise ChunkError("%s:%d missing keys: %s" % (path, lineno, sorted(missing)))
    extra = set(row) - REQUIRED_KEYS
    if extra:
        raise ChunkError("%s:%d unexpected keys: %s" % (path, lineno, sorted(extra)))
    if not isinstance(row["ids"], list):
        raise ChunkError("%s:%d ids must be a list" % (path, lineno))
    digest = hashlib.sha256(row["text"].encode("utf-8")).hexdigest()
    if digest != row["sha256"]:
        raise ChunkError("%s:%d sha256 mismatch for %s" % (path, lineno, row["chunk_id"]))


def load_chunks(chunks_dir=DEFAULT_CHUNKS_DIR, scope="teaching"):
    """Return chunks for *scope*, sorted by chunk_id for determinism."""
    if not os.path.isdir(chunks_dir):
        raise ChunkError("chunks directory not found: %s" % chunks_dir)

    rows = []
    seen = {}
    for name in sorted(os.listdir(chunks_dir)):
        if not name.endswith(".jsonl"):
            continue
        path = os.path.join(chunks_dir, name)
        with open(path, "r", encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ChunkError("%s:%d invalid JSON: %s" % (path, lineno, exc))
                _check_one(row, path, lineno)
                if row["corpus_scope"] != scope:
                    continue
                cid = row["chunk_id"]
                if cid in seen:
                    raise ChunkError("duplicate chunk_id %s (%s and %s)" % (cid, seen[cid], path))
                seen[cid] = path
                rows.append(row)

    rows.sort(key=lambda r: r["chunk_id"])
    return rows


def corpus_digest(rows):
    """Deterministic digest of the logical corpus contents."""
    h = hashlib.sha256()
    for row in sorted(rows, key=lambda r: r["chunk_id"]):
        h.update(row["chunk_id"].encode("utf-8"))
        h.update(b"\0")
        h.update(row["sha256"].encode("ascii"))
        h.update(b"\n")
    return h.hexdigest()

"""取り込み（lint + ingest）。

ingest は「差分だけ」を既定にする。Git を正とし、索引は再生成可能な派生物。
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import numpy as np

from kbkit import chunker, fm, store

REQUIRED_KEYS = [
    "doc_id", "scope", "title", "doc_type", "version",
    "status", "conf_level", "updated_at",
]
SCOPES = {"company", "project"}
STATUSES = {"draft", "review", "active", "deprecated"}
# 2026-10-29 追加: 骨架（`.claude/rules/02` §6）の状態機の語彙を受ける。
#   旧案件知識を `tools/kb-platform/repo/` へ移したため、1 ファイルが
#   骨架 gate3 と本 lint の両方を満たす必要が生じた（status の共通部分が
#   `draft` だけでは、baselined にすると検索から消え、active にすると gate3 が落ちる）。
#   「どの状態を検索対象にするか」は retrieval.py 側の RETRIEVABLE が持つ。
STATUSES |= {"open", "baselined", "changed", "done", "void"}
DOC_TYPES = {
    "standard", "pattern", "glossary", "requirement",
    "design-basic", "design-detail", "test", "decision",
    "incident", "howto",
}
CONF_LEVELS = {10, 20, 30, 40}
_MIN_TITLE = 4


def collect_docs(repo_root: str | Path) -> list[tuple[Path, str]]:
    root = Path(repo_root)
    out: list[tuple[Path, str]] = []
    for p in sorted(root.rglob("*.md")):
        rel = p.relative_to(root).as_posix()
        if rel.startswith("eval/") or rel.startswith("."):
            continue
        out.append((p, rel))
    return out


def _load(path: Path) -> tuple[dict, str]:
    return fm.split_front_matter(path.read_text(encoding="utf-8"))


def lint(repo_root: str | Path) -> list[str]:
    root = Path(repo_root)
    issues: list[str] = []
    seen_ids: dict[str, str] = {}
    seen_paths: set[str] = set()

    for path, rel in collect_docs(root):
        try:
            meta, body = _load(path)
        except Exception as e:  # noqa: BLE001 - lint は全件報告したい
            issues.append(f"{rel}: front matter を解析できません: {e}")
            continue

        if not meta:
            issues.append(f"{rel}: front matter がありません")
            continue

        for k in REQUIRED_KEYS:
            if meta.get(k) in (None, ""):
                issues.append(f"{rel}: 必須キー '{k}' がありません")

        doc_id = str(meta.get("doc_id") or "")
        if doc_id:
            if doc_id in seen_ids:
                issues.append(f"{rel}: doc_id '{doc_id}' が {seen_ids[doc_id]} と重複")
            seen_ids[doc_id] = rel
            if not doc_id.replace("-", "").isalnum():
                issues.append(f"{rel}: doc_id は英数字とハイフンのみ: '{doc_id}'")

        scope = meta.get("scope")
        if scope not in SCOPES:
            issues.append(f"{rel}: scope は {sorted(SCOPES)} のいずれか: {scope!r}")

        dtype = meta.get("doc_type")
        if dtype not in DOC_TYPES:
            issues.append(f"{rel}: doc_type が不正: {dtype!r}")

        status = meta.get("status")
        if status not in STATUSES:
            issues.append(f"{rel}: status が不正: {status!r}")

        try:
            level = int(meta.get("conf_level"))
            if level not in CONF_LEVELS:
                issues.append(f"{rel}: conf_level は {sorted(CONF_LEVELS)} のいずれか: {level}")
        except (TypeError, ValueError):
            issues.append(f"{rel}: conf_level が整数ではありません: {meta.get('conf_level')!r}")

        title = str(meta.get("title") or "")
        if len(title) < _MIN_TITLE:
            issues.append(f"{rel}: title が短すぎます: {title!r}")

        project_id = meta.get("project_id")
        if scope == "project":
            if not project_id:
                issues.append(f"{rel}: scope=project には project_id が必須です")
            elif f"projects/{project_id}/" not in rel:
                issues.append(
                    f"{rel}: project_id '{project_id}' と配置先ディレクトリが不一致"
                )
        elif scope == "company" and project_id:
            issues.append(f"{rel}: scope=company に project_id は指定できません")

        if not body.strip():
            issues.append(f"{rel}: 本文が空です")

        if rel in seen_paths:
            issues.append(f"{rel}: パスが重複")
        seen_paths.add(rel)

    return issues


def ingest(
    repo_root: str | Path,
    conn: sqlite3.Connection,
    embedder,
    changed_only: bool = True,
    reset: bool = False,
) -> dict:
    report = {
        "added": 0, "updated": 0, "skipped": 0,
        "chunks": 0, "errors": [],
    }
    if reset:
        conn.execute("DELETE FROM kb_chunk")
        conn.execute("DELETE FROM kb_doc")
        conn.commit()

    for path, rel in collect_docs(repo_root):
        raw = path.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        try:
            meta, body = fm.split_front_matter(raw.decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            report["errors"].append(f"{rel}: {e}")
            continue

        doc_id = str(meta.get("doc_id") or "").strip()
        if not doc_id:
            report["errors"].append(f"{rel}: doc_id がありません")
            continue

        existing = store.get_doc(conn, doc_id)
        if existing and existing["path"] != rel:
            report["errors"].append(
                f"{rel}: doc_id '{doc_id}' は {existing['path']} が使用中"
            )
            continue
        if changed_only and existing and existing["sha256"] == sha:
            report["skipped"] += 1
            continue

        chunks = chunker.chunk_document(body, meta)
        if not chunks:
            report["errors"].append(f"{rel}: チャンクが 0 件（本文が空？）")
            continue

        vectors = embedder.embed_batch([c["text"] for c in chunks])

        store.upsert_doc(
            conn,
            {
                "doc_id": doc_id,
                "scope": str(meta.get("scope") or "company"),
                "project_id": meta.get("project_id"),
                "title": str(meta.get("title") or ""),
                "doc_type": str(meta.get("doc_type") or ""),
                "phase": meta.get("phase"),
                "version": str(meta.get("version") or ""),
                "status": str(meta.get("status") or "draft"),
                "conf_level": int(meta.get("conf_level") or 20),
                "owner": meta.get("owner"),
                "path": rel,
                "sha256": sha,
                "updated_at": str(meta.get("updated_at") or ""),
                "indexed_at": store.now_iso(),
            },
        )
        store.replace_chunks(conn, doc_id, chunks, vectors, embedder.name)
        conn.commit()

        report["updated" if existing else "added"] += 1
        report["chunks"] += len(chunks)

    return report


def prune_deleted(conn: sqlite3.Connection, repo_root: str | Path) -> list[str]:
    """リポジトリから消えた文書を索引からも消す。"""
    live = {rel for _, rel in collect_docs(repo_root)}
    removed = []
    for row in conn.execute("SELECT doc_id, path FROM kb_doc").fetchall():
        if row["path"] not in live:
            store.delete_doc(conn, row["doc_id"])
            removed.append(row["doc_id"])
    conn.commit()
    return removed

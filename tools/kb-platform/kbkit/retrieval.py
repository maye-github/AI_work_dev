"""検索。

鉄則:
  1. 権限・スコープのフィルタは SQL の WHERE に押し込む（後掛け禁止）
  2. dense + sparse を RRF で統合
  3. 最後に rerank を通す（Phase 0 は簡易リランカー）
"""

from __future__ import annotations

import math
import os
import sqlite3
from typing import Callable

import numpy as np

from kbkit.embedder import normalize_text

RRF_K = 60


def _bigrams(text: str) -> set[str]:
    s = normalize_text(text).replace(" ", "")
    if len(s) < 2:
        return {s} if s else set()
    return {s[i : i + 2] for i in range(len(s) - 1)}


# 2026-10-29 追加: 検索対象にする status。上流は `active` 固定だったが、
#   骨架（`.claude/rules/02` §6）の状態機は `open/baselined/changed/done` を使うため、
#   そのままでは移設した知識が 1 件も当たらない。既定を骨架の「進行中〜完了」に広げ、
#   環境変数 `KB_RETRIEVABLE_STATUSES`（カンマ区切り）で上書きできるようにした。
#   `draft` / `void` / `deprecated` は既定で除外（未確定・作废は検索に出さない）。
DEFAULT_RETRIEVABLE = "active,open,baselined,changed,done"


def _retrievable_statuses() -> tuple[str, ...]:
    raw = os.environ.get("KB_RETRIEVABLE_STATUSES", DEFAULT_RETRIEVABLE)
    return tuple(s.strip() for s in raw.split(",") if s.strip())


def _load_candidates(
    conn: sqlite3.Connection,
    project_id: str | None,
    user_level: int,
) -> list[sqlite3.Row]:
    statuses = _retrievable_statuses()
    placeholders = ", ".join(f":st{i}" for i in range(len(statuses)))
    where = [f"d.status IN ({placeholders})", "d.conf_level <= :user_level"]
    params: dict[str, object] = {"user_level": user_level}
    for i, st in enumerate(statuses):
        params[f"st{i}"] = st
    if project_id:
        # 会社共通は全案件から、案件知識はその案件からのみ
        where.append(
            "(d.scope = 'company' OR (d.scope = 'project' AND d.project_id = :pid))"
        )
        params["pid"] = project_id
    else:
        where.append("d.scope = 'company'")
    sql = f"""
        SELECT c.chunk_id, c.doc_id, c.ord, c.heading, c.kind, c.text, c.embedding,
               d.title, d.doc_type, d.scope, d.project_id, d.conf_level
        FROM kb_chunk c
        JOIN kb_doc d ON d.doc_id = c.doc_id
        WHERE {' AND '.join(where)}
    """
    return conn.execute(sql, params).fetchall()


def _sparse_scores(query: str, rows: list[sqlite3.Row]) -> np.ndarray:
    qb = _bigrams(query)
    if not qb:
        return np.zeros(len(rows), dtype=np.float32)
    doc_bigrams = [_bigrams(r["text"] + " " + (r["heading"] or "")) for r in rows]
    n = len(rows)
    df = {g: 0 for g in qb}
    for db in doc_bigrams:
        for g in qb & db:
            df[g] += 1
    idf = {g: math.log((n + 1) / (df[g] + 1)) + 1.0 for g in qb}
    total = sum(idf.values()) or 1.0
    scores = np.zeros(n, dtype=np.float32)
    for i, db in enumerate(doc_bigrams):
        hit = sum(idf[g] for g in qb & db)
        scores[i] = hit / total
    return scores


def _order(scores: np.ndarray) -> list[int]:
    return [int(i) for i in np.argsort(-scores, kind="stable")]


def _rrf(rank_lists: list[list[int]], n: int, k: int = RRF_K) -> np.ndarray:
    agg = np.zeros(n, dtype=np.float32)
    for lst in rank_lists:
        for rank, idx in enumerate(lst, 1):
            agg[idx] += 1.0 / (k + rank)
    return agg


def simple_rerank(query: str, row: sqlite3.Row, base: float) -> float:
    """Phase 0 用の簡易リランカー（見出し一致と語の被覆を加点）。"""
    qb = _bigrams(query)
    hb = _bigrams(row["heading"] or "")
    tb = _bigrams(row["title"] or "")
    head = len(qb & hb) / (len(qb) or 1)
    title = len(qb & tb) / (len(qb) or 1)
    coverage = len(qb & _bigrams(row["text"])) / (len(qb) or 1)
    # 本文の被覆を最重視。見出し・タイトルは補助シグナルに留める
    # （タイトル一致は全チャンクに一律で乗るため、強くすると本文の差が消える）
    return base + 0.30 * coverage + 0.10 * head + 0.05 * title


def _filter_candidates(
    rows: list[sqlite3.Row],
    module: str | None = None,
    scope: str | None = None,
) -> list[sqlite3.Row]:
    """案件内の「モジュール」「スコープ」で候補を絞る（2026-10-29 追加）。

    なぜ要るか: 案件知識を 1 案件にまとめて入れたため、`R60User` の質問に対して
    `R60SesModel` の同種の節（イベント一覧など）が上位に来る。呼び出し側は
    「どのモジュールの話か」を知っているのに、それを伝える口が無かった
    （実測: 80 題中 3 件がモジュール違いで落ちた）。

    モジュールの判定は doc_id と title の部分一致（`r60ssk` / `R60Ssk` など）。
    語幹が同じ別モジュールが現れたら、そのときに対応表を足すこと。
    """
    if module:
        m = module.strip().lower()
        if m:
            rows = [
                r for r in rows
                if m in (r["doc_id"] or "").lower() or m in (r["title"] or "").lower()
            ]
    if scope:
        rows = [r for r in rows if (r["scope"] or "") == scope]
    return rows


def search(
    conn: sqlite3.Connection,
    query: str,
    embedder,
    project_id: str | None = None,
    user_level: int = 30,
    top_k: int = 5,
    rerank_n: int = 30,
    reranker: Callable[[str, sqlite3.Row, float], float] | None = simple_rerank,
    module: str | None = None,
    scope: str | None = None,
) -> list[dict]:
    rows = _filter_candidates(_load_candidates(conn, project_id, user_level), module, scope)
    if not rows:
        return []

    qvec = embedder.embed(query)
    mat = np.vstack([np.frombuffer(r["embedding"], dtype=np.float32) for r in rows])
    dense = mat @ qvec
    sparse = _sparse_scores(query, rows)

    fused = _rrf([_order(dense), _order(sparse)], len(rows))

    shortlist = _order(fused)[: max(rerank_n, top_k)]
    ranked: list[tuple[float, int]] = []
    for idx in shortlist:
        score = float(fused[idx])
        if reranker is not None:
            score = float(reranker(query, rows[idx], score))
        ranked.append((score, idx))
    ranked.sort(key=lambda x: (-x[0], rows[x[1]]["chunk_id"]))

    out: list[dict] = []
    for score, idx in ranked[:top_k]:
        r = rows[idx]
        out.append(
            {
                "chunk_id": r["chunk_id"],
                "doc_id": r["doc_id"],
                "title": r["title"],
                "heading": r["heading"],
                "kind": r["kind"],
                "scope": r["scope"],
                "project_id": r["project_id"],
                "doc_type": r["doc_type"],
                "conf_level": r["conf_level"],
                "text": r["text"],
                "score": round(score, 6),
                "dense": round(float(dense[idx]), 6),
                "sparse": round(float(sparse[idx]), 6),
                "citation": f"[{r['doc_id']}] {r['title']} § {r['heading']}",
            }
        )
    return out


def build_context(results: list[dict], max_chars: int = 4000) -> str:
    """LLM に渡す引用付きコンテキストを組み立てる。"""
    parts, used = [], 0
    for r in results:
        block = f"### {r['citation']}\n{r['text']}\n"
        if used + len(block) > max_chars:
            break
        parts.append(block)
        used += len(block)
    return "\n".join(parts)

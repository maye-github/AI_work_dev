"""`kbkit.retrieval.search` に `module` / `scope` を足した入口。

中身は上流の `search()` をそのまま呼ぶだけである。違いは 1 点だけで、
呼び出しの間だけ候補抽出（`_load_candidates`）をこの層の版に差し替える
（`_bootstrap.patched_candidates`）。**並び替えは上流が持つ 1 本だけ**であり、
ここに複製は無い。上流が並び替えを直せば、こちらの数字もそのまま直る。
"""

from __future__ import annotations

import json
import sqlite3
from typing import Callable

from tools.kb_local import _bootstrap
from tools.kb_local._bootstrap import _retrieval as R

__all__ = ["search"]

_UNSET = object()


#: 本文で使われている根拠の印。**弱い順**に並べる（先頭が最も注意を要する）。
#: 知識庫の本文は `【実測】`（実装を見て確かめた）・`【文書】`（文書に書いてある）・
#: `【推測】`（書いていないので推した）・`【差異】`（食い違いを登記した）を使い分けている。
CONF_ORDER = ("推測", "差異", "文書", "実測")


def _markers(text: str) -> list[str]:
    return [name for name in CONF_ORDER if f"【{name}】" in text]


def _attach_confidence(results: list[dict]) -> list[dict]:
    """結果に根拠の印を付ける。

    **これが無いと、`【推測】` の節を `【実測】` と同じ顔で読んでしまう。**
    検索結果は順位だけを返すので、中身の信頼度は本文を読むまで分からない——
    それを結果の側に引き上げる。
    """
    for item in results:
        # 印は本文にも見出しにも現れる（例:「§ 4. イベント一覧（【文書】… ＋【実測】実装）」）。
        # **両方を見る**——片方だけだと取りこぼす（実測で見出し側だけに付いていた）。
        haystack = f"{item.get('heading') or ''}\n{item.get('text') or ''}"
        found = _markers(haystack)
        item["markers"] = found
        item["confidence"] = found[0] if found else None
    return results


def _attach_extras(conn: sqlite3.Connection, results: list[dict]) -> list[dict]:
    """結果に `source_project` / `req_ids` を足す（退避表があるときだけ）。

    上流の `search()` は決め打ちの dict を返すため、出处と要求紐付けは載らない。
    ここで 1 回だけ引いて足す。**退避表が無い DB では何もしない**
    （上流だけを流した直後でも落ちないようにするため）。
    """
    if not results:
        return results
    ids = sorted({str(r["doc_id"]) for r in results})
    placeholders = ",".join("?" for _ in ids)
    try:
        rows = conn.execute(
            f"SELECT doc_id, source_project, req_ids FROM kb_doc_extra "
            f"WHERE doc_id IN ({placeholders})",
            ids,
        ).fetchall()
    except sqlite3.OperationalError:
        return results
    extra = {r[0]: (r[1], r[2]) for r in rows}

    # 派生ビュー（`chunks/` の検索摘要）かどうかを結果に載せる。
    # 摘要は検索対象としては強い（実測：外すと recall が落ちる）が、
    # **要約に移す過程で【推測】等の印が落ちる**ことがある。読む人にそれを知らせる。
    paths: dict[str, str] = {}
    try:
        for doc_id, path in conn.execute(
            f"SELECT doc_id, path FROM kb_doc WHERE doc_id IN ({placeholders})", ids
        ):
            paths[str(doc_id)] = str(path or "")
    except sqlite3.OperationalError:
        pass

    for item in results:
        doc_id = str(item["doc_id"])
        source, raw = extra.get(doc_id, (None, None))
        item["source_project"] = source
        try:
            item["req_ids"] = json.loads(raw) if raw else []
        except (TypeError, ValueError):
            item["req_ids"] = []
        item["path"] = paths.get(doc_id, "")
        item["derived"] = "/chunks/" in item["path"]
    return results


def search(
    conn: sqlite3.Connection,
    query: str,
    embedder,
    project_id: str | None = None,
    user_level: int = 30,
    top_k: int = 5,
    rerank_n: int = 30,
    reranker: Callable[[str, sqlite3.Row, float], float] | None | object = _UNSET,
    module: str | None = None,
    scope: str | None = None,
    allowed_projects: set[str] | None = None,
    exclude_derived: bool = False,
) -> list[dict]:
    """上流 `search()` と同じ戻り値に、`module` / `scope` の絞り込みを足したもの。

    `module` … doc_id か title の部分一致（例 `R60Ssk`）。呼び出し側が
    「どのモジュールの話か」を知っているときに渡す。実測で 80 題の recall@5 が
    0.863 → 0.925、top-1 のモジュール一致が 76/80 → 80/80 になる。
    `scope` … `company`（会社共通のみ）/ `project`（案件知識のみ）。
    """
    kwargs: dict[str, object] = {}
    if reranker is not _UNSET:
        kwargs["reranker"] = reranker

    with _bootstrap.patched_candidates(module, scope, allowed_projects, exclude_derived):
        results = R.search(
            conn, query, embedder,
            project_id=project_id, user_level=user_level,
            top_k=top_k, rerank_n=rerank_n, **kwargs,
        )
    return _attach_confidence(_attach_extras(conn, results))

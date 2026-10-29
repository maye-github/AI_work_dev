"""`kbkit.retrieval.search` に `module` / `scope` を足した入口。

中身は上流の `search()` をそのまま呼ぶだけである。違いは 1 点だけで、
呼び出しの間だけ候補抽出（`_load_candidates`）をこの層の版に差し替える
（`_bootstrap.patched_candidates`）。**並び替えは上流が持つ 1 本だけ**であり、
ここに複製は無い。上流が並び替えを直せば、こちらの数字もそのまま直る。
"""

from __future__ import annotations

import sqlite3
from typing import Callable

from tools.kb_local import _bootstrap
from tools.kb_local._bootstrap import _retrieval as R

__all__ = ["search"]

_UNSET = object()


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

    with _bootstrap.patched_candidates(module, scope):
        return R.search(
            conn, query, embedder,
            project_id=project_id, user_level=user_level,
            top_k=top_k, rerank_n=rerank_n, **kwargs,
        )

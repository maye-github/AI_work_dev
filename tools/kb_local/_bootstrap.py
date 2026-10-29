"""上流 `tools/kb-platform` を **1 バイトも変えずに** 振る舞いだけ差し替える土台。

なぜ必要か
----------
`tools/kb-platform/` は会社の上流（`D:\\AI_platform\\kb-platform`）の写しである。
上流の実装規則は我々の持ち物ではないので、**上流のファイルには手を入れない**
（`UPSTREAM-SYNC.md` §7）。一方で、骨架の状態機（`.claude/rules/02` §6）の語彙、
モジュール絞り込み、節レベルの評価は上流に無い。

そこで **上流は逐字のまま置き、差分はこの層（`tools/kb_local/`）にだけ書く**。
同期は「フォルダを丸ごと差し替える」で済み、当て直すファイルは 0 本になる。

差し込み口は 2 つだけ（どちらも上流の**公開関数を呼ぶ前に**一時的に差し替え、直後に戻す）
--------------------------------------------------------------------------------------
1. `kbkit.retrieval._load_candidates` … 候補抽出の WHERE 句。
   `kbkit.retrieval.search()` はこの名前をモジュール global から引くので、
   呼び出しの間だけ差し替えれば **並び替え（dense+sparse→RRF→rerank）は上流のまま**使える。
   上流の並び替えを複製しないことが、同期コストを増やさない唯一の方法である。
2. `kbkit.pipeline.STATUSES` … lint の語彙。`lint()` の間だけ広げる。

**上流がこの 2 つの名前を変えたら、ここが例外で落ちる。** 黙って挙動が変わるより、
同期のときに気づけるほうがよい（`UPSTREAM-SYNC.md` §2 の手順で必ず回帰を取る）。
"""

from __future__ import annotations

import contextlib
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "tools" / "kb-platform"
if str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

from kbkit import pipeline as _pipeline  # noqa: E402
from kbkit import retrieval as _retrieval  # noqa: E402

#: 検索対象にする status。上流は `active` 固定。
#: 骨架の状態機は `open/baselined/changed/done` を使うため、既定を「進行中〜完了」に広げる。
#: `draft`（未確定）と `void`（作废）は既定で出さない。
#: 環境変数 `KB_RETRIEVABLE_STATUSES`（カンマ区切り）で上書きできる。
DEFAULT_RETRIEVABLE = "active,open,baselined,changed,done"

#: 上流 `pipeline.STATUSES` に足す分（差分だけを持つ。上流の集合は書き換えない）。
EXTRA_STATUSES = frozenset({"open", "baselined", "changed", "done", "void"})

_CANDIDATE_SQL = """
    SELECT c.chunk_id, c.doc_id, c.ord, c.heading, c.kind, c.text, c.embedding,
           d.title, d.doc_type, d.scope, d.project_id, d.conf_level
    FROM kb_chunk c
    JOIN kb_doc d ON d.doc_id = c.doc_id
    WHERE {where}
"""


def retrievable_statuses() -> tuple[str, ...]:
    raw = os.environ.get("KB_RETRIEVABLE_STATUSES", DEFAULT_RETRIEVABLE)
    return tuple(s.strip() for s in raw.split(",") if s.strip())


def load_candidates(
    conn: sqlite3.Connection,
    project_id: str | None,
    user_level: int,
    module: str | None = None,
    scope: str | None = None,
) -> list[sqlite3.Row]:
    """上流 `_load_candidates` の差し替え版。

    上流の鉄則「権限・スコープのフィルタは SQL の WHERE に押し込む（後掛け禁止）」に従い、
    status・module・scope もすべて WHERE で絞る（取得後に Python で捨てない）。
    """
    statuses = retrievable_statuses()
    placeholders = ", ".join(f":st{i}" for i in range(len(statuses)))
    where = [f"d.status IN ({placeholders})", "d.conf_level <= :user_level"]
    params: dict[str, object] = {"user_level": user_level}
    for i, st in enumerate(statuses):
        params[f"st{i}"] = st

    if project_id:
        # 会社共通は全案件から、案件知識はその案件からのみ（上流と同じ）
        where.append(
            "(d.scope = 'company' OR (d.scope = 'project' AND d.project_id = :pid))"
        )
        params["pid"] = project_id
    else:
        where.append("d.scope = 'company'")

    if scope:
        where.append("d.scope = :scope")
        params["scope"] = scope

    if module and module.strip():
        # doc_id / title の部分一致（`R60Ssk` / `r60ssk` など）。
        # LIKE ではなく instr を使うのは、`%` `_` のエスケープを考えなくて済むため。
        where.append(
            "(instr(lower(d.doc_id), :mod) > 0 OR instr(lower(d.title), :mod) > 0)"
        )
        params["mod"] = module.strip().lower()

    return conn.execute(_CANDIDATE_SQL.format(where=" AND ".join(where)), params).fetchall()


@contextlib.contextmanager
def patched_candidates(module: str | None, scope: str | None):
    """`kbkit.retrieval._load_candidates` を呼び出しの間だけ差し替える。"""
    orig = getattr(_retrieval, "_load_candidates", None)
    if orig is None:
        raise RuntimeError(
            "上流 kbkit.retrieval._load_candidates が見つかりません。"
            "上流で改名された可能性があります（tools/kb_local/_bootstrap.py の差し込み口を確認）。"
        )

    def replacement(conn, project_id, user_level):
        return load_candidates(conn, project_id, user_level, module, scope)

    _retrieval._load_candidates = replacement
    try:
        yield orig
    finally:
        _retrieval._load_candidates = orig


@contextlib.contextmanager
def wider_statuses():
    """`kbkit.pipeline.STATUSES` を lint の間だけ骨架の語彙まで広げる。"""
    orig = _pipeline.STATUSES
    _pipeline.STATUSES = set(orig) | EXTRA_STATUSES
    try:
        yield
    finally:
        _pipeline.STATUSES = orig

"""上流 `tools/kb-platform` を **1 バイトも変えずに** 拡張する層。

    py -3 -m tools.kb_local search "..." --project P-R60-001 --module R60Ssk
    py -3 -m tools.kb_local eval
    py -3 -m tools.kb_local lint
    py -3 -m tools.kb_local ingest --prune     # 上流 run.py へ丸投げ
    py -3 -m tools.kb_local stats              # 同上

`tools/kb-platform/` は会社の上流（`D:\\AI_platform\\kb-platform`）の写しである。
上流の実装規則は我々の持ち物ではないので、**上流のファイルには手を入れない**。
我々の差分（骨架の状態機の語彙・モジュール絞り込み・節レベルの評価）は、
すべてこの層に置く。仕組みは `_bootstrap.py` の冒頭を読むこと。

上流 CLI（`tools/kb-platform/run.py`）を直接使うと、我々の文書は `status` が
`open` / `baselined` のため **`search` は 0 件、`lint` は NG になる**。
検索・lint・評価はこの層を通す（`ingest` / `stats` は上流のままでよい）。
"""

from tools.kb_local.evaluation import evaluate, format_report
from tools.kb_local.retrieval import search

__all__ = ["evaluate", "format_report", "search"]

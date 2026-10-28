"""legacy - 歴史案件（読み取り専用）から設計資産を抽出するツール群。

`D:/AI_work` は**他人のプロジェクトの実コードであり、永久に読み取り専用**である。
本パッケージの抽出器は対象を読むだけで、対象側へは一切書かない。
出力先が読み取り専用領域の内側を指した場合は、書く前に `guard_output()` が拒否する。

依存は標準ライブラリのみ（NFR-6）。機密の実値を書かない（gate6 は `tools/**/*.py` も走査する）。
"""

from __future__ import annotations

import importlib

# 遅延再エクスポート（PEP 562）。
# `from .xlsx_text import *` をここで eager に書くと、`py -3 -m tools.legacy.xlsx_text`
# がモジュールを二重ロードし、runpy が
# 「found in sys.modules after import of package ... unpredictable behaviour」を出す。
# 遅延させると、`tools.legacy.sheet_text` は使えるまま警告が消える。
__all__ = [
    "LegacyToolError",
    "MaskUnavailable",
    "ReadOnlyViolation",
    "guard_output",
    "load_mask_mapping",
    "mask_text_with",
    "read_workbook",
    "sheet_names",
    "sheet_text",
    "workbook_text",
]


def __getattr__(name: str):
    if name in __all__:
        return getattr(importlib.import_module("tools.legacy.xlsx_text"), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(__all__)

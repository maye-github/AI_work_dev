"""trans-cosmos-ai AI 全流程骨架 - 共通パス解決。

各ツールが個別に持っていた「リポジトリルートの上方探索」をここへ一本化する。
リポジトリルートの標識は `docs/00_registry/ids.yml` の 1 点のみである。

依存は標準ライブラリのみ（NFR-6）。機密の実値を書かない（gate6 は `tools/**/*.py` も走査する）。
"""

from __future__ import annotations

import sys
from pathlib import Path

# リポジトリルートを判定する標識（これを持つ階層がルート）
ROOT_MARKER = ("docs", "00_registry", "ids.yml")
REGISTRY_REL = "docs/00_registry/ids.yml"
TRACEABILITY_REL = "docs/00_registry/traceability.yml"


def registry_path(root: Path) -> Path:
    """ID 台帳（ids.yml）の絶対パス。"""
    return root.joinpath(*ROOT_MARKER)


def traceability_path(root: Path) -> Path:
    """トレーサビリティ・マトリクスの絶対パス。"""
    return root / TRACEABILITY_REL


def find_root(start: Path | None = None) -> Path:
    """リポジトリルート（docs/00_registry/ids.yml がある階層）を上方探索で特定する。

    見つからなければカレントディレクトリを返す（呼出側で存在確認すること）。
    """
    cur = (start or Path(__file__)).resolve()
    for parent in [cur, *cur.parents]:
        if registry_path(parent).is_file():
            return parent
    return Path.cwd()


def reconfigure_stdout() -> None:
    """Windows 既定 cp932 コンソールでも日本語診断を正しく出力する。"""
    for stream in (getattr(sys, "stdout", None), getattr(sys, "stderr", None)):
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):  # pragma: no cover
                pass


def rel(root: Path, path: Path) -> str:
    """ルートからの相対パス（POSIX 区切り）。表現できないときは絶対パスを返す。"""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()

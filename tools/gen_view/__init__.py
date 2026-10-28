"""gen_view — 節点成果物 .md → 人向け閲覧ビュー (HTML) の変換パッケージ。

`python -m tools.gen_view <source.md>` で単一ファイル HTML を生成する。
生成物は閲覧専用。修正は機読源 (.md/.yaml) へ入れる（単一ソース原則 / FR-3）。
"""

from .render import build_html, main, render_markdown

__all__ = ["main", "render_markdown", "build_html"]

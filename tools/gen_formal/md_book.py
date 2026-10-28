#!/usr/bin/env python3
"""md_book - 機読源 Markdown を「書類モデル」へ解析する（`gen_formal.book` の入力）。

単一ソース（NFR-1）:
  - 正は常に Markdown 側。本モジュールは**読むだけ**で、md を書き換えない。
  - 体裁（結合幅・塗り・罫線）は本モジュールではなく `book.py` が持つ。
    すなわち「何が書いてあるか」と「どう見せるか」を分離する。

解析規則（`docs/00_plan` の成果物 md に共通の書き方）:
  `## N. 見出し`      → 1 節（= 出力の 1 シート候補）
  `### 見出し`        → 節内の小見出し（= 帯）
  `| a | b |`         → 表。区切り行（`|---|`）は捨てる
  ```...```           → 固定幅ブロック（図・式）
  `**(n)** …`         → 番号付き手順。`**(n-m)**` は 1 段下げる
  `- …` / `> …`       → 箇条書き / 注記

使い方（単体で読むことは稀。`book.py` から呼ぶ）:
  from tools.gen_formal.md_book import parse
  doc = parse("tutorial/R60Login/节点2_基本设计/05_承認版_基本设计书.md")
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

__all__ = ["Block", "Sub", "Section", "Doc", "parse"]


# ---------------------------------------------------------------- model


@dataclass
class Block:
    """1 つの塊。`kind` で描き分ける。"""

    kind: str                      # table / text / bullet / quote / code / num
    rows: list[list[str]] = field(default_factory=list)
    text: str = ""
    lines: list[str] = field(default_factory=list)
    indent: int = 0


@dataclass
class Sub:
    """`###` 1 つ分。節の冒頭（`###` より前）は title='' の Sub になる。"""

    title: str
    blocks: list[Block] = field(default_factory=list)


@dataclass
class Section:
    number: str
    title: str
    subs: list[Sub] = field(default_factory=list)

    @property
    def blocks(self) -> list[Block]:
        out: list[Block] = []
        for sub in self.subs:
            out.extend(sub.blocks)
        return out


@dataclass
class Doc:
    title: str
    sections: list[Section] = field(default_factory=list)

    def section(self, number: str) -> Section | None:
        for sec in self.sections:
            if sec.number == number:
                return sec
        return None


# ---------------------------------------------------------------- helpers

_FRONT_MATTER = re.compile(r"^---\s*\n.*?\n---\s*\n", re.S)
_SEP_CELL = re.compile(r"^:?-{2,}:?$")
_SECTION = re.compile(r"^##\s+(\d+)\.\s*(.+?)\s*$")
_SUBSECTION = re.compile(r"^###\s+(.+?)\s*$")
_NUM_STEP = re.compile(r"^\((\d+(?:-\d+)?)\)\s*(.*)$")
_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_ILLEGAL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def clean(text: str) -> str:
    """セルに置ける文字列へ整える（装飾記号を落とし、制御文字を除く）。"""
    s = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    s = s.replace("**", "")
    s = s.replace("`", "")
    s = _LINK.sub(r"\1", s)
    s = s.replace("\\|", "|")
    return _ILLEGAL.sub("", s).strip()


def split_row(line: str) -> list[str]:
    """`| a | b |` → ['a', 'b']。セル内の `\\|` は区切らない。"""
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|"):
        body = body[:-1]
    cells: list[str] = []
    buf: list[str] = []
    escaped = False
    for ch in body:
        if escaped:
            buf.append("|" if ch == "|" else "\\" + ch)
            escaped = False
        elif ch == "\\":
            escaped = True
        elif ch == "|":
            cells.append(clean("".join(buf)))
            buf = []
        else:
            buf.append(ch)
    cells.append(clean("".join(buf)))
    return cells


def _is_separator(cells: list[str]) -> bool:
    real = [c for c in cells if c]
    return bool(real) and all(_SEP_CELL.match(c) for c in real)


# ---------------------------------------------------------------- parse


def parse(path: str | Path) -> Doc:
    """Markdown を読み、`Doc` を返す。ファイルは読むだけで書き換えない。"""
    text = Path(path).read_text(encoding="utf-8")
    text = _FRONT_MATTER.sub("", text, count=1)
    lines = text.split("\n")

    doc = Doc(title="")
    sec: Section | None = None
    sub: Sub | None = None
    table: list[list[str]] = []
    code: list[str] = []
    in_code = False

    def flush_table() -> None:
        nonlocal table
        if table and sub is not None:
            sub.blocks.append(Block(kind="table", rows=table))
        table = []

    def flush_code() -> None:
        nonlocal code
        if code and sub is not None:
            sub.blocks.append(Block(kind="code", lines=code))
        code = []

    for raw in lines:
        line = raw.rstrip()

        if line.startswith("```"):
            if in_code:
                flush_code()
                in_code = False
            else:
                flush_table()
                in_code = True
            continue
        if in_code:
            code.append(line)
            continue

        if not line.strip():
            flush_table()
            continue

        if line.strip() == "---":
            flush_table()
            continue

        m = _SECTION.match(line)
        if m:
            flush_table()
            sec = Section(number=m.group(1), title=clean(m.group(2)))
            sub = Sub(title="")
            sec.subs.append(sub)
            doc.sections.append(sec)
            continue

        if sec is None:
            if line.startswith("# ") and not doc.title:
                doc.title = clean(line[2:])
            continue

        m = _SUBSECTION.match(line)
        if m:
            flush_table()
            sub = Sub(title=clean(m.group(1)))
            sec.subs.append(sub)
            continue

        if sub is None:  # pragma: no cover - 構造上あり得ない
            continue

        if line.lstrip().startswith("|"):
            cells = split_row(line)
            if _is_separator(cells):
                continue
            table.append(cells)
            continue

        flush_table()

        s = line.strip()
        if s.startswith(">"):
            sub.blocks.append(Block(kind="quote", text=clean(s.lstrip(">").strip())))
            continue

        m = _NUM_STEP.match(s)
        if m:
            indent = 1 if "-" in m.group(1) else 0
            sub.blocks.append(Block(kind="num", text="(%s) %s" % (m.group(1), clean(m.group(2))),
                                    indent=indent))
            continue

        if s.startswith("- "):
            sub.blocks.append(Block(kind="bullet", text=clean(s[2:])))
            continue

        sub.blocks.append(Block(kind="text", text=clean(s)))

    flush_table()
    flush_code()
    return doc

"""用語集（`doc_type: glossary`）から中日英の対応を取り、検索語を拡張する。

なぜ要るか
----------
知識の本文は**日本語**である。質問する人は**中国語**で考える。
既定の embedder は文字 n-gram なので、**字面が一致しないと 0 件に近い**（実測：

    排他制御 はどうやっているか      0.1737
    排他控制是怎么做的                0.0677
    并发控制                         0.0189

）。同じ概念でも、使う語が違えば届かない。

やること
--------
用語集の表から `(日本語, 中文, English)` を取り、**質問に含まれる中文・English の語**を
見つけたら、対応する**日本語の語を質問に足す**。索引側は触らない（既存の語彙のまま）。

なぜ索引側を触らないか
----------------------
索引に同義語を混ぜると、後から「なぜこれが当たったのか」が説明できなくなる。
質問を広げるだけなら、**何を足したかを画面に出せる**（透明性が保てる）。

★ 判定はしない。用語集にある対応だけを使う。無い語は広げない。
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

#: 表の見出しから列の役割を決める（表記ゆれを吸収する）。
_JP_HEADS = ("日本語", "用語（原文）", "用語(原文)", "用語", "原文")
_CN_HEADS = ("中文", "中国語", "汉语")
_EN_HEADS = ("english", "英語", "英文")

_SPLIT_CELL = re.compile(r"\|")


def _norm(text: str) -> str:
    return text.strip().strip("*`").strip().lower()


def _head_role(cell: str) -> str | None:
    value = _norm(cell)
    # `用語ID` は見出しに「用語」を含むが、**語そのものではない**（ID 列）。
    # ここを取り違えると「并发控制 → TERM-005」のように ID を足してしまう（実測で発生）。
    if value.startswith(("用語id", "用語 no", "用語no", "id")):
        return None
    if any(value.startswith(_norm(h)) for h in _JP_HEADS):
        return "jp"
    if any(value.startswith(_norm(h)) for h in _CN_HEADS):
        return "cn"
    if any(value.startswith(_norm(h)) for h in _EN_HEADS):
        return "en"
    return None


def parse_tables(text: str) -> list[tuple[str, str, str]]:
    """Markdown の表から (日本語, 中文, English) の三つ組を取り出す。

    見出し行で列の役割を決めるので、列の順序が違っても動く。
    日本語が空の行は捨てる（拡張先が無い）。
    """
    out: list[tuple[str, str, str]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if not lines[i].strip().startswith("|"):
            i += 1
            continue
        block = []
        while i < len(lines) and lines[i].strip().startswith("|"):
            block.append(lines[i])
            i += 1
        if len(block) < 3:
            continue

        heads = [c.strip() for c in _SPLIT_CELL.split(block[0].strip().strip("|"))]
        roles = [_head_role(h) for h in heads]
        if "jp" not in roles:
            continue
        jp_i = roles.index("jp")
        cn_i = roles.index("cn") if "cn" in roles else None
        en_i = roles.index("en") if "en" in roles else None

        for row in block[2:]:
            cells = [c.strip() for c in _SPLIT_CELL.split(row.strip().strip("|"))]
            if len(cells) <= jp_i:
                continue
            jp = cells[jp_i]
            if not jp or jp.startswith("<"):
                continue
            cn = cells[cn_i] if cn_i is not None and cn_i < len(cells) else ""
            en = cells[en_i] if en_i is not None and en_i < len(cells) else ""
            out.append((jp, cn, en))
    return out


def build(conn: sqlite3.Connection, repo_root: Path) -> dict[str, set[str]]:
    """用語集を読み、`{中文または英語の語: {日本語の語}}` を作る。"""
    rows = conn.execute(
        "SELECT doc_id, path FROM kb_doc WHERE doc_type = 'glossary'"
    ).fetchall()
    lexicon: dict[str, set[str]] = {}
    for _doc_id, rel in rows:
        path = repo_root / str(rel)
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for jp, cn, en in parse_tables(text):
            for alias in (cn, en):
                alias = alias.strip()
                if not alias or alias.startswith("<") or alias.lower() == jp.lower():
                    continue
                lexicon.setdefault(alias, set()).add(jp)
    return lexicon


def expand(query: str, lexicon: dict[str, set[str]]) -> tuple[str, list[tuple[str, str]]]:
    """質問に含まれる中文・English の語を、対応する日本語の語で補う。

    Returns:
        (拡張後の質問, [(当たった語, 足した日本語), ...])

    既に質問に入っている語は足さない（重複で順位を歪めない）。
    """
    applied: list[tuple[str, str]] = []
    additions: list[str] = []
    # 長い語から当てる（「排他制御」が「排他」に食われないように）
    for alias in sorted(lexicon, key=len, reverse=True):
        if alias not in query:
            continue
        for jp in sorted(lexicon[alias]):
            if jp in query or jp in additions:
                continue
            additions.append(jp)
            applied.append((alias, jp))
    if not additions:
        return query, []
    return f"{query} {' '.join(additions)}", applied


def _self_test() -> int:
    """表の解析と拡張の最小検証（`用語ID` を語と誤認しないことを含む）。"""
    sample = """
| 用語ID | 用語（原文） | 読み | 中文 | English | 定義 |
|---|---|---|---|---|---|
| TERM-001 | 排他制御 | はいせいせいぎょ | 并发控制 | exclusive control | 新旧を判定する |
| TERM-002 | 引当 | ひきあて | 分配 | allocation | 在庫を確保する |
"""
    triples = parse_tables(sample)
    ok_parse = triples == [
        ("排他制御", "并发控制", "exclusive control"),
        ("引当", "分配", "allocation"),
    ]

    lexicon: dict[str, set[str]] = {}
    for jp, cn, en in triples:
        for alias in (cn, en):
            if alias:
                lexicon.setdefault(alias, set()).add(jp)

    expanded, applied = expand("并发控制 是怎么做的", lexicon)
    ok_expand = "排他制御" in expanded and ("并发控制", "排他制御") in applied
    # 日本語だけの質問は広げない
    jp_query, jp_applied = expand("排他制御について", lexicon)
    ok_noop = jp_query == "排他制御について" and not jp_applied

    ok = ok_parse and ok_expand and ok_noop
    print(f"[synonyms self-test] parse={ok_parse} expand={ok_expand} noop={ok_noop} "
          f"-> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())

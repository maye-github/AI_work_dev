"""見出しベースのチャンク分割。

方針:
  - `#` 見出し階層ごとに 1 セクション = 1 チャンク（長すぎる場合は段落で分割）
  - Markdown の表は「1 行 = 1 チャンク」（ヘッダ行を各チャンクに複写）
  - コードブロックは分割せず 1 チャンク
"""

from __future__ import annotations

import re

HEAD_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
_SEP_CELL_RE = re.compile(r"^\s*\|?[\s:\-|]+\|?\s*$")


def _is_table_start(lines: list[str], i: int) -> bool:
    if i + 1 >= len(lines):
        return False
    head, sep = lines[i].strip(), lines[i + 1].strip()
    return head.startswith("|") and "-" in sep and _SEP_CELL_RE.match(sep) is not None


def _split_long(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    out, buf, size = [], [], 0
    for ln in text.splitlines():
        if len(ln) > max_chars:
            if buf:
                out.append("\n".join(buf))
                buf, size = [], 0
            for k in range(0, len(ln), max_chars):
                out.append(ln[k : k + max_chars])
            continue
        if size + len(ln) + 1 > max_chars and buf:
            out.append("\n".join(buf))
            buf, size = [], 0
        buf.append(ln)
        size += len(ln) + 1
    if buf:
        out.append("\n".join(buf))
    return [x for x in out if x.strip()]


def _emit_section(
    heading: str, lines: list[str], out: list[dict], max_chars: int
) -> None:
    buf: list[str] = []

    def flush() -> None:
        if not buf:
            return
        text = "\n".join(buf).strip()
        del buf[:]
        for piece in _split_long(text, max_chars):
            out.append({"heading": heading, "kind": "para", "text": piece})

    i = 0
    while i < len(lines):
        line = lines[i]
        if _is_table_start(lines, i):
            flush()
            header = lines[i].strip()
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                out.append(
                    {
                        "heading": heading,
                        "kind": "row",
                        "text": f"{header}\n{lines[j].strip()}",
                    }
                )
                j += 1
            i = j
            continue
        m = FENCE_RE.match(line)
        if m:
            flush()
            fence = m.group(1)
            block = [line]
            j = i + 1
            while j < len(lines):
                block.append(lines[j])
                j += 1
                if FENCE_RE.match(lines[j - 1]) and len(block) > 1:
                    break
            out.append({"heading": heading, "kind": "code", "text": "\n".join(block)})
            i = j
            continue
        if not line.strip():
            flush()
            i += 1
            continue
        buf.append(line)
        i += 1
    flush()


def chunk_document(
    body: str, meta: dict | None = None, max_chars: int = 700
) -> list[dict]:
    meta = meta or {}
    title = str(meta.get("title") or "")
    lines = body.splitlines()

    sections: list[tuple[list[str], list[str]]] = []
    path: list[str] = []
    cur: list[str] = []
    for ln in lines:
        m = HEAD_RE.match(ln)
        if m:
            if cur:
                sections.append((list(path), cur))
            level = len(m.group(1))
            path = path[: level - 1] + [m.group(2).strip()]
            cur = []
        else:
            cur.append(ln)
    if cur:
        sections.append((list(path), cur))

    chunks: list[dict] = []
    for heading_path, sec_lines in sections:
        # 本文の H1 は front matter の title と重複するので見出しパスから落とす
        if heading_path and title and heading_path[0] == title:
            heading_path = heading_path[1:]
        heading = " > ".join(heading_path) if heading_path else title
        _emit_section(heading, sec_lines, chunks, max_chars)
    return chunks

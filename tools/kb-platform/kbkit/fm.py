"""front matter / YAML サブセットのパーサ。

PyYAML が無い環境でも動くよう、本プロジェクトで使う範囲だけを実装する:

    key: value
    key: [a, b, c]
    key:
      - item
    - id: x          # リスト・オブ・マップ
      question: ...
"""

from __future__ import annotations

import re
from typing import Any

_INT_RE = re.compile(r"^[-+]?\d+$")
_FLOAT_RE = re.compile(r"^[-+]?\d+\.\d+$")


class YamlError(ValueError):
    pass


def _split_flow(s: str) -> list[str]:
    """`[a, "b,c", [d]]` の中身をトップレベルのカンマで分割する。"""
    out: list[str] = []
    buf: list[str] = []
    depth = 0
    quote: str | None = None
    for ch in s:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
            buf.append(ch)
        elif ch in "[{":
            depth += 1
            buf.append(ch)
        elif ch in "]}":
            depth -= 1
            buf.append(ch)
        elif ch == "," and depth == 0:
            out.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    tail = "".join(buf).strip()
    if tail:
        out.append(tail)
    return out


def parse_scalar(raw: str) -> Any:
    v = raw.strip()
    if v == "":
        return None
    if len(v) >= 2 and v[0] in "\"'" and v[-1] == v[0]:
        return v[1:-1]
    low = v.lower()
    if low in ("null", "~"):
        return None
    if low in ("true", "yes", "on"):
        return True
    if low in ("false", "no", "off"):
        return False
    if v.startswith("[") and v.endswith("]"):
        return [parse_scalar(x) for x in _split_flow(v[1:-1])]
    if _INT_RE.match(v):
        return int(v)
    if _FLOAT_RE.match(v):
        return float(v)
    return v


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _clean(text: str) -> list[str]:
    return [
        ln.rstrip()
        for ln in text.splitlines()
        if ln.strip() and not ln.lstrip().startswith("#")
    ]


def parse(text: str) -> Any:
    lines = _clean(text)
    if not lines:
        return {}
    node, i = _parse_node(lines, 0, _indent(lines[0]))
    if i != len(lines):
        raise YamlError(f"行 {i + 1}: 解釈できない内容です: {lines[i]!r}")
    return node


def _parse_node(lines: list[str], i: int, ind: int) -> tuple[Any, int]:
    if lines[i].strip().startswith("- "):
        return _parse_list(lines, i, ind)
    return _parse_map(lines, i, ind)


def _parse_map(lines: list[str], i: int, ind: int) -> tuple[dict, int]:
    out: dict[str, Any] = {}
    while i < len(lines):
        line = lines[i]
        cur = _indent(line)
        s = line.strip()
        if cur < ind or s.startswith("- "):
            break
        if cur > ind:
            raise YamlError(f"行 {i + 1}: インデントが不正です: {line!r}")
        if ":" not in s:
            raise YamlError(f"行 {i + 1}: 'key: value' を期待しました: {line!r}")
        key, rest = s.split(":", 1)
        key, rest = key.strip(), rest.strip()
        if rest:
            out[key] = parse_scalar(rest)
            i += 1
            continue
        j = i + 1
        if j < len(lines):
            nind = _indent(lines[j])
            if nind > ind or (nind == ind and lines[j].strip().startswith("- ")):
                child, i = _parse_node(lines, j, nind)
                out[key] = child
                continue
        out[key] = None
        i += 1
    return out, i


def _parse_list(lines: list[str], i: int, ind: int) -> tuple[list, int]:
    out: list[Any] = []
    while i < len(lines):
        line = lines[i]
        if _indent(line) != ind:
            break
        s = line.strip()
        if not s.startswith("- "):
            break
        body = s[2:].strip()
        if ":" in body and not body.startswith(("[", '"', "'")):
            item_ind = ind + 2
            cont: list[str] = []
            j = i + 1
            while j < len(lines) and _indent(lines[j]) > ind:
                cont.append(lines[j])
                j += 1
            shift = (_indent(cont[0]) - item_ind) if cont else 0
            if shift > 0:
                cont = [ln[shift:] for ln in cont]
            elif shift < 0:
                cont = [" " * (-shift) + ln for ln in cont]
            sub = [" " * item_ind + body] + cont
            item, _ = _parse_map(sub, 0, item_ind)
            out.append(item)
            i = j
        else:
            out.append(parse_scalar(body))
            i += 1
    return out, i


def split_front_matter(text: str) -> tuple[dict, str]:
    """先頭の `--- ... ---` をメタデータとして分離する。"""
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines()
    if lines[0].strip() != "---":
        return {}, text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            meta = parse("\n".join(lines[1:i]))
            if not isinstance(meta, dict):
                raise YamlError("front matter はマップである必要があります")
            return meta, "\n".join(lines[i + 1:]).lstrip("\n")
    raise YamlError("front matter が '---' で閉じられていません")

"""知識が決めた「形」を成果物が満たしているかを見る（2026-11-09）。

`kb_refs` は「引いたか」しか見ない。ここは「**引いた知識が要求する形になっているか**」を見る。

    py -3 -m tools.kb_local check-constraints --node 2 tutorial/.../05_承認版_基本设计书.md
    py -3 -m tools.kb_local check-constraints --node 5 tutorial/.../节点5_制造

見るもの（`tools/kb-platform/constraints.yaml` が唯一真源）:
  - required_headings … 章節が知識の型どおりか（欠けを名指しする）
  - checks … forbid_regex / require_regex / require_all（SQL の書き方・4 行固定・DELETE 禁止 等）

**内容の正しさは見ない。** 形が合っているかだけを見る（意味は人が読む＝紅線③）。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

CONSTRAINTS = Path("tools/kb-platform/constraints.yaml")
TEXT_SUFFIXES = {".md", ".py", ".ts", ".vue", ".js", ".yaml", ".yml", ".txt"}


def _load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data


def _norm_heading(text: str) -> str:
    """`0. 文書管理` / `１．文書管理` / `文書管理` を同じ形にする。"""
    t = text.strip()
    t = re.sub(r"^[0-9０-９]+(?:\.[0-9０-９]+)*\.?\s*", "", t)
    # 見出しに付いた補足（`（D-201〜D-206）` 等）を落とす
    t = re.sub(r"[（(][^）)]*[）)]\s*$", "", t)
    return t.strip()


def _headings(text: str) -> set[str]:
    out = set()
    for m in re.finditer(r"^#{2,4}\s+(.+?)\s*$", text, re.M):
        out.add(_norm_heading(m.group(1)))
    return out


def _read_target(path: Path, kind: str | None = None) -> str:
    code_only = kind == "code"
    suffixes = ({".py", ".ts", ".vue", ".js"} if code_only else TEXT_SUFFIXES)
    if path.is_dir():
        parts = []
        for f in sorted(path.rglob("*")):
            if f.is_file() and f.suffix in suffixes and "__pycache__" not in f.parts:
                try:
                    parts.append(f.read_text(encoding="utf-8", errors="ignore"))
                except OSError:
                    pass
        return "\n".join(parts)
    return path.read_text(encoding="utf-8", errors="ignore")


def check(node: int, target: Path, constraints_file: Path = CONSTRAINTS) -> dict:
    data = _load(constraints_file)
    conf = (data.get("nodes") or {}).get(node)
    if not conf:
        return {"ok": True, "skipped": True, "problems": [], "node": node}
    text = _read_target(target, conf.get("kind"))
    problems: list[str] = []

    required = conf.get("required_headings") or []
    if required:
        actual = _headings(text)
        missing = []
        for h in required:
            if isinstance(h, dict):
                names = [h.get("name")] + list(h.get("also") or [])
                if not any(n in actual for n in names):
                    missing.append(str(h.get("name")))
            elif h not in actual:
                missing.append(h)
        if missing:
            problems.append(
                "知識が要求する節がない（出所: {0}）: {1}".format(
                    conf.get("source", "?"), ", ".join(missing))
            )

    for chk in conf.get("checks") or []:
        name = chk.get("name", "?")
        kind = chk.get("type")
        msg = chk.get("message", name)
        if kind == "forbid_regex":
            if re.search(chk.get("pattern", ""), text, re.M):
                problems.append(f"[{name}] {msg}")
        elif kind == "require_regex":
            if not re.search(chk.get("pattern", ""), text, re.M):
                problems.append(f"[{name}] {msg}")
        elif kind == "require_all":
            miss = [p for p in chk.get("patterns") or [] if not re.search(p, text, re.M)]
            if miss:
                problems.append(f"[{name}] {msg}（欠け: {', '.join(miss)}）")

    return {"ok": not problems, "skipped": False, "problems": problems, "node": node}


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--node" not in argv or len(argv) < 2:
        print("usage: py -3 -m tools.kb_local check-constraints --node N <file|dir>", file=sys.stderr)
        return 2
    i = argv.index("--node")
    node = int(argv[i + 1])
    rest = [a for j, a in enumerate(argv) if j not in (i, i + 1)]
    if not rest:
        print("usage: py -3 -m tools.kb_local check-constraints --node N <file|dir>", file=sys.stderr)
        return 2
    target = Path(rest[0])
    res = check(node, target)
    if res.get("skipped"):
        print(f"[constraints] 節点 {node} の制約は未定義（skip）")
        return 0
    if res["ok"]:
        print(f"[constraints] 節点 {node}: OK  {target}")
        return 0
    print(f"[constraints] 節点 {node}: NG  {target}")
    for p in res["problems"]:
        print(f"  - {p}")
    return 1

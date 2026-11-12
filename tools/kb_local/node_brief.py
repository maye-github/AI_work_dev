"""節点の「必読条目」を、そのまま AI の入力に同梱できる形で出す。

なぜ要るか
----------
「知識庫を参考にしてください」では参考にならない。AI は自分が知っている一般論で埋める。
**節点ごとに対応する条目を機械的に取り出して、プロンプトへ貼る**——これがこのコマンドの役割である。

    py -3 -m tools.kb_local node-brief --node 5

出すもの（1 条あたり）: doc_id / 題名 / パス / 主要な節の見出しと抜粋（先頭 3 行）。
全文は出さない（文脈を食う）。全文が要るときはパスを開く。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml


def _front(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    try:
        meta = yaml.safe_load(text[3:end]) or {}
    except yaml.YAMLError:
        meta = {}
    return (meta if isinstance(meta, dict) else {}), text[end + 4:]


def _sections(body: str) -> list[tuple[str, list[str]]]:
    out: list[tuple[str, list[str]]] = []
    cur = None
    buf: list[str] = []
    for line in body.splitlines():
        m = re.match(r"^(#{2,3})\s+(.+?)\s*$", line)
        if m:
            if cur is not None:
                out.append((cur, buf))
            cur = m.group(2).strip()
            buf = []
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        out.append((cur, buf))
    return out


def brief(repo: Path, node: int, per_section: int = 3, max_sections: int = 10) -> str:
    from tools.kb_refs import NODE_REQUIRED, load_docs, DEFAULT_DB

    if node not in NODE_REQUIRED:
        return f"（節点 {node} の必読条目は未定義）"
    docs = load_docs(DEFAULT_DB)
    lines = [
        f"## 節点 {node} の必読条目（知識庫から自動同梱）",
        "",
        "以下は**この節点で必ず参照する条目**である。抜粋は見出しと先頭数行に限る。",
        "**実際に使った節を `kb_usage`（doc_id / 節 / 反映先）に記録すること。**",
        "",
    ]
    for doc_id in NODE_REQUIRED[node]:
        info = docs.get(doc_id)
        if not info:
            lines += [f"### {doc_id}", "", "**索引に見つからない（要確認）**", ""]
            continue
        path = repo / info["path"]
        try:
            meta, body = _front(path)
        except OSError:
            lines += [f"### {doc_id}", "", f"**読めない: {info['path']}**", ""]
            continue
        title = meta.get("title") or info.get("title") or doc_id
        lines += [
            f"### {doc_id} — {title}",
            f"path: `{info['path']}`",
            "",
        ]
        secs = _sections(body)[:max_sections]
        if not secs:
            head = [ln for ln in body.splitlines() if ln.strip()][:per_section]
            lines += [f"- {h.strip()}" for h in head] + [""]
            continue
        for name, buf in secs:
            picked = [ln.strip() for ln in buf if ln.strip()][:per_section]
            if not picked:
                continue
            lines.append(f"- **{name}**: " + " / ".join(picked))
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    node = None
    repo = Path("tools/kb-platform/repo")
    if "--node" in argv:
        node = int(argv[argv.index("--node") + 1])
    if "--repo" in argv:
        repo = Path(argv[argv.index("--repo") + 1])
    if node is None:
        print("usage: py -3 -m tools.kb_local node-brief --node N", file=sys.stderr)
        return 2
    print(brief(repo, node))
    return 0

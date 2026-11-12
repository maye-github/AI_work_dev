"""`knowledge/` の条目が「決められた形」になっているかを見る。

なぜ要るか
----------
「AI が sources から知識を作る」工程は、**出力の形が決まっていないと検証できない**。
形がばらばらだと、人は毎回まるごと読み直すことになり、機械は何も確かめられない。

この検査は 4 つだけ見る（内容の正しさは見ない。それは人の仕事＝紅線③）:

1. front matter の必須字段（`source_files` を含む）
2. 本文の 5 節（結論／根拠／適用範囲／未確定／更新条件）
3. `source_files` に挙げた原本が**実在する**か
4. 結論が空でないか、断定を避ける語（たぶん・おそらく…）が混ざっていないか（警告のみ）

**出典の無い知識を許さない**のがこの検査の主目的である（紅線⑤と同じ考え方）。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REQUIRED_KEYS = (
    "doc_id", "scope", "project_id", "title", "doc_type",
    "conf_level", "status", "updated_at", "source_files",
)
REQUIRED_SECTIONS = ("結論", "根拠", "適用範囲", "未確定", "更新条件")
HEDGE_RE = re.compile(r"たぶん|おそらく|恐らく|と思われる|かもしれません|probably|maybe", re.IGNORECASE)

#: 遡及適用の免除（1 行 1 パス・repo からの相対）。**理由を書けないものを足してはならない。**
EXEMPT_FILE = "knowledge_exempt.txt"  # `tools/kb-platform/` からの相対


def _split_front_matter(text: str) -> tuple[dict | None, str]:
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end < 0:
        return None, text
    try:
        meta = yaml.safe_load(text[3:end]) or {}
    except yaml.YAMLError:
        return None, text
    body = text[end + 4:]
    return (meta if isinstance(meta, dict) else None), body


def _sections(body: str) -> set[str]:
    return {m.group(1).strip() for m in re.finditer(r"^##\s+(.+?)\s*$", body, re.M)}


def _section_text(body: str, name: str) -> str:
    m = re.search(rf"^##\s+{re.escape(name)}\s*$(.*?)(?=^##\s+|\Z)", body, re.M | re.S)
    return (m.group(1).strip() if m else "")


def _load_exempt(root: Path) -> set[str]:
    p = root / EXEMPT_FILE
    if not p.is_file():
        return set()
    out = set()
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.add(line)
    return out


def check_file(path: Path, project_dir: Path) -> tuple[list[str], list[str]]:
    """1 ファイルを検査する。返り値は (problems, warnings)。"""
    problems: list[str] = []
    warnings: list[str] = []
    meta, body = _split_front_matter(path.read_text(encoding="utf-8"))
    if meta is None:
        return ["front matter が読めない（`---` で囲む）"], warnings

    for key in REQUIRED_KEYS:
        if key not in meta:
            problems.append(f"必須字段が無い: {key}")

    sources = meta.get("source_files")
    if sources is not None:
        if isinstance(sources, str):
            sources = [sources]
        if not isinstance(sources, list) or not sources:
            problems.append("`source_files` が空（出典の無い知識は許さない）")
        else:
            for s in sources:
                rel = str(s).split("#", 1)[0].strip()
                if not rel:
                    continue
                cand = project_dir / rel
                if not cand.exists():
                    problems.append(f"`source_files` の原本が無い: {rel}")

    secs = _sections(body)
    for name in REQUIRED_SECTIONS:
        if name not in secs:
            problems.append(f"節が無い: `## {name}`")

    conclusion = _section_text(body, "結論")
    if "結論" in secs and not conclusion:
        problems.append("`## 結論` が空")
    if conclusion and HEDGE_RE.search(conclusion):
        warnings.append("`## 結論` に断定を避ける語がある（出典を確かめる）")

    if str(meta.get("status", "")) == "open" and not conclusion:
        problems.append("`status: open` なのに結論が無い")

    return problems, warnings


def check(repo: Path) -> dict:
    root = repo.parent  # tools/kb-platform/repo -> tools/kb-platform
    exempt = _load_exempt(root)
    results = []
    for proj in sorted((repo / "projects").iterdir()) if (repo / "projects").is_dir() else []:
        kdir = proj / "knowledge"
        if not kdir.is_dir():
            continue
        for f in sorted(kdir.glob("*.md")):
            rel = f.relative_to(root).as_posix()
            if rel in exempt:
                results.append({"file": rel, "exempt": True, "problems": [], "warnings": []})
                continue
            problems, warnings = check_file(f, proj)
            results.append({"file": rel, "exempt": False, "problems": problems, "warnings": warnings})
    bad = [r for r in results if r["problems"]]
    return {"results": results, "checked": len(results), "bad": len(bad), "ok": not bad}


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    repo = Path("tools/kb-platform/repo")
    if "--repo" in argv:
        repo = Path(argv[argv.index("--repo") + 1])
    res = check(repo)
    for r in res["results"]:
        if r["exempt"]:
            print(f"SKIP {r['file']}  （適用外: knowledge_exempt.txt）")
        elif r["problems"]:
            print(f"NG   {r['file']}")
            for p in r["problems"]:
                print(f"       - {p}")
        else:
            print(f"OK   {r['file']}")
        for w in r["warnings"]:
            print(f"       ⚠ {w}")
    print(f"\n[knowledge] 検査 {res['checked']} 件 / 不合格 {res['bad']} 件")
    return 0 if res["ok"] else 1

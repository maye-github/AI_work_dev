# -*- coding: utf-8 -*-
"""P3 用の探针：同一批问题，分别打 kb-platform 和 tools/rag，看"哪个模块"被命中。

为什么需要它
------------
`eval` 只给出聚合的 recall/MRR，看不出"串味"（问题里写了 R60Maker，命中的却是别的模块）。
串味要靠"命中模块"这个字段才看得见，所以这里逐题打印前 5 条命中的模块。

题目的唯一来源是 `tools/kb-platform/repo/eval/golden.yaml` 里 `project: P-R60-001` 的那些用例，
不在本脚本里另抄一份（否则题会两边漂移）。

用法
----
    py -3 reports/kb-export/p3_probe.py            # 打表
    py -3 reports/kb-export/p3_probe.py --json f   # 另存机读结果
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = ROOT / "tools/kb-platform/repo/eval/golden.yaml"
KB_REPO = ROOT / "tools/kb-platform/repo"
PROJECT = "P-R60-001"
TOP_K = 5


def _run(cmd: list[str]) -> object:
    out = subprocess.run(
        cmd, cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if out.returncode != 0:
        raise SystemExit(f"命令失败: {' '.join(cmd)}\n{out.stderr[-800:]}")
    return json.loads(out.stdout)


def kb_hits(question: str) -> list[dict]:
    rows = _run(
        [sys.executable, "tools/kb-platform/run.py", "search", question,
         "--repo", str(KB_REPO), "--project", PROJECT, "--top-k", str(TOP_K), "--json"]
    )
    return [{"key": r["doc_id"], "label": f'{r["title"]} § {r["heading"]}'} for r in rows]


def rag_hits(question: str) -> list[dict]:
    rows = _run(
        [sys.executable, "-m", "tools.rag", "query", question, "-k", str(TOP_K), "--json"]
    )
    return [{"key": r["module"], "label": f'{r["chunk_id"]} ({r["title"]})'} for r in rows]


def _norm(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalnum())


def rank_of(hits: list[dict], expect: list[str], loose: bool = False) -> int:
    """第一条"命中期望"的位置（1 起算，0 = 前 5 条都不对）。

    loose=True はモジュール名で照合する（rag 側の key は `R60Maker` のような模块名で、
    期待値は `r60-001-chunks-r60maker` のような doc_id のため、包含で見る）。
    """
    want = [_norm(e) for e in expect]
    for i, h in enumerate(hits, 1):
        got = _norm(h["key"])
        if got in want or (loose and any(got and got in w for w in want)):
            return i
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", dest="json_out", help="机读结果の保存先")
    args = ap.parse_args(argv)

    cases = [c for c in (yaml.safe_load(GOLDEN.read_text(encoding="utf-8")) or [])
             if c.get("project") == PROJECT]

    rows = []
    for c in cases:
        kb = kb_hits(c["question"])
        rg = rag_hits(c["question"])
        rows.append(
            {
                "id": c["id"],
                "question": c["question"],
                "expect": c["expect"],
                "kb_top1": kb[0]["label"] if kb else "",
                "kb_top1_key": kb[0]["key"] if kb else "",
                "kb_rank": rank_of(kb, c["expect"]),
                "rag_top1": rg[0]["label"] if rg else "",
                "rag_top1_key": rg[0]["key"] if rg else "",
                "rag_rank": rank_of(rg, c["expect"], loose=True),
            }
        )

    kb_ok = sum(1 for r in rows if r["kb_rank"] == 1)
    rag_ok = sum(1 for r in rows if r["rag_rank"] == 1)
    print(f"cases={len(rows)}  top1 命中 kb={kb_ok}  rag={rag_ok}\n")
    print("| # | kb top-1 | kb rank | rag top-1 | rag rank |")
    print("|---|---|---:|---|---:|")
    for r in rows:
        print(f'| {r["id"]} | {r["kb_top1"][:60]} | {r["kb_rank"] or "-"} '
              f'| {r["rag_top1"][:50]} | {r["rag_rank"] or "-"} |')

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"\n[probe] 保存: {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

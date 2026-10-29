"""把 `tools/rag` 的 80 题金标，对 **kb-platform 的检索**跑一遍（规格书 §13 KPI⑥ 的口径）。

为什么需要这个
--------------
`tools/rag eval` 测的是 rag 自己的索引——那是尺子测自己。
规格书 §13 KPI⑥「RAG検索のヒット率」要测的是**正本库**（§11.2 组件④ = `tools/kb-platform`）。
两边的金标不能各写一份（会漂移），所以这里直接读 rag 的 `eval/gold-qa.yaml`。

怎么对上号
----------
金标里的 `expected_chunk_ids` 是 rag 的 chunk id（如 `R60Ssk:screen:overview`）。
kb 侧的检索摘要每个小节的第一行就是 `` `R60Ssk:screen:overview` / `screen` ``
（`tools/kb_migrate.py` 的 `write_digest` 生成），所以**命中片段的正文里出现该 id 就算命中**。
这个对应关系是精确的字符串对应，不是模糊匹配。

用法
----
    py -3 -m tools.kb_eval                      # 打表
    py -3 -m tools.kb_eval --json reports/x.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
KB_ROOT = ROOT / "tools" / "kb-platform"
sys.path.insert(0, str(KB_ROOT))

from kbkit import store  # noqa: E402
from kbkit.embedder import get_embedder  # noqa: E402

# 検索は上流 `kbkit.retrieval` を直接使わない。上流は `status = 'active'` 固定で、
# 我々の文書（`open` / `baselined`）が 1 件も拾われないため。
# 差分は `tools/kb_local/` に置き、上流は逐字のまま保つ（`tools/kb-platform/UPSTREAM-SYNC.md`）。
from tools.kb_local.retrieval import search  # noqa: E402

DEFAULT_GOLD = ROOT / "eval" / "gold-qa.yaml"
DEFAULT_DB = KB_ROOT / "data" / "kb.sqlite3"


def load_questions(path: Path) -> list[dict]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    qs = data.get("questions") if isinstance(data, dict) else data
    if not isinstance(qs, list):
        raise SystemExit(f"{path} に questions リストがありません")
    for q in qs:
        if "question" not in q or "expected_chunk_ids" not in q:
            raise SystemExit(f"{path}: {q.get('qid')} に question / expected_chunk_ids がありません")
    return qs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="80 题金标 → kb-platform 检索评测")
    ap.add_argument("--gold", default=str(DEFAULT_GOLD))
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--project", default="P-R60-001")
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--with-module", action="store_true",
                    help="金标の module を検索器に渡す（『呼び出し側がモジュールを知っている』場合の上限）")
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args(argv)

    questions = load_questions(Path(args.gold))
    embedder = get_embedder("hash")
    conn = store.connect(args.db)
    store.init_schema(conn)

    rows: list[dict] = []
    for q in questions:
        hits = search(
            conn, q["question"], embedder,
            project_id=args.project, top_k=args.top_k,
            module=q.get("module") if args.with_module else None,
        )
        expect = list(q["expected_chunk_ids"])
        # 命中判定: 期待 chunk id が取得片段の本文に現れるか（摘要片は先頭に id 行を持つ）
        first = None
        matched_by = None
        for rank, h in enumerate(hits, 1):
            hit_ids = [e for e in expect if e in h["text"]]
            if hit_ids:
                first, matched_by = rank, hit_ids[0]
                break
        # 参考値: 取得 1 位が同じモジュールか。
        # 見るのは doc_id と、片段の先頭行（摘要片は `R60Ssk:screen:overview` の id 行から始まる）。
        # 本文全体を見ないのは、他モジュール名を引用している片を誤って「同じ」と数えないため。
        mod = str(q.get("module") or "").lower()
        head = hits[0]["text"].splitlines()[0] if hits and hits[0]["text"] else ""
        top1_module_ok = bool(hits) and bool(mod) and mod in (hits[0]["doc_id"] + head).lower()
        rows.append({
            "qid": q.get("qid"),
            "module": q.get("module"),
            "question": q["question"],
            "expect": expect,
            "rank": first,
            "matched_by": matched_by,
            "top1_module_ok": top1_module_ok,
            "top1": f'{hits[0]["doc_id"]} § {hits[0]["heading"]}' if hits else "",
        })

    n = len(rows) or 1
    hits = sum(1 for r in rows if r["rank"])
    rr = sum(1.0 / r["rank"] for r in rows if r["rank"])
    mod_ok = sum(1 for r in rows if r["top1_module_ok"])

    by_mod: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_mod[r["module"] or "?"].append(r)

    mode = "module ヒントあり" if args.with_module else "module ヒントなし"
    print(f"gold={len(rows)}  top_k={args.top_k}  "
          f"recall@{args.top_k}={hits / n:.3f}  MRR={rr / n:.3f}  "
          f"top1_module={mod_ok}/{len(rows)}  [{mode}]")
    print()
    for mod in sorted(by_mod):
        rs = by_mod[mod]
        m = len(rs)
        h = sum(1 for r in rs if r["rank"])
        mrr = sum(1.0 / r["rank"] for r in rs if r["rank"]) / m
        print(f"  {mod:<14} n={m:<3} recall={h / m:.3f}  mrr={mrr:.3f}")
    miss = [r for r in rows if not r["rank"]]
    if miss:
        print(f"\n未命中 {len(miss)} 件:")
        for r in miss:
            print(f"  {r['qid']}  {r['question'][:50]}  取得1位={r['top1'][:60]}")

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps({"summary": {"cases": len(rows), "top_k": args.top_k,
                                    "recall": round(hits / n, 4), "mrr": round(rr / n, 4),
                                    "top1_module": mod_ok},
                        "details": rows}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"\n[kb_eval] 保存: {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

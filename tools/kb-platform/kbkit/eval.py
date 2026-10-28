"""ゴールデンセットによる検索品質の評価。"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from kbkit import fm
from kbkit.retrieval import search


def load_golden(path: str | Path) -> list[dict]:
    data = fm.parse(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("cases") or []
    if not isinstance(data, list):
        raise ValueError("golden set はケースのリストである必要があります")
    for i, case in enumerate(data):
        if not isinstance(case, dict) or "question" not in case:
            raise ValueError(f"golden set の {i + 1} 件目に question がありません")
        case.setdefault("id", f"Q{i + 1:03d}")
        expect = case.get("expect") or []
        case["expect"] = [expect] if isinstance(expect, str) else list(expect)
    return data


def evaluate(
    conn: sqlite3.Connection,
    embedder,
    cases: list[dict],
    project_id: str | None = None,
    user_level: int = 30,
    top_k: int = 5,
) -> dict:
    rows: list[dict] = []
    hits = 0
    rr_total = 0.0

    for case in cases:
        pid = case.get("project", project_id)
        results = search(
            conn,
            case["question"],
            embedder,
            project_id=pid,
            user_level=int(case.get("user_level", user_level)),
            top_k=top_k,
        )
        got = [r["doc_id"] for r in results]
        expect = case["expect"]

        first = next(
            (rank for rank, d in enumerate(got, 1) if d in expect), None
        )
        hit = first is not None
        hits += int(hit)
        rr_total += (1.0 / first) if first else 0.0

        rows.append(
            {
                "id": case["id"],
                "question": case["question"],
                "expect": expect,
                "got": got,
                "hit": hit,
                "rank": first,
            }
        )

    n = len(cases) or 1
    return {
        "cases": len(cases),
        "top_k": top_k,
        "recall": round(hits / n, 4),
        "mrr": round(rr_total / n, 4),
        "details": rows,
    }

def format_report(report: dict) -> str:
    lines = [
        f"cases={report['cases']}  top_k={report['top_k']}  "
        f"recall@{report['top_k']}={report['recall']:.3f}  MRR={report['mrr']:.3f}",
        "",
    ]
    for r in report["details"]:
        mark = "OK  " if r["hit"] else "MISS"
        rank = f"rank={r['rank']}" if r["rank"] else "rank=-"
        lines.append(f"{mark} {r['id']} {rank}  {r['question']}")
        if not r["hit"]:
            lines.append(f"       expect={r['expect']}")
            lines.append(f"       got   ={r['got']}")
    return "\n".join(lines)

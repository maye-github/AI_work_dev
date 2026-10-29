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
            module=case.get("module"),
            scope=case.get("scope"),
        )
        got = [r["doc_id"] for r in results]
        expect = case["expect"]

        first = next(
            (rank for rank, d in enumerate(got, 1) if d in expect), None
        )
        hit = first is not None
        hits += int(hit)
        rr_total += (1.0 / first) if first else 0.0

        # 節レベルの判定（2026-10-29 追加）。
        #   doc 単位の的中は「モジュールは合っているが節が違う」を見逃す
        #   （実測: RQ008 は doc 判定で OK だが、答えの節は 9 位だった）。
        #   `expect_heading` を持つケースだけ、見出しの部分一致で節まで判定する。
        sec_expect = case.get("expect_heading") or []
        if isinstance(sec_expect, str):
            sec_expect = [sec_expect]
        sec_hit = None
        sec_rank = None
        if sec_expect:
            wanted = [s.lower() for s in sec_expect]
            for rank, r in enumerate(results, 1):
                if r["doc_id"] not in expect:
                    continue
                h = (r["heading"] or "").lower()
                if any(w in h for w in wanted):
                    sec_hit, sec_rank = True, rank
                    break
            if sec_hit is None:
                sec_hit = False

        rows.append(
            {
                "id": case["id"],
                "question": case["question"],
                "expect": expect,
                "got": got,
                "hit": hit,
                "rank": first,
                "section_hit": sec_hit,
                "section_rank": sec_rank,
                "top1_heading": results[0]["heading"] if results else "",
            }
        )

    n = len(cases) or 1
    sec_rows = [r for r in rows if r["section_hit"] is not None]
    sec_ok = sum(1 for r in sec_rows if r["section_hit"])
    return {
        "cases": len(cases),
        "top_k": top_k,
        "recall": round(hits / n, 4),
        "mrr": round(rr_total / n, 4),
        "section_cases": len(sec_rows),
        "section_recall": round(sec_ok / len(sec_rows), 4) if sec_rows else None,
        "details": rows,
    }

def format_report(report: dict) -> str:
    lines = [
        f"cases={report['cases']}  top_k={report['top_k']}  "
        f"recall@{report['top_k']}={report['recall']:.3f}  MRR={report['mrr']:.3f}",
    ]
    if report.get("section_recall") is not None:
        lines[0] += (
            f"  節recall={report['section_recall']:.3f}"
            f" ({report['section_cases']} 件)"
        )
    lines.append("")
    for r in report["details"]:
        mark = "OK  " if r["hit"] else "MISS"
        rank = f"rank={r['rank']}" if r["rank"] else "rank=-"
        sec = ""
        if r["section_hit"] is not None:
            sec = (
                f"  §OK(rank={r['section_rank']})" if r["section_hit"]
                else "  §MISS"
            )
        lines.append(f"{mark} {r['id']} {rank}{sec}  {r['question']}")
        if not r["hit"]:
            lines.append(f"       expect={r['expect']}")
            lines.append(f"       got   ={r['got']}")
        elif r["section_hit"] is False:
            lines.append(f"       §1位の見出し={r['top1_heading']}")
    return "\n".join(lines)

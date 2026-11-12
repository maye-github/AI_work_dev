"""上流 `kbkit.eval` の評価に、案件の `module` / `scope` と **節レベル判定**を足したもの。

足した理由
----------
- `module` / `scope` … 金標（`repo/eval/golden.yaml`）の案件ケースは `module:` を持つ。
  上流の評価はそれを検索器へ渡さないため、モジュール跨ぎの取り違えが数えられない。
- `expect_heading` … doc 単位の的中は「モジュールは合っているが節が違う」を見逃す
  （実測: RQ008 は doc 判定で OK だが、答えの節は 9 位だった）。
  `expect_heading` を持つケースだけ、見出しの部分一致で節まで判定する。

指標の式（recall / MRR）は上流 `kbkit.eval.evaluate` と同一に保つ。
上流を読むときに「同じ式が 2 か所」と映らないよう、**式を変えるときは両方を見ること**。
"""

from __future__ import annotations

import sqlite3

from tools.kb_local.retrieval import search

__all__ = ["evaluate", "format_report"]


def evaluate(
    conn: sqlite3.Connection,
    embedder,
    cases: list[dict],
    project_id: str | None = None,
    user_level: int = 30,
    top_k: int = 5,
    allowed_projects: set[str] | None = None,
    exclude_derived: bool = False,
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
            allowed_projects=allowed_projects,
            exclude_derived=exclude_derived,
        )
        got = [r["doc_id"] for r in results]
        expect = case["expect"]

        first = next((rank for rank, d in enumerate(got, 1) if d in expect), None)
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
                "module": case.get("module"),
                **_section_result(case, results, expect),
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


def _section_result(case: dict, results: list[dict], expect: list[str]) -> dict:
    """`expect_heading` があるケースだけ、期待見出しに当たった位置を返す。"""
    wanted = case.get("expect_heading") or []
    if isinstance(wanted, str):
        wanted = [wanted]
    if not wanted:
        return {"section_hit": None, "section_rank": None, "top1_heading": ""}

    lowered = [w.lower() for w in wanted]
    for rank, r in enumerate(results, 1):
        if r["doc_id"] not in expect:
            continue
        if any(w in (r["heading"] or "").lower() for w in lowered):
            return {
                "section_hit": True,
                "section_rank": rank,
                "top1_heading": results[0]["heading"] if results else "",
            }
    return {
        "section_hit": False,
        "section_rank": None,
        "top1_heading": results[0]["heading"] if results else "",
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

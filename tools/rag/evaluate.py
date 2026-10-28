# -*- coding: utf-8 -*-
"""Gold-question evaluation for the RAG index."""
from __future__ import annotations

import datetime
import json
import os

import yaml

from .store import search


def load_gold(path):
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if isinstance(data, list):
        questions = data
    elif isinstance(data, dict):
        questions = data.get("questions", [])
    else:
        raise ValueError("gold file must be a list or a mapping with `questions`")
    if not questions:
        raise ValueError("gold file contains no questions: %s" % path)
    for q in questions:
        for key in ("qid", "module", "question", "expected_chunk_ids"):
            if key not in q:
                raise ValueError("gold question missing %s: %r" % (key, q))
    return questions


def _run_one(db_path, q, k, module=None):
    results = search(db_path, q["question"], k=k, module=module)
    got = [r["chunk_id"] for r in results]
    expected = list(q["expected_chunk_ids"])
    ranks = [got.index(cid) + 1 for cid in expected if cid in got]
    first_rank = min(ranks) if ranks else None
    return {
        "qid": q["qid"],
        "module": q["module"],
        "type": q.get("type", "fact"),
        "question": q["question"],
        "expected": expected,
        "got": got,
        "hit": any(cid in got for cid in expected),
        "strict_hit": all(cid in got for cid in expected),
        "first_rank": first_rank,
        "rr": (1.0 / first_rank) if first_rank else 0.0,
        "unsupported": len(results) == 0,
    }


def _aggregate(items):
    n = len(items) or 1
    return {
        "questions": len(items),
        "hit_at_k": round(sum(1 for i in items if i["hit"]) / n, 4),
        "strict_hit_at_k": round(sum(1 for i in items if i["strict_hit"]) / n, 4),
        "mrr": round(sum(i["rr"] for i in items) / n, 4),
        "unsupported_rate": round(sum(1 for i in items if i["unsupported"]) / n, 4),
    }


def evaluate(db_path, gold_path, k=5, report_path=None):
    questions = load_gold(gold_path)

    filtered = [_run_one(db_path, q, k, module=q["module"]) for q in questions]
    unfiltered = [_run_one(db_path, q, k) for q in questions]

    by_module = {}
    for item in filtered:
        by_module.setdefault(item["module"], []).append(item)
    by_type = {}
    for item in filtered:
        by_type.setdefault(item["type"], []).append(item)

    report = {
        "generated_on": datetime.date.today().isoformat(),
        "scope": "teaching",
        "index": os.path.abspath(db_path),
        "gold": gold_path,
        "k": k,
        "gold_count": len(questions),
        "filtered_by_module": _aggregate(filtered),
        "unfiltered": _aggregate(unfiltered),
        "by_module": {m: _aggregate(v) for m, v in sorted(by_module.items())},
        "by_type": {t: _aggregate(v) for t, v in sorted(by_type.items())},
        "questions": filtered,
        "unfiltered_questions": unfiltered,
    }

    if report_path:
        parent = os.path.dirname(report_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(report_path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
    return report


def print_summary(report):
    print("gold questions: %d (k=%d)" % (report["gold_count"], report["k"]))
    for label, agg in (
        ("filtered by module", report["filtered_by_module"]),
        ("unfiltered", report["unfiltered"]),
    ):
        print(
            "%-18s recall@%d=%.3f strict=%.3f mrr=%.3f unsupported=%.3f"
            % (
                label, report["k"], agg["hit_at_k"], agg["strict_hit_at_k"],
                agg["mrr"], agg["unsupported_rate"],
            )
        )
    print("by module (filtered):")
    for module, agg in report["by_module"].items():
        print(
            "  %-14s n=%-3d recall@%d=%.3f strict=%.3f mrr=%.3f"
            % (module, agg["questions"], report["k"], agg["hit_at_k"],
               agg["strict_hit_at_k"], agg["mrr"])
        )
    misses = [q for q in report["questions"] if not q["hit"]]
    if misses:
        print("misses:")
        for q in misses:
            print("  %s expected=%s got=%s" % (q["qid"], q["expected"], q["got"]))

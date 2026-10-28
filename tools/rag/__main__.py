# -*- coding: utf-8 -*-
"""CLI: py -3 -m tools.rag {build,query,eval,stats}"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys

from .evaluate import evaluate, print_summary
from .loader import DEFAULT_CHUNKS_DIR, load_chunks
from .store import build_index, default_db_path, search, stats

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def cmd_build(args):
    scopes = ["teaching", "holdout"] if args.scope == "all" else [args.scope]
    for scope in scopes:
        rows = load_chunks(args.chunks, scope=scope)
        db_path = args.db if (args.db and len(scopes) == 1) else default_db_path(scope)
        build_index(rows, scope=scope, db_path=db_path)
        print("built %-8s chunks=%-3d -> %s" % (scope, len(rows), db_path))
    return 0


def cmd_query(args):
    db_path = args.db or default_db_path(args.scope)
    results = search(db_path, args.query, k=args.k, module=args.module)
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0
    if not results:
        print("no results")
        return 0
    for rank, row in enumerate(results, 1):
        print(
            "%d. %s  [%s/%s]  score=%.4f"
            % (rank, row["chunk_id"], row["module"], row["artifact_type"], row["score"])
        )
        print("   %s" % row["title"])
        print("   %s ; %s" % (row["source_path"], row["source_locator"]))
        if args.text:
            text = row["text"]
            print("   %s" % (text[: args.text] + ("..." if len(text) > args.text else "")))
    return 0


def cmd_bundle(args):
    db_path = args.db or default_db_path(args.scope)
    results = search(db_path, args.query, k=args.k, module=args.module)
    chunks = [
        {
            "chunk_id": r["chunk_id"],
            "artifact_type": r["artifact_type"],
            "title": r["title"],
            "text": r["text"],
            "source_path": r["source_path"],
            "source_locator": r["source_locator"],
            "score": r["score"],
        }
        for r in results
    ]
    chars = sum(len(c["title"]) + len(c["text"]) for c in chunks)
    bundle = {
        "node": args.node,
        "module": args.module,
        "query": args.query,
        "chunks": chunks,
        # Conservative estimate for mixed Japanese/ASCII text; not a tokenizer.
        "token_estimate": (chars * 2 + 2) // 3,
    }
    payload = json.dumps(bundle, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        parent = os.path.dirname(args.out)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(payload)
        print("wrote %d chunks (token_estimate=%d) -> %s"
              % (len(chunks), bundle["token_estimate"], args.out))
    else:
        print(payload, end="")
    return 0


def cmd_eval(args):
    db_path = args.db or default_db_path(args.scope)
    report = evaluate(db_path, args.gold, k=args.k, report_path=args.report)
    print_summary(report)

    overall = report["filtered_by_module"]["hit_at_k"]
    worst = min(
        (agg["hit_at_k"] for agg in report["by_module"].values()), default=1.0
    )
    failed = False
    if overall < args.min_recall:
        print("FAIL overall recall@%d %.3f < %.3f" % (args.k, overall, args.min_recall))
        failed = True
    if worst < args.min_module_recall:
        print("FAIL worst module recall@%d %.3f < %.3f" % (args.k, worst, args.min_module_recall))
        failed = True
    print("overall=%.3f worst_module=%.3f" % (overall, worst))
    return 1 if failed else 0


def cmd_stats(args):
    db_path = args.db or default_db_path(args.scope)
    data = stats(db_path)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="py -3 -m tools.rag")
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="build a SQLite index from chunk JSONL")
    p_build.add_argument("--scope", choices=["teaching", "holdout", "all"], default="teaching")
    p_build.add_argument("--chunks", default=DEFAULT_CHUNKS_DIR)
    p_build.add_argument("--db", help="override database path (single scope only)")
    p_build.set_defaults(func=cmd_build)

    p_query = sub.add_parser("query", help="retrieve chunks")
    p_query.add_argument("query")
    p_query.add_argument("--scope", choices=["teaching", "holdout"], default="teaching")
    p_query.add_argument("--db")
    p_query.add_argument("-k", type=int, default=5)
    p_query.add_argument("--module")
    p_query.add_argument("--json", action="store_true")
    p_query.add_argument("--text", type=int, default=0, help="print first N chars of text")
    p_query.set_defaults(func=cmd_query)

    p_eval = sub.add_parser("eval", help="evaluate against gold questions")
    p_eval.add_argument("--gold", default="eval/gold-qa.yaml")
    p_eval.add_argument("--report", default="reports/rag/eval-latest.json")
    p_eval.add_argument("--scope", choices=["teaching", "holdout"], default="teaching")
    p_eval.add_argument("--db")
    p_eval.add_argument("-k", type=int, default=5)
    p_eval.add_argument("--min-recall", type=float, default=0.80)
    p_eval.add_argument("--min-module-recall", type=float, default=0.75)
    p_eval.set_defaults(func=cmd_eval)

    p_bundle = sub.add_parser("bundle", help="emit a context_bundle.json for one node")
    p_bundle.add_argument("--node", required=True, help="n01..n08")
    p_bundle.add_argument("--module", required=True)
    p_bundle.add_argument("--query", required=True)
    p_bundle.add_argument("--scope", choices=["teaching", "holdout"], default="teaching")
    p_bundle.add_argument("--db")
    p_bundle.add_argument("-k", type=int, default=8)
    p_bundle.add_argument("--out")
    p_bundle.set_defaults(func=cmd_bundle)

    p_stats = sub.add_parser("stats", help="show index metadata")
    p_stats.add_argument("--scope", choices=["teaching", "holdout"], default="teaching")
    p_stats.add_argument("--db")
    p_stats.set_defaults(func=cmd_stats)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python
"""kb-platform の CLI。

    python run.py lint
    python run.py ingest --all
    python run.py search "在庫不足のときのエラーコードは？" --project P-DEMO-001
    python run.py eval
    python run.py stats
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from kbkit import eval as kbeval  # noqa: E402
from kbkit import pipeline, store  # noqa: E402
from kbkit.embedder import get_embedder  # noqa: E402
from kbkit.retrieval import build_context, search  # noqa: E402

ROOT = Path(__file__).resolve().parent
DEFAULT_REPO = ROOT / "repo"
DEFAULT_DB = ROOT / "data" / "kb.sqlite3"
DEFAULT_GOLDEN = ROOT / "repo" / "eval" / "golden.yaml"


def _out(text: str = "") -> None:
    print(text)


def cmd_lint(args) -> int:
    issues = pipeline.lint(args.repo)
    if not issues:
        _out(f"OK  {len(pipeline.collect_docs(args.repo))} 文書に問題ありません")
        return 0
    _out(f"NG  {len(issues)} 件の問題:")
    for issue in issues:
        _out(f"  - {issue}")
    return 1


def cmd_ingest(args) -> int:
    embedder = get_embedder(args.embedder)
    conn = store.connect(args.db)
    store.init_schema(conn)
    report = pipeline.ingest(
        args.repo, conn, embedder,
        changed_only=not args.all, reset=args.reset,
    )
    if args.prune:
        removed = pipeline.prune_deleted(conn, args.repo)
        if removed:
            _out(f"削除: {', '.join(removed)}")
    _out(
        f"追加={report['added']} 更新={report['updated']} "
        f"スキップ={report['skipped']} チャンク={report['chunks']}"
    )
    for err in report["errors"]:
        _out(f"  ERROR {err}")
    s = store.stats(conn)
    _out(f"索引: 文書{s['docs']} / チャンク{s['chunks']} / model={s['emb_models']}")
    return 1 if report["errors"] else 0


def cmd_search(args) -> int:
    embedder = get_embedder(args.embedder)
    conn = store.connect(args.db)
    store.init_schema(conn)
    results = search(
        conn, args.query, embedder,
        project_id=args.project, user_level=args.level, top_k=args.top_k,
        module=args.module, scope=args.scope,
    )
    if args.json:
        _out(json.dumps(results, ensure_ascii=False, indent=2))
        return 0
    if not results:
        _out("ヒットなし")
        return 0
    for i, r in enumerate(results, 1):
        _out(f"{i}. [{r['score']:.4f}] {r['citation']}")
        body = r["text"].replace("\n", " ")
        if len(body) > 140:
            body = body[:140] + "…"
        _out(f"   {body}")
    if args.context:
        _out("\n--- context ---")
        _out(build_context(results))
    return 0


def cmd_eval(args) -> int:
    embedder = get_embedder(args.embedder)
    conn = store.connect(args.db)
    store.init_schema(conn)
    cases = kbeval.load_golden(args.golden)
    report = kbeval.evaluate(
        conn, embedder, cases,
        project_id=args.project, user_level=args.level, top_k=args.top_k,
    )
    if args.json:
        _out(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _out(kbeval.format_report(report))
    ok = report["recall"] >= args.threshold
    _out(f"\nしきい値 recall@{args.top_k} >= {args.threshold}: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def cmd_stats(args) -> int:
    conn = store.connect(args.db)
    store.init_schema(conn)
    _out(json.dumps(store.stats(conn), ensure_ascii=False, indent=2))
    rows = conn.execute(
        "SELECT doc_id, scope, project_id, doc_type, status, conf_level, title "
        "FROM kb_doc ORDER BY scope, doc_id"
    ).fetchall()
    for r in rows:
        _out(f"  {r['doc_id']:<18} {r['scope']:<8} {r['project_id'] or '-':<12} "
             f"{r['doc_type']:<14} L{r['conf_level']}  {r['title']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--db", default=str(DEFAULT_DB))
    common.add_argument("--repo", default=str(DEFAULT_REPO))
    common.add_argument("--embedder", default="hash", choices=["hash", "bge"])

    p = argparse.ArgumentParser(description="kb-platform Phase 0 CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("lint", parents=[common], help="front matter / 配置の検査")
    sp.set_defaults(func=cmd_lint)

    sp = sub.add_parser("ingest", parents=[common], help="差分取り込み")
    sp.add_argument("--all", action="store_true", help="変更なしも再索引")
    sp.add_argument("--reset", action="store_true", help="索引を全消しして作り直す")
    sp.add_argument("--prune", action="store_true", help="消えた文書を索引から削除")
    sp.set_defaults(func=cmd_ingest)

    sp = sub.add_parser("search", parents=[common], help="検索")
    sp.add_argument("query")
    sp.add_argument("--project", default=None, help="案件ID（例: P-DEMO-001）")
    sp.add_argument("--level", type=int, default=30, help="利用者の権限レベル")
    sp.add_argument("--top-k", type=int, default=5)
    sp.add_argument("--module", default=None,
                    help="モジュールで絞る（例: R60Ssk）。doc_id/title の部分一致")
    sp.add_argument("--scope", default=None, choices=["company", "project"],
                    help="会社共通だけ / 案件知識だけ に絞る")
    sp.add_argument("--context", action="store_true", help="LLM 用コンテキストも出力")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_search)

    sp = sub.add_parser("eval", parents=[common], help="ゴールデンセット評価")
    sp.add_argument("--golden", default=str(DEFAULT_GOLDEN))
    sp.add_argument("--project", default=None)
    sp.add_argument("--level", type=int, default=30)
    sp.add_argument("--top-k", type=int, default=5)
    sp.add_argument("--threshold", type=float, default=0.85)
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_eval)

    sp = sub.add_parser("stats", parents=[common], help="索引の状態")
    sp.set_defaults(func=cmd_stats)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

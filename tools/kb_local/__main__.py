"""`tools/kb_local` の CLI。上流 `run.py` の CLI に `--module` / `--scope` と節評価を足したもの。

    py -3 -m tools.kb_local search "..." --project P-R60-001 --module R60Ssk
    py -3 -m tools.kb_local eval
    py -3 -m tools.kb_local lint
    py -3 -m tools.kb_local ingest --prune     # 上流 run.py へそのまま委譲
    py -3 -m tools.kb_local stats              # 同上

なぜ「上流 CLI を使わない」のか
------------------------------
上流の `search` は `status = 'active'` の文書しか拾わず、`lint` は骨架の状態語彙
（`open` / `baselined` / …）を知らない。我々の文書はその語彙で書かれているため、
上流 CLI をそのまま叩くと **検索 0 件・lint NG** になる。差分はこの層だけに置く。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys

from tools.kb_local import _bootstrap
from tools.kb_local._bootstrap import _pipeline, _retrieval  # noqa: F401
from tools.kb_local.evaluation import evaluate, format_report
from tools.kb_local.retrieval import search

VENDOR = _bootstrap.VENDOR
DEFAULT_REPO = VENDOR / "repo"
DEFAULT_DB = VENDOR / "data" / "kb.sqlite3"
DEFAULT_GOLDEN = VENDOR / "repo" / "eval" / "golden.yaml"

#: 上流の実装をそのまま使うコマンド（我々の差分が要らないもの）。
DELEGATED = {"ingest", "stats"}


def _out(text: str = "") -> None:
    print(text)


def _upstream_main(argv: list[str]) -> int:
    """上流 `run.py` の `main()` を、書き換えずに呼ぶ。"""
    spec = importlib.util.spec_from_file_location("kb_upstream_run", VENDOR / "run.py")
    if spec is None or spec.loader is None:
        raise SystemExit(f"上流 CLI を読み込めません: {VENDOR / 'run.py'}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.main(argv)


def cmd_lint(rest: list[str]) -> int:
    """上流 lint を、状態語彙を広げた状態で実行する（出力は上流と同一）。"""
    with _bootstrap.wider_statuses():
        return _upstream_main(["lint", *rest])


def cmd_search(rest: list[str]) -> int:
    from kbkit.embedder import get_embedder
    from kbkit.retrieval import build_context
    from kbkit import store

    ap = argparse.ArgumentParser(prog="tools.kb_local search", description="検索")
    ap.add_argument("query")
    ap.add_argument("--project", default=None, help="案件ID（例: P-R60-001）")
    ap.add_argument("--module", default=None,
                    help="モジュールで絞る（例: R60Ssk）。doc_id / title の部分一致")
    ap.add_argument("--scope", default=None, choices=["company", "project"],
                    help="会社共通だけ / 案件知識だけ に絞る")
    ap.add_argument("--level", type=int, default=30, help="利用者の権限レベル")
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--context", action="store_true", help="LLM 用コンテキストも出力")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--repo", default=str(DEFAULT_REPO))
    ap.add_argument("--embedder", default="hash", choices=["hash", "bge"])
    args = ap.parse_args(rest)

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


def cmd_eval(rest: list[str]) -> int:
    from kbkit import eval as kbeval
    from kbkit import store
    from kbkit.embedder import get_embedder

    ap = argparse.ArgumentParser(prog="tools.kb_local eval", description="ゴールデンセット評価")
    ap.add_argument("--golden", default=str(DEFAULT_GOLDEN))
    ap.add_argument("--project", default=None)
    ap.add_argument("--level", type=int, default=30)
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--threshold", type=float, default=0.85)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--repo", default=str(DEFAULT_REPO))
    ap.add_argument("--embedder", default="hash", choices=["hash", "bge"])
    args = ap.parse_args(rest)

    embedder = get_embedder(args.embedder)
    conn = store.connect(args.db)
    store.init_schema(conn)
    cases = kbeval.load_golden(args.golden)   # 金標の読み方は上流のまま
    report = evaluate(
        conn, embedder, cases,
        project_id=args.project, user_level=args.level, top_k=args.top_k,
    )
    if args.json:
        _out(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _out(format_report(report))
    ok = report["recall"] >= args.threshold
    _out(f"\nしきい値 recall@{args.top_k} >= {args.threshold}: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        _out(__doc__ or "")
        return 0

    cmd, rest = argv[0], argv[1:]
    if cmd in DELEGATED:
        return _upstream_main(argv)
    if cmd == "lint":
        return cmd_lint(rest)
    if cmd == "search":
        return cmd_search(rest)
    if cmd == "eval":
        return cmd_eval(rest)

    _out(f"未知のコマンド: {cmd}\n")
    _out(__doc__ or "")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

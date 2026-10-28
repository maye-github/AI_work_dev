"""`python -m tools.ingest` の CLI。

サブコマンド:
    manifest       取入マニフェストを検証して要約を出す
    secret-gate    機密遮断を実行し secret_evidence.json を書く（路径のみ記録）
    scan           リポジトリを棚卸しし inventory.json を書く（**内容は読まない**）
    id-candidates  発号候補を生成する（全行 approved: false）
    id-apply       人が approved: true と記入した行だけを登録する

`--self-test` は合成フィクスチャで全段を検証する（実案件に触れない）。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import find_root, load_manifest, validate_manifest
from .id_candidates import approved_rows, propose_candidates
from .inventory import build_inventory, merge_by_pgm
from .manifest import MANIFEST_REL, manifest_summary
from .scanner import walk_repo
from .secret_gate import collect_secret_evidence, git_tracked
from .selftest import self_test

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


def _dump_yaml(data, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if yaml is None:  # pragma: no cover
        raise RuntimeError("pyyaml が必要です")
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def _iter_targets(manifest: dict):
    """`(project, repo)` を列挙する。"""
    for project in manifest.get("projects", []):
        for repo in project.get("repos", []):
            yield project, repo


def cmd_manifest(args) -> int:
    data = load_manifest(args.manifest)
    problems = validate_manifest(data)
    print(f"[tools.ingest] manifest: {manifest_summary(data)}")
    if problems:
        for problem in problems:
            print(f"  FAIL  {problem}")
        return 1
    print("  PASS  構造検証")
    return 0


def cmd_secret_gate(args) -> int:
    data = load_manifest(args.manifest)
    problems = validate_manifest(data)
    if problems:
        for problem in problems:
            print(f"  FAIL  {problem}")
        return 1

    out_root = Path(args.root) / data["output_root"]
    globs = data["secret_block_globs"]
    total_blocked = 0

    for project, repo in _iter_targets(data):
        repo_root = Path(project["root"]) / repo["path"]
        if not repo_root.is_dir():
            print(f"  SKIP  {project['project_key']}/{repo['name']}: 不在 {repo_root}")
            continue
        evidence = collect_secret_evidence(repo_root, globs)
        total_blocked += len(evidence["blocked"])
        target = out_root / str(project["project_key"]) / repo["name"] / "secret_evidence.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
        print(
            f"  {project['project_key']}/{repo['name']}: tracking={evidence['tracking']} "
            f"遮断 {len(evidence['blocked'])} 件 → {target}"
        )

    print(f"[tools.ingest] secret-gate: 遮断合計 {total_blocked} 件（値は読んでいない）")
    return 0


def cmd_scan(args) -> int:
    data = load_manifest(args.manifest)
    problems = validate_manifest(data)
    if problems:
        for problem in problems:
            print(f"  FAIL  {problem}")
        return 1

    out_root = Path(args.root) / data["output_root"]
    globs = data["secret_block_globs"]

    for project, repo in _iter_targets(data):
        repo_root = Path(project["root"]) / repo["path"]
        if not repo_root.is_dir():
            print(f"  SKIP  {project['project_key']}/{repo['name']}: 不在 {repo_root}")
            continue
        traversal = project.get("traversal") or {}
        tracked = git_tracked(repo_root)
        evidence = collect_secret_evidence(repo_root, globs, tracked=tracked)
        blocked = {row["path"] for row in evidence["blocked"]}
        entries = walk_repo(
            repo_root,
            include_suffixes=traversal.get("include_suffixes"),
            exclude_dirs=traversal.get("exclude_dirs"),
            max_scan_bytes=int(traversal.get("max_scan_bytes", 524288)),
        )
        inventory = build_inventory(project, repo["name"], entries, blocked)
        target = out_root / str(project["project_key"]) / repo["name"] / "inventory.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")
        print(
            f"  {project['project_key']}/{repo['name']}: {inventory['counts']['files']} ファイル "
            f"(遮断 {inventory['counts']['blocked']}) → {target}"
        )
    return 0


def cmd_id_candidates(args) -> int:
    data = load_manifest(args.manifest)
    problems = validate_manifest(data)
    if problems:
        for problem in problems:
            print(f"  FAIL  {problem}")
        return 1

    out_root = Path(args.root) / data["output_root"]
    for project in data.get("projects", []):
        merged: dict[str, list[str]] = {}
        for repo in project.get("repos", []):
            repo_root = Path(project["root"]) / repo["path"]
            if not repo_root.is_dir():
                continue
            traversal = project.get("traversal") or {}
            entries = walk_repo(
                repo_root,
                include_suffixes=traversal.get("include_suffixes"),
                exclude_dirs=traversal.get("exclude_dirs"),
                max_scan_bytes=int(traversal.get("max_scan_bytes", 524288)),
            )
            for pgm, rels in merge_by_pgm(entries).items():
                merged.setdefault(pgm, []).extend(rels)

        candidates = propose_candidates(merged, project.get("prefix_plan"))
        target = out_root / str(project["project_key"]) / "id_candidates.yml"
        _dump_yaml(candidates, target)
        approved = approved_rows(candidates)
        print(
            f"  {project['project_key']}: 候補 {len(candidates['modules'])} モジュール / "
            f"承認済 {len(approved)} 行 → {target}"
        )
    print("[tools.ingest] id-candidates: 発号は行っていない（全行 approved: false）")
    return 0


def cmd_id_apply(args) -> int:
    """人が承認した行だけを登録する（红线①③の機械化）。

    Phase 1.5 では **書込みを実装しない**。承認行の抽出と表示までを行い、
    実書込みは Phase 2.3（人ゲート G-B2 通過後）に実装する。
    書込みが未実装であることを隠さずに報告する。
    """
    data = load_manifest(args.manifest)
    problems = validate_manifest(data)
    if problems:
        for problem in problems:
            print(f"  FAIL  {problem}")
        return 1

    out_root = Path(args.root) / data["output_root"]
    total = 0
    for project in data.get("projects", []):
        path = out_root / str(project["project_key"]) / "id_candidates.yml"
        if not path.is_file():
            print(f"  SKIP  {project['project_key']}: 候補が未生成 {path}")
            continue
        candidates = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        rows = approved_rows(candidates)
        total += len(rows)
        for row in rows:
            print(f"  APPROVED  {row.get('module')} {row.get('prefix')} -> {row.get('assigned')}")
        if not rows:
            print(f"  {project['project_key']}: 承認行ゼロ（登録対象なし）")

    if total == 0:
        print("[tools.ingest] id-apply: 承認行が無いため何もしない")
        return 0

    print(
        "[tools.ingest] id-apply: 書込みは Phase 2.3（G-B2 承認後）に実装。"
        "本コマンドは現時点で **書込みを行わない**（未実装を隠さない）。"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="tools.ingest", description="trans-cosmos-ai 歴史案件 取入ツール")
    ap.add_argument("--self-test", action="store_true", help="合成フィクスチャで自己検証する")
    ap.add_argument("--root", default=None, help="リポジトリルート（省略時は自動探索）")

    sub = ap.add_subparsers(dest="command")
    default_manifest = str(find_root() / MANIFEST_REL)

    p_manifest = sub.add_parser("manifest", help="マニフェストを検証する")
    p_manifest.add_argument("--manifest", default=default_manifest)
    p_manifest.set_defaults(func=cmd_manifest)

    p_gate = sub.add_parser("secret-gate", help="機密遮断を実行し証跡を書く")
    p_gate.add_argument("--manifest", default=default_manifest)
    p_gate.set_defaults(func=cmd_secret_gate)

    p_scan = sub.add_parser("scan", help="棚卸しを実行し inventory.json を書く")
    p_scan.add_argument("--manifest", default=default_manifest)
    p_scan.set_defaults(func=cmd_scan)

    p_cand = sub.add_parser("id-candidates", help="発号候補を生成する")
    p_cand.add_argument("--manifest", default=default_manifest)
    p_cand.set_defaults(func=cmd_id_candidates)

    p_apply = sub.add_parser("id-apply", help="承認済み行を登録する")
    p_apply.add_argument("--manifest", default=default_manifest)
    p_apply.set_defaults(func=cmd_id_apply)

    return ap


def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv if argv is not None else sys.argv[1:])
    args.root = args.root or str(find_root())

    if getattr(args, "self_test", False):
        ok, failures = self_test()
        return 0 if ok else 1

    if not getattr(args, "command", None):
        ap.print_help()
        return 2

    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

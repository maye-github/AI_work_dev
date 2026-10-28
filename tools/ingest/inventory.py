"""棚卸し結果を業務モジュール（PGM）単位へ併合する。

機密遮断（`secret_gate`）で除外されたファイルは **ここへ到達しない**。
非遮断テキストだけを `trace_check.scan_text` で走査する
（規格の二重実装を避ける。片方だけ更新されると走査漏れが生じる）。
"""

from __future__ import annotations

from pathlib import Path

from .scanner import FileEntry, entries_to_dicts, pgm_of


def merge_by_pgm(entries: list[FileEntry]) -> dict[str, list[str]]:
    """`{pgm: [rel, ...]}` を作る。PGM 不明のものは `_unassigned` へ寄せる。"""
    merged: dict[str, list[str]] = {}
    for entry in entries:
        pgm = pgm_of(entry.rel) or "_unassigned"
        merged.setdefault(pgm, []).append(entry.rel)
    return {pgm: sorted(rels) for pgm, rels in sorted(merged.items())}


def scan_repo_text(
    repo_root: Path,
    entries: list[FileEntry],
    blocked: set[str],
    max_scan_bytes: int = 524288,
    patterns=None,
    root: Path | None = None,
) -> list[dict]:
    """非遮断テキストを機密走査する（gate6 と同じ規格）。

    `blocked` に入っている路径は **読まない**（遮断の意味が無くなるため）。
    """
    from tools.trace_check import scan_text  # 循環 import を避けるため遅延 import

    hits: list[dict] = []
    for entry in entries:
        if entry.rel in blocked or entry.size > max_scan_bytes:
            continue
        path = repo_root / entry.rel
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        hits.extend(scan_text(text, patterns=patterns, rel=entry.rel, root=root))
    return hits


def build_inventory(
    project: dict,
    repo_name: str,
    entries: list[FileEntry],
    blocked: set[str],
) -> dict:
    """1 リポジトリ分の棚卸し成果物（`inventory.json` の内容）を組み立てる。

    **内容は読まない。** path / size / sha1 / kind のみを記録する。
    """
    traversal = project.get("traversal") or {}
    return {
        "project_key": project.get("project_key"),
        "repo": repo_name,
        "root": str(project.get("root", "")),
        "traversal": {
            "include_suffixes": list(traversal.get("include_suffixes") or []),
            "exclude_dirs": list(traversal.get("exclude_dirs") or []),
            "max_scan_bytes": traversal.get("max_scan_bytes", 524288),
        },
        "counts": {
            "files": len(entries),
            "blocked": len(blocked),
            "bytes": sum(e.size for e in entries),
        },
        "files": entries_to_dicts(entries),
        "module_asset_map": merge_by_pgm(entries),
    }

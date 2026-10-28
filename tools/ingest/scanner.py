"""リポジトリ走査（棚卸し）。**棚卸しの段階では内容を読まない。**

内容を読むのは:
  1. 機密遮断（`secret_gate`）が除外しなかったファイルだけ
  2. かつ `max_scan_bytes` 以下のものだけ

「まず全部読んでから判断する」設計にしない。読んだ時点で漏洩は起きている。
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, asdict
from pathlib import Path

# 業務モジュール（PGM）名の抽出。R60AreaController.py → R60Area / R60AreaEdit.vue → R60Area
PGM_RE = re.compile(r"(R60[A-Za-z0-9]+?)(?:Controller|Copy|Create|Edit|Multi|Sup|Mes|Self)?\.(?:py|vue|ts)$")

# 共通基盤（業務モジュールではない）。module_scope から除く。
INFRA_PGMS = frozenset(
    {"R60Common", "R60CSVDownload", "R60Login", "R60User", "R60ServerJobRef"}
)

KIND_BY_SUFFIX = {
    ".py": "python",
    ".vue": "vue",
    ".ts": "typescript",
    ".sql": "sql",
    ".md": "doc",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".txt": "text",
}


@dataclass(frozen=True)
class FileEntry:
    rel: str
    size: int
    sha1: str
    kind: str


def classify(rel: str) -> str:
    return KIND_BY_SUFFIX.get(Path(rel).suffix.lower(), "other")


def hash_file(path: Path, max_bytes: int) -> str:
    """sha1。巨大ファイルは `max_bytes` で打ち切る（同一性判定には十分）。"""
    digest = hashlib.sha1()
    remaining = max_bytes
    with path.open("rb") as handle:
        while remaining > 0:
            chunk = handle.read(min(65536, remaining))
            if not chunk:
                break
            digest.update(chunk)
            remaining -= len(chunk)
    return digest.hexdigest()


def walk_repo(
    repo_root: Path,
    include_suffixes: tuple[str, ...] | list[str] | None = None,
    exclude_dirs: tuple[str, ...] | list[str] | None = None,
    max_scan_bytes: int = 524288,
) -> list[FileEntry]:
    """`repo_root` 配下を棚卸しする。**ファイル内容は読まない**（size と sha1 のみ）。"""
    suffixes = {s.lower() for s in (include_suffixes or ())}
    excluded = set(exclude_dirs or ())
    entries: list[FileEntry] = []

    if not repo_root.is_dir():
        return entries

    for path in sorted(repo_root.rglob("*")):
        if not path.is_file():
            continue
        parts = set(path.relative_to(repo_root).parts)
        if parts & excluded:
            continue
        if suffixes and path.suffix.lower() not in suffixes:
            continue
        try:
            size = path.stat().st_size
            digest = hash_file(path, max_scan_bytes)
        except OSError:
            continue
        rel = path.relative_to(repo_root).as_posix()
        entries.append(FileEntry(rel=rel, size=size, sha1=digest, kind=classify(rel)))

    return entries


def entries_to_dicts(entries: list[FileEntry]) -> list[dict]:
    return [asdict(entry) for entry in entries]


def pgm_of(rel: str) -> str | None:
    """パスから業務モジュール（PGM）名を抽出する。該当しなければ None。"""
    name = Path(rel).name
    if name == "__init__.py":
        return None
    m = PGM_RE.search(name)
    if not m:
        return None
    pgm = m.group(1)
    return None if pgm in INFRA_PGMS else pgm

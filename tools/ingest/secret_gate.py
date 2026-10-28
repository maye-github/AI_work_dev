"""機密遮断（取入の最重要ゲート）。

実測された事実（2026-10-12）:
    歴史案件 `D:/AI_work` の 3 リポジトリは **いずれも git 管理下**であり、
    `.env` 系が **7 路径** 追跡されていた（api 1 / doc 4 / front-end 2）。
    `api/.gitignore` は `*.log` `*.pyc` `__pycache__` しか無視していなかった。
    ＝ **取入側で機械的に遮断しなければ、そのまま取り込まれる**。

方針:
    1. `git ls-files` で追跡路径を得る
    2. `secret_block_globs`（`**/.env` 等）と交差するものを **入力から除外**
    3. 除外した路径を `secret_evidence.json` に記録する（**路径のみ。値は読まない**）
    4. git の追跡状態が **不明な場合は遮断側に倒す**（安全側。漏らすより取りこぼす）

本モジュールは値を一度も読まない。記録するのは路径と一致 glob だけである。
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from fnmatch import fnmatch


def is_blocked(rel: str, globs: list[str] | tuple[str, ...]) -> str | None:
    """`rel` がいずれかの glob に一致すればその glob を返す（非該当は None）。

    `**/.env` は深い階層の `.env` に一致させる必要がある。`fnmatch` は `**` を
    特別扱いしないため、`**/x` を「任意階層の x」として自前で展開する。
    """
    rel = rel.replace("\\", "/")
    name = rel.rsplit("/", 1)[-1]
    for glob in globs:
        g = glob.replace("\\", "/")
        if g.startswith("**/"):
            # 任意階層: ベース名一致、または完全一致
            if fnmatch(name, g[3:]) or fnmatch(rel, g):
                return glob
        elif fnmatch(rel, g) or fnmatch(name, g):
            return glob
    return None


def git_tracked(repo_root: Path) -> set[str] | None:
    """`git ls-files` の結果（POSIX 相対路径の集合）。

    git 不在・非リポジトリ・空リポジトリの場合は **None** を返す
    （＝追跡状態が不明。呼び出し側は遮断側に倒すこと）。
    """
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files", "-z"],
            capture_output=True,
            check=False,
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    raw = proc.stdout.decode("utf-8", errors="surrogateescape")
    files = {p.replace("\\", "/") for p in raw.split("\0") if p}
    return files or None


def collect_secret_evidence(
    repo_root: Path,
    globs: list[str] | tuple[str, ...],
    tracked: set[str] | None = None,
) -> dict:
    """遮断对象の証跡を集める。

    Args:
        repo_root: 対象リポジトリのルート（読むだけ。書き換えない）。
        globs:     遮断 glob（マニフェストの `secret_block_globs`）。
        tracked:   追跡路径の注入点（省略時は `git_tracked`）。
                   self-test はここに合成集合を渡し、git 無しで検証する。

    Returns:
        ``{"tracking": "git" | "unknown", "blocked": [ {path, matched_glob, tracked} ]}``
        値（パスワード・鍵の中身）は **一切含めない**。
    """
    if tracked is None:
        tracked = git_tracked(repo_root)
    tracking_state = "git" if tracked is not None else "unknown"

    if tracked is None:
        # 追跡状態が不明 → 安全側。ディレクトリ上の実ファイルを全部 glob 判定して遮断する。
        candidates: set[str] = set()
        if repo_root.is_dir():
            for path in repo_root.rglob("*"):
                if path.is_file():
                    candidates.add(path.relative_to(repo_root).as_posix())
    else:
        candidates = set(tracked)

    blocked = []
    for rel in sorted(candidates):
        glob = is_blocked(rel, globs)
        if glob is None:
            continue
        blocked.append(
            {
                "path": rel,
                "matched_glob": glob,
                "tracked": tracking_state == "git",
            }
        )

    return {"tracking": tracking_state, "blocked": blocked}


def blocked_set(evidence: dict) -> set[str]:
    return {row["path"] for row in evidence.get("blocked", [])}

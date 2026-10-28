"""取入マニフェスト（`docs/00_registry/ingest-manifest.yml`）の読込と検証。

マニフェストは取入の **唯一の入力**である（NFR-1）。本モジュールは
「人が書いた 1 ファイル」を構造検証するだけで、内容を書き換えない。

鍵名の制約:
    gate1 は front-matter の ``id`` / ``*_id`` / ``*_ids`` / ``ids`` を「ID 宣言」とみなす。
    マニフェストは docs/00_registry 配下のため現状 gate1 の対象外だが、
    将来移動しても野号判定を誘発しないよう、当該鍵名は禁止する。
"""

from __future__ import annotations

import json
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

MANIFEST_REL = "docs/00_registry/ingest-manifest.yml"

REQUIRED_TOP = ("schema_version", "output_root", "secret_block_globs", "projects")
REQUIRED_PROJECT = ("project_key", "root", "repos")
REQUIRED_REPO = ("name", "path", "role")

BANNED_KEYS = ("id", "ids")


def _banned(key: str) -> bool:
    k = str(key)
    return k in BANNED_KEYS or k.endswith("_id") or k.endswith("_ids")


def _walk_keys(node, path=""):
    if isinstance(node, dict):
        for key, value in node.items():
            yield f"{path}{key}"
            yield from _walk_keys(value, f"{path}{key}.")
    elif isinstance(node, list):
        for idx, value in enumerate(node):
            yield from _walk_keys(value, f"{path}[{idx}].")


def load_manifest(path: str | Path) -> dict:
    """マニフェストを読み込む。未検証（検証は `validate_manifest`）。"""
    p = Path(path)
    if yaml is None:  # pragma: no cover
        raise RuntimeError("pyyaml が必要です（NFR-6: 標準ライブラリ + pyyaml のみ）")
    text = p.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"マニフェストの最上位はマッピングである必要があります: {p}")
    return data


def validate_manifest(data: dict) -> list[str]:
    """構造検証。問題の文字列リストを返す（空 = 合格）。例外は投げない。"""
    problems: list[str] = []

    for key in REQUIRED_TOP:
        if key not in data:
            problems.append(f"必須キー欠落: {key}")

    if not isinstance(data.get("secret_block_globs"), list) or not data.get("secret_block_globs"):
        problems.append("secret_block_globs は空でないリストである必要があります（機器遮断が無効化されるため）")

    out_root = data.get("output_root")
    if not isinstance(out_root, str) or not out_root or out_root.startswith(("/", "\\")) or ":" in out_root:
        problems.append("output_root はリポジトリ相対パスである必要があります")

    projects = data.get("projects")
    if not isinstance(projects, list) or not projects:
        problems.append("projects は空でないリストである必要があります")
        projects = []

    seen_keys: set[str] = set()
    for idx, project in enumerate(projects):
        where = f"projects[{idx}]"
        if not isinstance(project, dict):
            problems.append(f"{where} はマッピングである必要があります")
            continue
        for key in REQUIRED_PROJECT:
            if key not in project:
                problems.append(f"{where}: 必須キー欠落 {key}")
        pkey = str(project.get("project_key", ""))
        if not pkey:
            problems.append(f"{where}: project_key が空です")
        elif pkey in seen_keys:
            problems.append(f"{where}: project_key が重複しています: {pkey}")
        else:
            seen_keys.add(pkey)
        if ".." in str(project.get("root", "")):
            problems.append(f"{where}: root に '..' は使えません")
        repos = project.get("repos")
        if not isinstance(repos, list) or not repos:
            problems.append(f"{where}: repos は空でないリストである必要があります")
            continue
        for ridx, repo in enumerate(repos):
            rwhere = f"{where}.repos[{ridx}]"
            if not isinstance(repo, dict):
                problems.append(f"{rwhere} はマッピングである必要があります")
                continue
            for key in REQUIRED_REPO:
                if key not in repo:
                    problems.append(f"{rwhere}: 必須キー欠落 {key}")
            if ".." in str(repo.get("path", "")):
                problems.append(f"{rwhere}: path に '..' は使えません")

    # 禁止鍵（gate1 の野号判定を誘発しないため）
    for keypath in _walk_keys(data):
        leaf = keypath.rstrip(".").rsplit(".", 1)[-1].split("[")[0]
        if _banned(leaf):
            problems.append(f"禁止キー: {keypath}（gate1 が ID 宣言と誤認します）")

    return problems


def manifest_summary(data: dict) -> str:
    """人が読む 1 行要約（CLI 表示用）。"""
    projects = data.get("projects") or []
    parts = []
    for project in projects:
        repos = project.get("repos") or []
        parts.append(f"{project.get('project_key', '?')}({len(repos)} repos)")
    return json.dumps(
        {
            "schema_version": data.get("schema_version"),
            "output_root": data.get("output_root"),
            "secret_block_globs": len(data.get("secret_block_globs") or []),
            "projects": ", ".join(parts),
        },
        ensure_ascii=False,
    )

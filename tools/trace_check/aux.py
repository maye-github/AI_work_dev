"""補助検査（門番ではない）— 封印検査 seal と凍結前整合 freeze。

6 道の門（gate1..gate6）とは別枠である。``stats.gates_run`` は 6 のままで、
本モジュールの検査は ``aux`` / ``aux_checks`` にだけ現れる。

- **seal**: 凍結後に下流成果物が実在資産（絶対パス・物理名・実装ファイル名）を
  引用していないことを検査する。門番の代わりではなく、6 道の後に必ず走る付帯検査。
- **freeze**: 凍結前の内部矛盾検査が実際に処置されたかを機械的に確認する
  （論点の振り分け漏れ、R 類に対する revision_history の欠落）。

設定が無い場合は SKIP（PASS でも FAIL でもない）。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - 環境依存
    yaml = None

# 識別子の境界判定に使う文字。前後がこれらなら「語の一部」とみなして除外する。
_BOUNDARY_RE = re.compile(r"[A-Za-z0-9_-]")
_NUMBER_ROW_RE = re.compile(r"^\|\s*(\d+)\s*\|")


# --------------------------------------------------------------------------
# 共通
# --------------------------------------------------------------------------

def discover_freeze_files(root: Path) -> list[Path]:
    """``reports/drill/<module>/freeze.y(a)ml`` を列挙する（``_archive*`` は除外）。"""
    base = Path(root) / "reports" / "drill"
    if not base.is_dir():
        return []
    out: list[Path] = []
    for path in sorted(base.glob("*/freeze.y*ml")):
        if path.name not in ("freeze.yaml", "freeze.yml"):
            continue
        rel_parts = path.relative_to(root).parts
        if any(part.startswith("_archive") for part in rel_parts):
            continue
        out.append(path)
    return out


def load_freeze(path: Path) -> dict:
    if yaml is None:
        raise RuntimeError("PyYAML が必要")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("freeze.yaml の最上位が mapping ではない")
    return data


def normalize_path(text: str) -> str:
    value = str(text).strip().strip("'\"")
    value = value.replace("\\", "/")
    while len(value) > 1 and value.endswith("/"):
        value = value[:-1]
    return value.casefold()


def scope_aliases(frozen_scope: list[str]) -> list[tuple[str, str]]:
    """``frozen_scope`` の字面と、十分に長い basename の別名を返す。

    戻り値の label は**実パスを出さない**ための固定語である（失敗表示に実在パスを載せない）。
    """
    aliases: list[tuple[str, str]] = []
    for raw in frozen_scope or []:
        literal = normalize_path(raw)
        if not literal:
            continue
        aliases.append((literal, "frozen_scope"))
        base = literal.rsplit("/", 1)[-1]
        if len(base) >= 6 and ("_" in base or "-" in base):
            if base != literal:
                aliases.append((base, "frozen_scope(basename)"))
    return aliases


def _contains_with_boundary(haystack: str, needle: str) -> bool:
    start = 0
    while True:
        index = haystack.find(needle, start)
        if index < 0:
            return False
        end = index + len(needle)
        before = haystack[index - 1] if index > 0 else ""
        after = haystack[end] if end < len(haystack) else ""
        before_bad = bool(before) and bool(_BOUNDARY_RE.match(before))
        after_bad = bool(after) and bool(_BOUNDARY_RE.match(after))
        if not before_bad and not after_bad:
            return True
        start = index + 1


# --------------------------------------------------------------------------
# 封印検査（seal）
# --------------------------------------------------------------------------

def iter_seal_targets(repo: Any, case_ref: str) -> list[Path]:
    """下流成果物だけを返す（台帳・回答鍵・派生ビュー・アーカイブは対象外）。"""
    base = Path(repo.root) / "tutorial" / case_ref
    if not base.is_dir():
        return []
    out: list[Path] = []
    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(base).parts
        if any(part.startswith("_archive") for part in rel_parts):
            continue
        if path.name.endswith(".zh.md"):
            continue
        if path.suffix not in (".md", ".yaml", ".yml"):
            continue
        out.append(path)
    return out


def load_seal_patterns(root: Path, module: str) -> tuple[list[tuple[str, str, re.Pattern]] | None, list[str]]:
    """モジュール固有の識別子パターンを読む。

    戻り値の第 1 要素が ``None`` なら「設定なし（identifier seal は skip）」。
    """
    path = Path(root) / "reports" / "drill" / module / "seal_patterns.local.json"
    if not path.is_file():
        return None, []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [], [f"{module}: seal_patterns.local.json を解析できない: {exc}"]
    if not isinstance(data, dict):
        return [], [f"{module}: seal_patterns.local.json の最上位が object ではない"]

    compiled: list[tuple[str, str, re.Pattern]] = []
    for item in data.get("patterns") or []:
        if not isinstance(item, dict):
            continue
        regex = str(item.get("regex") or "")
        if not regex or regex.startswith("__"):
            continue
        label = str(item.get("label") or "identifier")
        kind = str(item.get("kind") or "identifier")
        try:
            compiled.append((label, kind, re.compile(regex)))
        except re.error as exc:
            return [], [f"{module}: 不正な regex（{label}）: {exc}"]
    return compiled, []


def scan_seal_text(
    text: str,
    *,
    rel: str,
    module: str,
    aliases: list[tuple[str, str]],
    patterns: list[tuple[str, str, re.Pattern]],
) -> list[dict]:
    hits: list[dict] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        lowered = normalize_path(line)
        seen: set[tuple[int, str, str]] = set()
        for needle, label in aliases:
            if _contains_with_boundary(lowered, needle):
                key = (lineno, "path", label)
                if key not in seen:
                    seen.add(key)
                    hits.append({"file": rel, "line": lineno, "module": module, "kind": "path", "label": label})
        for label, kind, regex in patterns:
            if regex.search(line):
                key = (lineno, kind, label)
                if key not in seen:
                    seen.add(key)
                    hits.append({"file": rel, "line": lineno, "module": module, "kind": kind, "label": label})
    return hits


def seal_check(repo: Any) -> dict:
    freeze_files = discover_freeze_files(Path(repo.root))
    if not freeze_files:
        return {
            "pass": True,
            "status": "SKIP",
            "stats": {"modules": 0, "hit_lines": 0, "hits": 0, "identifier_skipped": 0},
            "hits": [],
            "problems": [],
        }

    all_hits: list[dict] = []
    problems: list[str] = []
    modules = 0
    identifier_skipped = 0

    for freeze_path in freeze_files:
        module = freeze_path.parent.name
        try:
            freeze = load_freeze(freeze_path)
        except Exception as exc:  # YAML 解析失敗・PyYAML 不在も含む
            problems.append(f"{module}: freeze.yaml を解析できない: {exc}")
            continue

        case_ref = str(freeze.get("case_ref") or module)
        aliases = scope_aliases(freeze.get("frozen_scope") or [])
        targets = iter_seal_targets(repo, case_ref)
        if not targets:
            problems.append(f"{module}: tutorial/{case_ref} に走査対象が無い")
            continue

        patterns, pattern_problems = load_seal_patterns(Path(repo.root), module)
        problems.extend(pattern_problems)
        if patterns is None:
            identifier_skipped += 1
            patterns = []

        modules += 1
        for path in targets:
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            all_hits.extend(
                scan_seal_text(
                    text,
                    rel=repo.rel(path),
                    module=module,
                    aliases=aliases,
                    patterns=patterns,
                )
            )

    hit_lines = len({(hit["file"], hit["line"]) for hit in all_hits})
    failed = bool(all_hits) or bool(problems)
    return {
        "pass": not failed,
        "status": "FAIL" if failed else "PASS",
        "stats": {
            "modules": modules,
            "hit_lines": hit_lines,
            "hits": len(all_hits),
            "identifier_skipped": identifier_skipped,
        },
        "hits": all_hits[:100],
        "problems": problems,
    }


# --------------------------------------------------------------------------
# 凍結前整合（freeze）
# --------------------------------------------------------------------------

def _markdown_tables(text: str) -> list[dict]:
    """``|`` で始まる連続行を表として返す。行番号は 1 起步。"""
    lines = text.splitlines()
    tables: list[dict] = []
    index = 0
    while index < len(lines):
        if not lines[index].lstrip().startswith("|"):
            index += 1
            continue
        start = index
        block: list[tuple[int, str]] = []
        while index < len(lines) and lines[index].lstrip().startswith("|"):
            block.append((index + 1, lines[index]))
            index += 1
        if len(block) < 2:
            continue
        header = [cell.strip() for cell in block[0][1].strip().strip("|").split("|")]
        body = block[2:] if re.match(r"^\s*\|[\s:|-]+\|\s*$", block[1][1]) else block[1:]
        rows: list[tuple[int, list[str]]] = []
        for lineno, line in body:
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            rows.append((lineno, cells))
        tables.append({"header": header, "rows": rows, "start": start + 1})
    return tables


def parse_disposition_table(text: str) -> tuple[list[int], dict[int, str], str | None]:
    """``振り分け`` 列を持つ表を読み、論点番号と振り分けを返す。"""
    for table in _markdown_tables(text):
        header = table["header"]
        disposition_index = None
        for position, cell in enumerate(header):
            if "振り分け" in cell:
                disposition_index = position
                break
        if disposition_index is None:
            continue

        issues: list[int] = []
        dispositions: dict[int, str] = {}
        for lineno, cells in table["rows"]:
            if not cells:
                continue
            match = re.match(r"^\**\s*(\d+)\s*\**$", cells[0])
            if not match:
                continue
            number = int(match.group(1))
            issues.append(number)
            if disposition_index < len(cells):
                dispositions[number] = cells[disposition_index].strip()
        return issues, dispositions, None
    return [], {}, "振り分け列を持つ表が見つからない"


def _module_dirs(repo: Any, module: str) -> list[Path]:
    base = Path(repo.root) / "tutorial" / module
    return sorted(path for path in base.glob("节点1_*") if path.is_dir()) if base.is_dir() else []


def _count_r_defects(repo: Any, module: str) -> int:
    comparison = Path(repo.root) / "reports" / "drill" / module / "comparison.md"
    if not comparison.is_file():
        return 0
    count = 0
    for line in comparison.read_text(encoding="utf-8").splitlines():
        if _NUMBER_ROW_RE.match(line) and "**R**" in line:
            count += 1
    return count


def _valid_revision_entries(freeze: dict) -> int:
    entries = freeze.get("revision_history") or []
    if not isinstance(entries, list):
        return 0
    return sum(1 for entry in entries if isinstance(entry, dict) and str(entry.get("reason") or "").strip())


def freeze_readiness_check(repo: Any) -> dict:
    freeze_files = discover_freeze_files(Path(repo.root))
    if not freeze_files:
        return {
            "pass": True,
            "status": "SKIP",
            "stats": {"modules": 0, "issues": 0, "dispositions": 0, "r_defects": 0},
            "problems": [],
            "modules": [],
        }

    problems: list[str] = []
    details: list[dict] = []
    totals = {"issues": 0, "dispositions": 0, "r_defects": 0, "revision_entries": 0}

    for freeze_path in freeze_files:
        module = freeze_path.parent.name
        try:
            freeze = load_freeze(freeze_path)
        except Exception as exc:  # YAML 解析失敗・PyYAML 不在も含む
            problems.append(f"{module}: freeze.yaml を解析できない: {exc}")
            continue

        interrogation = Path(repo.root) / "reports" / "drill" / module / "interrogation.md"
        issues: list[int] = []
        dispositions: dict[int, str] = {}
        source = None
        if not interrogation.is_file():
            problems.append(f"{module}: {repo.rel(interrogation)} が無い")
        else:
            issues, dispositions, error = parse_disposition_table(interrogation.read_text(encoding="utf-8"))
            if error:
                problems.append(f"{module}: interrogation.md: {error}")
            source = repo.rel(interrogation)

        if not any(value for value in dispositions.values()):
            # 旧版の互換: 節点1 の 02 §4 に振り分けが書かれている場合がある。
            fallback_found = False
            for node_dir in _module_dirs(repo, str(freeze.get("case_ref") or module)):
                candidate = node_dir / "02_確認事項一覧.md"
                if not candidate.is_file():
                    continue
                f_issues, f_dispositions, _ = parse_disposition_table(candidate.read_text(encoding="utf-8"))
                if any(value for value in f_dispositions.values()):
                    issues, dispositions = f_issues, f_dispositions
                    source = repo.rel(candidate)
                    fallback_found = True
                    break
            if not fallback_found:
                problems.append(f"{module}: 振り分け（①/②/③）が 1 件も記入されていない")

        missing = [str(number) for number in issues if not str(dispositions.get(number, "")).strip()]
        if missing:
            problems.append(f"{module}: 振り分け未記入の論点: {', '.join(missing)}")

        r_defects = _count_r_defects(repo, module)
        revision_entries = _valid_revision_entries(freeze)
        if r_defects > revision_entries:
            problems.append(
                f"{module}: R 類 {r_defects} 件に対し revision_history の理由付き項目が "
                f"{revision_entries} 件しかない"
            )

        totals["issues"] += len(issues)
        totals["dispositions"] += len([d for d in dispositions.values() if str(d).strip()])
        totals["r_defects"] += r_defects
        totals["revision_entries"] += revision_entries
        details.append(
            {
                "module": module,
                "source": source,
                "issues": len(issues),
                "dispositions": len([d for d in dispositions.values() if str(d).strip()]),
                "r_defects": r_defects,
                "revision_entries": revision_entries,
            }
        )

    failed = bool(problems)
    return {
        "pass": not failed,
        "status": "FAIL" if failed else "PASS",
        "stats": {"modules": len(freeze_files), **totals},
        "problems": problems,
        "modules": details,
    }

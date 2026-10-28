#!/usr/bin/env python3
"""gen_excel - 機読源から日文正式 Excel の列定義を生成する（Phase1: dry-run）。

単一ソース（NFR-1）:
  発番元 = docs/00_registry/ids.yml
  詳細定義元 = docs/30_detail_design/D-043-R60Area.yaml（存在すれば物理名を優先取得）

使い方:
  python -m tools.gen_formal.gen_excel --dry-run --module R-101
  → [gen_formal] field_count=56 | output_columns=ara_cmp_list_56_items.csv
  → reports/gen_formal_columns_R101.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

from ..paths import find_root

MODULE_CHOICES = ("R-101",)


# リポジトリルートの上方探索は tools/paths.py が唯一の実装である
# （かつて trace_check / gen_formal / ingest が同じ関数を 3 つ持っていた）。
_find_root = find_root


def _camel_to_snake(name: str) -> str:
    """cmpCd -> CMP_CD / ksnDat -> KSN_DAT / araRnm -> ARA_RNM"""
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name)
    s = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", "_", s)
    return s.upper()


def _load_registry(root: Path) -> dict:
    if yaml is None:
        raise RuntimeError("pyyaml が必要です: pip install pyyaml")
    path = root / "docs" / "00_registry" / "ids.yml"
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _load_detail_physical_names(root: Path) -> dict[str, str]:
    """D-043-R60Area.yaml があれば I-ID -> 物理列名 の対応を取得（単一ソース優先）。"""
    path = root / "docs" / "30_detail_design" / "D-043-R60Area.yaml"
    if not path.is_file() or yaml is None:
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            doc = yaml.safe_load(fh) or {}
    except Exception:  # pragma: no cover
        return {}
    out: dict[str, str] = {}
    for item in (doc.get("io_definitions") or doc.get("item_definitions") or []):
        if isinstance(item, dict) and item.get("item_id"):
            out[str(item["item_id"])] = str(item.get("physical_name") or "")
    return out


def field_columns(module: str = "R-101", root: Path | None = None) -> list[str]:
    """指定モジュールの正式 Excel 列名（大文字スネーク）を順番どおり返す。"""
    root = root or _find_root()
    registry = _load_registry(root)
    ids = registry.get("ids") or {}
    physical = _load_detail_physical_names(root)

    columns: list[str] = []
    for key in sorted(ids, key=_id_sort_key):
        if not re.match(r"^I-\d+$", key):
            continue
        entry = ids[key] or {}
        column = physical.get(key) or _camel_to_snake(str(entry.get("name", key)))
        columns.append(column)
    return columns


def _id_sort_key(key: str):
    m = re.match(r"^([A-Z]+)-(\d+)$", key)
    return (m.group(1), int(m.group(2))) if m else (key, 0)


def dry_run(module: str = "R-101", root: Path | None = None) -> dict:
    root = root or _find_root()
    columns = field_columns(module, root)
    out_name = f"ara_cmp_list_{len(columns)}items.csv"
    print(f"[gen_formal] field_count={len(columns)} | output_columns={out_name}")

    report_dir = root / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "gen_formal_columns_R101.json"
    payload = {
        "module": module,
        "field_count": len(columns),
        "output_columns": out_name,
        "columns": columns,
        "source": "docs/00_registry/ids.yml (I-ID) / docs/30_detail_design/D-043-R60Area.yaml (physical)",
        "phase": "Phase1 dry-run only - 実 .xlsx は生成しない",
    }
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[gen_formal] columns -> reports/{report_path.name}")
    return payload


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="gen_formal", description="機読源 → 日文 Excel 列定義（Phase1 dry-run）")
    ap.add_argument("--dry-run", action="store_true", help="列数のみ検証（既定動作）")
    ap.add_argument("--module", default="R-101", choices=MODULE_CHOICES)
    ap.add_argument("--root")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve() if args.root else _find_root()
    payload = dry_run(args.module, root)
    return 0 if payload["field_count"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())

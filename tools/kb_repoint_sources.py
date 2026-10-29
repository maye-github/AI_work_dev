"""chunk の `source_path` を、実際に開ける場所へ付け替える（一回限りの修復器）。

なぜ要るか
----------
2026-10-29 に旧案件の 76 件を `docs/95_legacy/r60/` から
`tools/kb-platform/repo/projects/P-R60-001/` へ移したが、**7 本の JSONL の
`source_path` は移設前のパスのまま**だった。実測では 344 chunk のうち
**1 本も盤上に存在しない**（`os.path.exists` → 0/344）。

二種類ある
----------
1. **移設で壊れたもの**（`docs/95_legacy/r60/…`）— 移設先へ機械的に付け替えられる。
   接頭辞を差し替えるだけで、344 中の 201 件がそのまま実在パスになる（検証済み）。
2. **元から外部のもの**（旧案件の実装・Excel 抽出物・A/B レポート）— それらは
   `D:\\AI_work` 側の資産で、本リポジトリには存在しない。**壊れたのではなく外にある。**

そこで `source_kind` を足す:

- `repo`     … 本リポジトリ内のパス。そのまま開ける。
- `external` … 旧案件側のパス。本リポジトリには無い（出典の記録として残す）。

`text` には触らないので `sha256` は変わらない（loader の検証もそのまま通る）。

使い方
------
    py -3 -m tools.kb_repoint_sources            # 何が変わるかだけ表示
    py -3 -m tools.kb_repoint_sources --apply    # 書き戻す（冪等）
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHUNKS = ROOT / "tools" / "kb-platform" / "repo" / "projects" / "P-R60-001" / "chunks" / "raw"

OLD_PREFIX = "docs/95_legacy/r60/"
NEW_PREFIX = "tools/kb-platform/repo/projects/P-R60-001/"


def repoint(row: dict) -> dict:
    """1 chunk を付け替えて返す（元のキー順を保ち、source_path の直後に source_kind）。"""
    out = {}
    for k, v in row.items():
        if k == "source_kind":
            continue  # 既存があれば付け直す
        out[k] = v
        if k == "source_path":
            if isinstance(v, str) and v.startswith(OLD_PREFIX):
                out["source_path"] = NEW_PREFIX + v[len(OLD_PREFIX):]
                out["source_kind"] = "repo"
            elif isinstance(v, str) and v.startswith(NEW_PREFIX):
                out["source_kind"] = "repo"   # 既に移設先（再実行時）
            else:
                out["source_kind"] = "external"
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="chunk の source_path を開ける場所へ付け替える")
    ap.add_argument("--apply", action="store_true", help="実際に書き戻す（既定は dry-run）")
    ap.add_argument("--chunks", default=str(CHUNKS))
    args = ap.parse_args(argv)

    cdir = Path(args.chunks)
    files = sorted(cdir.glob("*.jsonl"))
    if not files:
        raise SystemExit(f"JSONL が見つかりません: {cdir}")

    total = moved = ext = missing = 0
    per_file: list[str] = []

    for path in files:
        rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
        new_rows = []
        f_moved = f_ext = f_missing = 0
        for r in rows:
            n = repoint(r)
            total += 1
            if n["source_kind"] == "repo":
                moved += 1
                f_moved += 1
                if not (ROOT / n["source_path"]).exists():
                    missing += 1
                    f_missing += 1
            else:
                ext += 1
                f_ext += 1
            new_rows.append(n)

        per_file.append(
            f"  {path.stem:<14} 全{len(rows):>3}  repo={f_moved:>3}  external={f_ext:>3}"
            + (f"  ★未解決={f_missing}" if f_missing else "")
        )
        if args.apply:
            body = "\n".join(
                json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in new_rows
            ) + "\n"
            path.write_text(body, encoding="utf-8", newline="\n")

    print(f"[kb_repoint] {'適用' if args.apply else 'dry-run（--apply で書き戻し）'}")
    print("\n".join(per_file))
    print(f"\n  合計 {total} chunk : repo={moved}  external={ext}  未解決={missing}")
    if missing:
        print("  ★ repo 扱いにしたが盤上に無いものがある。接頭辞の対応を確認すること。")
    return 0 if missing == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

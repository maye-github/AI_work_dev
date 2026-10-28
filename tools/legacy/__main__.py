#!/usr/bin/env python3
"""`python -m tools.legacy.xlsx_text` の CLI。

使い方:
  py -3 -m tools.legacy <file.xlsx>                     # 全シート（既定は非空セルのみ）
  py -3 -m tools.legacy <file.xlsx> --list              # シート名と規模だけ
  py -3 -m tools.legacy <file.xlsx> --sheet 画面項目内容   # 1 シートだけ
  py -3 -m tools.legacy <file.xlsx> --grid              # タブ区切りの格子で出す
  py -3 -m tools.legacy <file.xlsx> --out out.txt       # 1 ファイルへ連結
  py -3 -m tools.legacy <file.xlsx> --out dir --split   # 1 シート 1 ファイル
  py -3 -m tools.legacy <file.xlsx> --out out.txt --mask  # 外へ出す前に脱敏
  py -3 -m tools.legacy --self-test                     # 合成フィクスチャで自己検証

既定が「非空セルのみ」である理由:
  設計書のシートは 1 つの論理セルが横に何十列も結合されている。格子で出すと
  「同じ値が 20 個並ぶ」だけで読めない。空セルを落とすと 1 行 = 1 レコードになる。

安全則:
  - 出力先が読み取り専用領域（`D:/AI_work` 等）の内側なら、書く前に拒否する。
  - `--mask` で辞書が無い場合は、**未マスクのまま出力せず停止する**（紅线⑦）。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from tools.paths import find_root, reconfigure_stdout

from . import xlsx_text
from .selftest import self_test

_UNSAFE_FILENAME = re.compile(r'[\\/:*?"<>|\s]+')


def _safe_stem(name: str, fallback: str) -> str:
    cleaned = _UNSAFE_FILENAME.sub("_", name).strip("_")
    return cleaned or fallback


def _print_list(path: Path) -> int:
    names = xlsx_text.sheet_names(path)
    print(f"{path}  シート数={len(names)}")
    for i, name in enumerate(names):
        head = xlsx_text.sheet_text(path, index=i).split("\n", 1)[0]
        print(f"  [{i}] {name}\t{head.lstrip('# ')}")
    return 0


def _emit(texts: list[tuple[str, str]], args, root: Path) -> int:
    """`[(シート名, 本文)]` を出力する。"""
    if args.mask:
        texts = [(name, xlsx_text.mask_text_with(body, root)) for name, body in texts]

    if not args.out:
        for i, (_, body) in enumerate(texts):
            if i:
                print()
            print(body)
        return 0

    if args.split:
        out_dir = xlsx_text.guard_output(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        for i, (name, body) in enumerate(texts):
            target = xlsx_text.guard_output(out_dir / f"{i:02d}_{_safe_stem(name, f'sheet{i}')}.txt")
            target.write_text(body + "\n", encoding="utf-8")
            print(f"  書出 {target}  ({len(body.splitlines())} 行)", file=sys.stderr)
        return 0

    target = xlsx_text.guard_output(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n\n".join(body for _, body in texts) + "\n", encoding="utf-8")
    print(f"  書出 {target}  ({len(texts)} シート)", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    reconfigure_stdout()

    parser = argparse.ArgumentParser(
        prog="tools.legacy.xlsx_text",
        description="歴史案件の .xlsx を標準ライブラリだけでテキスト化する（読み取り専用）",
    )
    parser.add_argument("path", nargs="?", help="対象の .xlsx")
    parser.add_argument("--list", action="store_true", help="シート名と行数だけを出す")
    parser.add_argument("--sheet", help="シート名で 1 枚だけ選ぶ")
    parser.add_argument("--sheet-index", type=int, help="シート番号（0 起点）で 1 枚だけ選ぶ")
    parser.add_argument("--out", help="出力先（--split 併用時はディレクトリ）")
    parser.add_argument("--split", action="store_true", help="1 シート 1 ファイルで書き出す")
    parser.add_argument("--mask", action="store_true", help="出力前に脱敏する（紅线⑦）")
    parser.add_argument("--grid", action="store_true", help="タブ区切りの格子で出す（既定は非空セルのみ）")
    parser.add_argument("--fill-merge", action="store_true",
                        help="--grid のとき結合セルの左上値を範囲へ複製する（既定は複製しない）")
    parser.add_argument("--show-merge", action="store_true", help="結合範囲の一覧を先頭に注記する")
    parser.add_argument("--self-test", action="store_true", help="合成フィクスチャで自己検証する")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    if args.self_test:
        ok, failures = self_test()
        if ok:
            print("[tools.legacy] self-test: 全項目 PASS")
            return 0
        for failure in failures:
            print(f"  FAIL  {failure}")
        return 1

    if not args.path:
        parser.print_help()
        return 2

    # --split は「1 シート 1 ファイルをディレクトリへ」の意。ファイル名を渡すと
    # その名前のディレクトリが黙って出来る（実際に踏んだ）。先に弾く。
    if args.split and not args.out:
        parser.error("--split には --out <ディレクトリ> が必要です")
    if args.split and Path(args.out).suffix:
        parser.error(
            f"--split の --out はディレクトリでなければなりません（ファイル名に見えます）: {args.out}"
        )
    if args.fill_merge and not args.grid:
        parser.error("--fill-merge は --grid と併用してください（疎表示は結合を複製しません）")
    if args.fill_merge:
        args.show_merge = True  # 複製したら、どの範囲を複製したか必ず分かるようにする

    path = Path(args.path)
    try:
        if args.list:
            return _print_list(path)

        kwargs = {
            "mode": "grid" if args.grid else "sparse",
            "fill_merges": bool(args.fill_merge),
            "show_merge": bool(args.show_merge),
        }
        if args.sheet is not None:
            texts = [(args.sheet, xlsx_text.sheet_text(path, sheet=args.sheet, **kwargs))]
        elif args.sheet_index is not None:
            texts = [(str(args.sheet_index),
                      xlsx_text.sheet_text(path, index=args.sheet_index, **kwargs))]
        else:
            texts = [
                (name, xlsx_text.sheet_text(path, index=i, **kwargs))
                for i, name in enumerate(xlsx_text.sheet_names(path))
            ]

        return _emit(texts, args, find_root())
    except xlsx_text.LegacyToolError as exc:
        print(f"  ERROR  {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

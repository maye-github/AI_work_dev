#!/usr/bin/env python3
"""selftest - tools/legacy の自己検証（合成フィクスチャ・実案件に触れない）。

合成した .xlsx を**メモリ上で**組み立てて検証する。`D:/AI_work` は一切読まない。
検証する性質:
  1. シート名の列挙順がワークブック定義順である
  2. `<rPh>`（振仮名）が本文へ混入しない     ← 素朴な実装が最も踏み抜く罠
  3. リッチテキストの run が連結される
  4. inlineStr / 数値 / 実体参照 / セル内改行 が読める
  5. 疎表示で空セルが落ち、列記号が実際の位置を指す
  6. 格子表示で行列位置が保たれ、結合の複製は opt-in でのみ起きる
  7. 異常系（存在しないシート / 範囲外 / 非 zip）が明確な例外になる
  8. 書き込みガードが読み取り専用領域を拒否する
"""

from __future__ import annotations

import io
import tempfile
import zipfile
from pathlib import Path

from .xlsx_text import (
    LegacyToolError,
    ReadOnlyViolation,
    guard_output,
    read_workbook,
    sheet_names,
    sheet_text,
    workbook_text,
)

# ---------------------------------------------------------------------------
# 合成フィクスチャ（実在の業務データではない。構造の検証専用）
# ---------------------------------------------------------------------------

_NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_NS_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
_NS_OR = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

_WORKBOOK = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="{_NS_MAIN}" xmlns:r="{_NS_OR}"><sheets>
<sheet name="明細" sheetId="1" r:id="rId1"/>
<sheet name="空" sheetId="2" r:id="rId2"/>
</sheets></workbook>"""

_RELS = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{_NS_REL}">
<Relationship Id="rId1" Type="{_NS_OR}/worksheet" Target="worksheets/sheet1.xml"/>
<Relationship Id="rId2" Type="{_NS_OR}/worksheet" Target="worksheets/sheet2.xml"/>
</Relationships>"""

# si1 にルビ（<rPh>）を仕込む。素朴に <t> を全部集めると「機能概要キノウガイヨウ」になる。
_SHARED = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<sst xmlns="%s" count="5" uniqueCount="5">
<si><t>会社コード</t></si>
<si><t>機能概要</t><rPh sb="0" eb="4"><t>キノウガイヨウ</t></rPh>
<phoneticPr fontId="1" type="katakana"/></si>
<si><r><rPr><b/></rPr><t>あ</t></r><r><t>い</t></r></si>
<si><t>A&amp;B &lt;x&gt;</t></si>
<si><t xml:space="preserve">行1&#10;行2</t></si>
</sst>""" % _NS_MAIN

_SHEET1 = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="{_NS_MAIN}"><sheetData>
<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c><c r="D1" t="s"><v>0</v></c></row>
<row r="2"><c r="A2" t="inlineStr"><is><t>いんライン</t></is></c><c r="B2"><v>123</v></c></row>
<row r="4"><c r="A4" t="s"><v>2</v></c></row>
<row r="5"><c r="C5" t="s"><v>3</v></c></row>
<row r="6"><c r="A6" t="s"><v>4</v></c></row>
</sheetData>
<mergeCells count="1"><mergeCell ref="D1:E1"/></mergeCells></worksheet>"""

_SHEET2 = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="{_NS_MAIN}"><sheetData/></worksheet>"""


def build_fixture() -> bytes:
    """検証用の .xlsx をメモリ上で組み立てて返す。"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("xl/workbook.xml", _WORKBOOK)
        zf.writestr("xl/_rels/workbook.xml.rels", _RELS)
        zf.writestr("xl/sharedStrings.xml", _SHARED)
        zf.writestr("xl/worksheets/sheet1.xml", _SHEET1)
        zf.writestr("xl/worksheets/sheet2.xml", _SHEET2)
    return buf.getvalue()


def _write_fixture(directory: Path) -> Path:
    path = directory / "fixture.xlsx"
    path.write_bytes(build_fixture())
    return path


# ---------------------------------------------------------------------------
# 検証本体
# ---------------------------------------------------------------------------


def run_checks() -> list[str]:
    """失敗メッセージの一覧を返す（空 = 全通過）。"""
    failures: list[str] = []

    with tempfile.TemporaryDirectory(prefix="legacy_selftest_") as tmp:
        fixture = _write_fixture(Path(tmp))

        # 1. シート名列挙
        names = sheet_names(fixture)
        if names != ["明細", "空"]:
            failures.append(f"1. シート名が定義順ではありません: {names}")

        # 2〜4 は既定の疎表示でまとめて確認する
        text = sheet_text(fixture, sheet="明細")

        # 2. 振仮名が混入しない（最重要）
        if "キノウガイヨウ" in text:
            failures.append("2. 振仮名(<rPh>)が本文へ混入しています")
        if "機能概要" not in text:
            failures.append("2. 振仮名を除いた本文が失われています")

        # 3. リッチテキストの連結
        if "A:あい" not in text:
            failures.append("3. リッチテキスト(<r>)の run が連結されていません")

        # 4. inlineStr / 数値 / 実体参照 / セル内改行
        if "r2\tA:いんライン | B:123" not in text:
            failures.append("4. inlineStr または数値が読めていません")
        if "C:A&B <x>" not in text:
            failures.append("4. XML 実体参照が復元されていません")
        if "A:行1 / 行2" not in text:
            failures.append("4. セル内改行の畳み込みが効いていません")

        # 5. 疎表示: 空セルが落ち、列記号が実際の位置を指す
        expected_sparse = "r1\tA:会社コード | B:機能概要 | D:会社コード"
        if expected_sparse not in text.split("\n"):
            failures.append(f"5. 疎表示の位置が不一致。期待: {expected_sparse!r}")
        if "\t\t\t\t" in text:
            failures.append("5. 疎表示なのに空セルが残っています")

        # 6. ヘッダ（疎表示は結合を複製しないので、使用列は D 列までの 4）
        header = text.split("\n")[0]
        if not header.startswith("# sheet: 明細") or "rows=6 cols=4 mode=sparse" not in header:
            failures.append(f"6. 疎表示のヘッダが不一致: {header!r}")

        # 6b. 格子 + 結合複製 + 注記（opt-in）
        filled = sheet_text(fixture, sheet="明細", mode="grid", fill_merges=True, show_merge=True)
        filled_lines = filled.split("\n")
        expected_row1 = "会社コード\t機能概要\t\t会社コード\t会社コード"
        if expected_row1 not in filled_lines:
            failures.append(f"6b. 結合複製が不一致。期待: {expected_row1!r}")
        if "# merged: D1:E1" not in filled:
            failures.append("6b. 結合範囲の注記が出ていません")
        if "mode=grid" not in filled_lines[0]:
            failures.append(f"6b. 格子モードのヘッダが不一致: {filled_lines[0]!r}")

        # 6c. 結合複製は既定では起きない（忠実側が既定であることの確認）
        plain = sheet_text(fixture, sheet="明細", mode="grid")
        if "会社コード\t機能概要\t\t会社コード\t会社コード" in plain:
            failures.append("6c. 結合複製が既定で有効になっています（忠実側が既定であるべき）")

        # 7. 空シート
        empty = sheet_text(fixture, sheet="空")
        if "rows=0 cols=0" not in empty:
            failures.append(f"7. 空シートの扱いが不一致: {empty.splitlines()[0]!r}")

        # 8. 全シート連結
        if len(read_workbook(fixture)) != 2:
            failures.append("8. read_workbook が 2 シートを返していません")
        if "# sheet: 空" not in workbook_text(fixture):
            failures.append("8. workbook_text に 2 番目のシートが出ていません")

        # 9. 異常系
        for label, call in [
            ("存在しないシート", lambda: sheet_text(fixture, sheet="無い")),
            ("範囲外のシート番号", lambda: sheet_text(fixture, index=99)),
            ("存在しないファイル", lambda: sheet_text(Path(tmp) / "no_such.xlsx")),
        ]:
            try:
                call()
                failures.append(f"9. {label} で例外が出ませんでした")
            except LegacyToolError:
                pass

        # 非 zip（= 壊れた xlsx）
        broken = Path(tmp) / "broken.xlsx"
        broken.write_bytes(b"this is not a zip")
        try:
            sheet_text(broken)
            failures.append("9. 非 zip ファイルで例外が出ませんでした")
        except LegacyToolError:
            pass

        # 10. 書き込みガード（読み取り専用領域を拒否する）
        try:
            guard_output("D:/AI_work/doc/inventory.json")
            failures.append("10. 読み取り専用領域への出力が拒否されませんでした")
        except ReadOnlyViolation:
            pass

        # 書き込み可能な場所は通す
        try:
            guard_output(Path(tmp) / "ok.txt")
        except ReadOnlyViolation:
            failures.append("10. 書き込み可能な場所まで拒否しています")

    return failures


def self_test() -> tuple[bool, list[str]]:
    failures = run_checks()
    return (not failures), failures

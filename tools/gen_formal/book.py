#!/usr/bin/env python3
"""book - 機読源 Markdown → 「基本設計書（画面編）」体裁の Excel（目視・対外用）。

何をするか:
  `md_book.parse()` が作った書類モデルを、参考書（`50.設計書/画面設計書/*.xlsx`）の
  **見た目**に寄せて xlsx へ描く。節 → シート、小見出し → 帯、表 → 結合セル群。

やらないこと（重要）:
  - 参考書の**業務内容は一切写さない**。中身は md に書いてあることだけ。
  - 顧客の会社名・ロゴ・ページフッタ・雛形図形は複製しない（顧客識別子）。
  - `docs/**` へは書かない（CP-R-3: `docs/**/*.xlsx == 0`）。出力は `reports/` のみ。

単一ソース（NFR-1）:
  - 正は md。生成物を手で編集しない（編集したら次の生成で消える）。
  - 結合幅・塗り・罫線は**本ファイルが唯一の定義**（md に体裁を書かない）。

冪等（`.claude/rules/03-design-coding.md` §7.1）:
  - 現在時刻・乱数・集合の反復順を持ち込まない。同じ md からは同じバイト列が出る。

使い方:
  py -3 -m tools.gen_formal.book --md <file.md>                 # dry-run（既定）
  py -3 -m tools.gen_formal.book --md <file.md> --out reports/x.xlsx
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.page import PageMargins
from openpyxl.worksheet.properties import PageSetupProperties

from .md_book import Block, Doc, Section, Sub, parse  # noqa: F401  (Sub は型注釈用)

FONT_NAME = "Meiryo UI"
MONO_FONT = "Consolas"

FILL_BANNER = PatternFill("solid", fgColor="99CCFF")
FILL_HEAD = PatternFill("solid", fgColor="99CCFF")
FILL_GROUP = PatternFill("solid", fgColor="CCECFF")
FILL_FIRST = PatternFill("solid", fgColor="CCFFFF")

_SIDE_THIN = Side(style="thin", color="000000")
_SIDE_HAIR = Side(style="hair", color="000000")
_SIDE_DOUBLE = Side(style="double", color="000000")

BORDER_HEAD = Border(left=_SIDE_THIN, right=_SIDE_THIN, top=_SIDE_THIN, bottom=_SIDE_DOUBLE)
BORDER_DATA = Border(left=_SIDE_THIN, right=_SIDE_THIN, top=_SIDE_HAIR, bottom=_SIDE_HAIR)
BORDER_DOC = Border(left=_SIDE_THIN, right=_SIDE_THIN, top=_SIDE_THIN, bottom=_SIDE_THIN)
BORDER_NONE = Border()

ALIGN_HEAD = Alignment(horizontal="center", vertical="center", wrap_text=True)
ALIGN_DATA = Alignment(horizontal="left", vertical="top", wrap_text=True)
ALIGN_CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)


# ---------------------------------------------------------------- 紙面の設計

# シート → 物理列数。合計幅は TOTAL_WIDTH を等分する（結合で読みやすい幅にする）。
TOTAL_WIDTH = 132.0

SHEET_COLS = {
    "変更履歴": 20,
    "画面概要": 14,
    "画面遷移図": 18,
    "画面レイアウト": 24,
    "画面項目内容": 46,
    "イベント一覧": 47,
    "業務処理説明": 46,
    "処理モジュール": 24,
    "入力チェック一覧": 24,
    "エラー一覧": 24,
    "使用エンティティ・共通部品": 20,
    "非機能・セキュリティ": 18,
    "制約・前提": 18,
    "追跡": 20,
}

# 節 → シート。前半 8 つは参考書（画面編）と同じ名前に揃える。
# 参考書の最終シート `R60LoginAction`（Struts 固有）は置かず、`処理モジュール` にする。
SHEET_PLAN: list[tuple[str, list[str]]] = [
    ("変更履歴", ["0.1", "14", "0.2", "0.3", "0.4"]),
    ("画面概要", ["1"]),
    ("画面遷移図", ["2"]),
    ("画面レイアウト", ["3"]),
    ("画面項目内容", ["4"]),
    ("イベント一覧", ["5"]),
    ("業務処理説明", ["6"]),
    ("処理モジュール", ["7"]),
    ("入力チェック一覧", ["8"]),
    ("エラー一覧", ["9"]),
    ("使用エンティティ・共通部品", ["10"]),
    ("非機能・セキュリティ", ["11"]),
    ("制約・前提", ["12"]),
    ("追跡", ["13"]),
]

# ---------------------------------------------------------------------------
# 「詳細設計書」体裁（2026-10-22 追加）。
#   節の並びが画面編と違うため、**シート名を流用してはならない**。
#   画面編の SHEET_PLAN で詳細設計を描くと、§2 論理設計が「画面遷移図」に入る等の誤配置になる。
#   対応: 節番号 → シート名の対応を別表で持つ。どちらを使うかは `--profile` か自動判定で決める。
# ---------------------------------------------------------------------------
DETAIL_SHEET_COLS = {
    "変更履歴": 20,
    "詳細設計の範囲": 18,
    "論理設計": 30,
    "データモデル": 40,
    "項目定義": 40,
    "SQL テンプレート": 44,
    "エラー分岐": 40,
    "境界値表": 34,
    "非機能・セキュリティ": 20,
    "制約・前提": 18,
    "追跡": 24,
    "付表B_未確定事項": 24,
}

DETAIL_SHEET_PLAN: list[tuple[str, list[str]]] = [
    # 末尾の 2 つは節題で引く（初稿・改修版・承認版で節番号が動くため）。
    ("変更履歴", ["0.1", "0.2", "0.3", "0.4", "#改訂履歴"]),
    ("詳細設計の範囲", ["1"]),
    ("論理設計", ["2"]),
    ("データモデル", ["3"]),
    ("項目定義", ["4"]),
    ("SQL テンプレート", ["5"]),
    ("エラー分岐", ["6"]),
    ("境界値表", ["7"]),
    ("非機能・セキュリティ", ["8"]),
    ("制約・前提", ["9"]),
    ("追跡", ["10"]),
    ("付表B_未確定事項", ["#付表 B"]),
]

PROFILES = {
    "画面編": (SHEET_PLAN, SHEET_COLS, "基本設計書（画面編）"),
    "詳細設計": (DETAIL_SHEET_PLAN, DETAIL_SHEET_COLS, "詳細設計書"),
}

# 詳細設計書だと判定する節題の手掛かり（`--profile auto` のときだけ使う）。
_DETAIL_HINTS = ("論理設計", "SQL テンプレート", "境界値表", "データモデル")


def detect_profile(doc: Doc) -> str:
    """節題から体裁を推定する。見つからなければ画面編（既存の既定を変えない）。"""
    titles = [s.title for s in doc.sections]
    hits = sum(1 for h in _DETAIL_HINTS if any(h in t for t in titles))
    return "詳細設計" if hits >= 2 else "画面編"

# 画面項目内容: 論理 16 列 → 物理列の結合範囲（左端, 右端）
ITEM_SPANS = [
    (1, 1), (2, 6), (7, 10), (11, 11), (12, 12), (13, 13), (14, 14),
    (15, 18), (19, 22), (23, 24), (25, 25), (26, 26), (27, 27),
    (28, 31), (32, 45), (46, 46),
]
ITEM_GROUPS = [
    ("基本情報", 1, 6), ("種別", 7, 10), ("入出力", 11, 12),
    ("エンティティ", 13, 22), ("画面表示", 23, 31),
    ("表示・入力仕様", 32, 45), ("項目ID", 46, 46),
]

# イベント一覧: 論理 7 列 → 物理列の結合範囲
EVENT_SPANS = [(1, 1), (2, 7), (8, 11), (12, 15), (16, 31), (32, 40), (41, 47)]
EVENT_GROUPS = [
    ("イベント", 1, 11), ("分類", 12, 15), ("処理概要", 16, 31),
    ("例外処理", 32, 40), ("備考", 41, 47),
]

# 業務処理説明: 入力 / 処理 / 出力 の 3 帯
BAND_IN = (1, 8)
BAND_PROC = (9, 39)
BAND_OUT = (40, 46)


# ---------------------------------------------------------------- 描画


class SheetBuilder:
    """1 シート分の描画。行カーソルを持ち、以降は必ず前進する。"""

    def __init__(self, ws, ncols: int):
        self.ws = ws
        self.ncols = ncols
        self.row = 0
        self.last_header_row = 0
        width = max(2.0, TOTAL_WIDTH / ncols)
        for i in range(1, ncols + 1):
            ws.column_dimensions[get_column_letter(i)].width = width
        ws.sheet_view.showGridLines = False
        ws.page_setup.orientation = "landscape"
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.page_margins = PageMargins(left=0.4, right=0.4, top=0.5, bottom=0.5)

    # -- 低レベル --------------------------------------------------

    def _merge(self, r1, c1, r2, c2, border=BORDER_NONE):
        ws = self.ws
        if r1 == r2 and c1 == c2:
            pass
        else:
            ws.merge_cells(start_row=r1, start_column=c1, end_row=r2, end_column=c2)
        for rr in range(r1, r2 + 1):
            for cc in range(c1, c2 + 1):
                ws.cell(row=rr, column=cc).border = border

    def _write(self, r, c, value, font, align, fill=None, border=BORDER_NONE):
        cell = self.ws.cell(row=r, column=c, value=value)
        cell.font = font
        cell.alignment = align
        if fill is not None:
            cell.fill = fill
        cell.border = border
        return cell

    # -- 帯・段落 --------------------------------------------------

    def banner(self, text: str) -> None:
        self.row += 1
        self._merge(self.row, 1, self.row, self.ncols, BORDER_DOC)
        self._write(self.row, 1, text, Font(name=FONT_NAME, size=11, bold=True),
                    ALIGN_DATA, FILL_BANNER, BORDER_DOC)
        for c in range(1, self.ncols + 1):
            self.ws.cell(row=self.row, column=c).fill = FILL_BANNER
        self.ws.row_dimensions[self.row].height = 24

    def group(self, text: str) -> None:
        self.row += 2
        self._merge(self.row, 1, self.row, self.ncols, BORDER_DOC)
        self._write(self.row, 1, text, Font(name=FONT_NAME, size=10, bold=True),
                    ALIGN_DATA, FILL_GROUP, BORDER_DOC)
        for c in range(1, self.ncols + 1):
            self.ws.cell(row=self.row, column=c).fill = FILL_GROUP
        self.ws.row_dimensions[self.row].height = 20

    def text(self, text: str, indent: int = 0) -> None:
        self.row += 1
        self._merge(self.row, 1, self.row, self.ncols, BORDER_NONE)
        self._write(self.row, 1, text, Font(name=FONT_NAME, size=9), ALIGN_DATA)
        if indent:
            self.ws.cell(row=self.row, column=1).alignment = Alignment(
                horizontal="left", vertical="top", wrap_text=True, indent=2)

    def bullet(self, text: str) -> None:
        self.text("・" + text)

    def quote(self, text: str) -> None:
        self.row += 1
        self._merge(self.row, 1, self.row, self.ncols, BORDER_NONE)
        self._write(self.row, 1, text, Font(name=FONT_NAME, size=8, italic=True, color="595959"),
                    ALIGN_DATA)

    def code(self, lines: list[str]) -> None:
        self.row += 1
        self._merge(self.row, 1, self.row, self.ncols, BORDER_DOC)
        self._write(self.row, 1, "\n".join(lines), Font(name=MONO_FONT, size=8),
                    ALIGN_DATA, None, BORDER_DOC)
        self.ws.row_dimensions[self.row].height = min(409, max(15, 11.0 * len(lines)))

    # -- 表 --------------------------------------------------------

    def spans_for(self, rows: list[list[str]]) -> list[tuple[int, int]]:
        """論理列 → 物理列の割当。内容の長さで重みを付ける（同じ入力なら同じ結果）。"""
        n = max(len(r) for r in rows)
        weights: list[float] = []
        for i in range(n):
            lens = [len(r[i]) for r in rows if i < len(r) and r[i]]
            avg = (sum(lens) / len(lens)) if lens else 8.0
            weights.append(max(6.0, min(avg, 60.0)))
        total = sum(weights)
        raw = [w / total * self.ncols for w in weights]
        ints = [max(1, int(x)) for x in raw]
        # 端数を「切り捨てで減った分」だけ、小数部の大きい順に配る（同点は左優先）
        while sum(ints) < self.ncols:
            order = sorted(range(n), key=lambda i: (-(raw[i] - int(ints[i])), i))
            for i in order:
                if sum(ints) >= self.ncols:
                    break
                ints[i] += 1
        while sum(ints) > self.ncols:
            order = sorted(range(n), key=lambda i: (-ints[i], i))
            for i in order:
                if sum(ints) <= self.ncols:
                    break
                if ints[i] > 1:
                    ints[i] -= 1
        spans: list[tuple[int, int]] = []
        c = 1
        for size in ints:
            spans.append((c, c + size - 1))
            c += size
        return spans

    def table(self, rows: list[list[str]], spans: list[tuple[int, int]] | None = None,
              group_bands: list[tuple[str, int, int]] | None = None) -> None:
        if not rows:
            return
        if spans is None:
            spans = self.spans_for(rows)
        ncol = max(len(r) for r in rows)

        if group_bands:
            self.row += 1
            for label, c1, c2 in group_bands:
                self._merge(self.row, c1, self.row, c2, BORDER_HEAD)
                self._write(self.row, c1, label,
                            Font(name=FONT_NAME, size=9, bold=True), ALIGN_HEAD,
                            FILL_HEAD, BORDER_HEAD)
            for c in range(1, self.ncols + 1):
                self.ws.cell(row=self.row, column=c).fill = FILL_HEAD

        # 見出し行
        self.row += 1
        head_row = self.row
        self.last_header_row = head_row
        for i, (c1, c2) in enumerate(spans[:ncol]):
            self._merge(head_row, c1, head_row, c2, BORDER_HEAD)
            self._write(head_row, c1, rows[0][i] if i < len(rows[0]) else "",
                        Font(name=FONT_NAME, size=9, bold=True), ALIGN_HEAD,
                        FILL_HEAD, BORDER_HEAD)
            for c in range(c1, c2 + 1):
                self.ws.cell(row=head_row, column=c).fill = FILL_HEAD
        self.ws.row_dimensions[head_row].height = 30

        # データ行
        for k, src in enumerate(rows[1:]):
            self.row += 1
            fill = FILL_FIRST if k == 0 else None
            for i, (c1, c2) in enumerate(spans[:ncol]):
                value = src[i] if i < len(src) else ""
                self._merge(self.row, c1, self.row, c2, BORDER_DATA)
                self._write(self.row, c1, value, Font(name=FONT_NAME, size=9),
                            ALIGN_DATA, fill, BORDER_DATA)
                if fill is not None:
                    for c in range(c1, c2 + 1):
                        self.ws.cell(row=self.row, column=c).fill = fill

    def freeze_below_header(self) -> None:
        """見出し直下で固定する。2 枚目以降の表では上書きしない（最初の表が正）。"""
        if self.ws.freeze_panes is None and self.last_header_row:
            self.ws.freeze_panes = "A%d" % (self.last_header_row + 1)


# ---------------------------------------------------------------- 各節の描画


def _blocks_simple(sb: SheetBuilder, sub: Sub) -> None:
    if sub.title:
        sb.group(sub.title)
    for blk in sub.blocks:
        if blk.kind == "table":
            sb.table(blk.rows)
        elif blk.kind == "code":
            sb.code(blk.lines)
        elif blk.kind == "bullet":
            sb.bullet(blk.text)
        elif blk.kind == "quote":
            sb.quote(blk.text)
        elif blk.kind == "num":
            sb.text(blk.text, indent=1 + blk.indent)
        else:
            sb.text(blk.text)


def render_generic(sb: SheetBuilder, subs: list[Sub], first_table_form: bool = False) -> None:
    first = True
    for sub in subs:
        if sub.title:
            sb.group(sub.title)
        for blk in sub.blocks:
            if blk.kind != "table":
                if blk.kind == "code":
                    sb.code(blk.lines)
                elif blk.kind == "bullet":
                    sb.bullet(blk.text)
                elif blk.kind == "quote":
                    sb.quote(blk.text)
                elif blk.kind == "num":
                    sb.text(blk.text, indent=1 + blk.indent)
                else:
                    sb.text(blk.text)
                continue
            spans = None
            if first and first_table_form and len(blk.rows[0]) == 2:
                spans = [(1, 3), (4, sb.ncols)]
            sb.table(blk.rows, spans=spans)
            first = False


def render_item_table(sb: SheetBuilder, subs: list[Sub]) -> None:
    """§4 画面項目内容。16 列 + 上位の帯を 2 段で出す。"""
    for sub in subs:
        if sub.title:
            sb.group(sub.title)
        for blk in sub.blocks:
            if blk.kind != "table":
                if blk.kind == "quote":
                    sb.quote(blk.text)
                elif blk.kind == "bullet":
                    sb.bullet(blk.text)
                else:
                    sb.text(blk.text)
                continue
            if max(len(r) for r in blk.rows) == 16:
                sb.table(blk.rows, spans=ITEM_SPANS, group_bands=ITEM_GROUPS)
                sb.freeze_below_header()
            else:
                sb.table(blk.rows)


def render_event_table(sb: SheetBuilder, subs: list[Sub]) -> None:
    """§5 イベント一覧。7 列 + 上位の帯。"""
    for sub in subs:
        if sub.title:
            sb.group(sub.title)
        for blk in sub.blocks:
            if blk.kind != "table":
                if blk.kind == "quote":
                    sb.quote(blk.text)
                elif blk.kind == "bullet":
                    sb.bullet(blk.text)
                else:
                    sb.text(blk.text)
                continue
            if max(len(r) for r in blk.rows) == 7:
                sb.table(blk.rows, spans=EVENT_SPANS, group_bands=EVENT_GROUPS)
                sb.freeze_below_header()
            else:
                sb.table(blk.rows)


def _split_bands(blocks: list[Block]) -> tuple[list[str], list[str], list[str]]:
    """イベント 1 つ分の塊を 入力 / 処理 / 出力 の 3 列へ振り分ける。"""
    band = "proc"
    ins: list[str] = []
    proc: list[str] = []
    outs: list[str] = []
    for blk in blocks:
        if blk.kind == "table":
            proc.append("／".join(c for c in blk.rows[0] if c))
            for row in blk.rows[1:]:
                proc.append(" | ".join(row))
            continue
        text = blk.text
        if blk.kind == "num":
            target = proc
        elif text.startswith("入力"):
            band = "in"
            rest = text[len("入力"):].strip(" 　:：")
            target = ins
            if rest:
                target.append(rest)
            continue
        elif text.startswith("処理") and len(text) <= 4:
            band = "proc"
            continue
        elif text.startswith("出力"):
            band = "out"
            rest = text[len("出力"):].strip(" 　:：")
            target = outs
            if rest:
                target.append(rest)
            continue
        else:
            target = {"in": ins, "proc": proc, "out": outs}[band]
        if blk.kind == "num" and blk.indent:
            target.append("　　" + text)
        else:
            target.append(text)
    return ins, proc, outs


def render_process_doc(sb: SheetBuilder, subs: list[Sub]) -> None:
    """§6 業務処理説明。イベントごとに 入力 / 処理 / 出力 の 3 帯を縦に流す。"""
    for sub in subs:
        if not sub.title:
            if sub.blocks:
                sb.group("共通前処理")
                for blk in sub.blocks:
                    if blk.kind == "num":
                        sb.text(blk.text, indent=1 + blk.indent)
                    elif blk.kind == "bullet":
                        sb.bullet(blk.text)
                    elif blk.kind == "quote":
                        sb.quote(blk.text)
                    else:
                        sb.text(blk.text)
            continue

        sb.group(sub.title)
        ins, proc, outs = _split_bands(sub.blocks)

        # 帯の見出し
        sb.row += 1
        for label, (c1, c2) in (("入力", BAND_IN), ("処理", BAND_PROC), ("出力", BAND_OUT)):
            sb._merge(sb.row, c1, sb.row, c2, BORDER_HEAD)
            sb._write(sb.row, c1, label, Font(name=FONT_NAME, size=9, bold=True),
                      ALIGN_HEAD, FILL_HEAD, BORDER_HEAD)
            for c in range(c1, c2 + 1):
                sb.ws.cell(row=sb.row, column=c).fill = FILL_HEAD
        sb.ws.row_dimensions[sb.row].height = 18

        n = max(len(ins), len(proc), len(outs), 1)
        for k in range(n):
            sb.row += 1
            for lines, (c1, c2) in ((ins, BAND_IN), (proc, BAND_PROC), (outs, BAND_OUT)):
                value = lines[k] if k < len(lines) else ""
                sb._merge(sb.row, c1, sb.row, c2, BORDER_DATA)
                sb._write(sb.row, c1, value, Font(name=FONT_NAME, size=9),
                          ALIGN_DATA, None, BORDER_DATA)


# ---------------------------------------------------------------- 組み立て


def _resolve(doc: Doc, key: str) -> list[Sub]:
    """'0.1' → §0 の小見出し 0.1。'14' → §14 のすべての小見出し。

    '#題' は**節題の部分一致**で引く（節番号が版によって動く節に使う）。
    例: 承認版では「付表 B」の節が無くなり、改訂履歴が §12 → §11 へ繰り上がる。
    番号で引くと、消えた節の代わりに別の節がそのシートへ入ってしまう。
    """
    if key.startswith("#"):
        needle = key[1:]
        for sec in doc.sections:
            if needle in sec.title:
                return [s for s in sec.subs if s.title or s.blocks]
        return []
    if "." in key:
        sec_no = key.split(".", 1)[0]
        sec = doc.section(sec_no)
        if sec is None:
            return []
        # 小見出しの題は "0.1 書類情報" の形。節番号込みで前方一致させる
        # （"1" で切ると "0.1" が "1" に化けて 0 件になる）。
        return [s for s in sec.subs if s.title.startswith(key)]
    sec = doc.section(key)
    if sec is None:
        return []
    return [s for s in sec.subs if s.title or s.blocks]


def _safe_title(name: str) -> str:
    out = name
    for ch in "[]:*?/\\":
        out = out.replace(ch, "_")
    return out[:31]


def build(doc: Doc, sheet_names: list[str] | None = None,
          profile: str = "auto") -> Workbook:
    """書類モデル → Workbook。`sheet_names` を渡すとそのシートだけ作る。"""
    if profile == "auto":
        profile = detect_profile(doc)
    plan, cols, label = PROFILES[profile]

    wb = Workbook()
    wb.remove(wb.active)
    wb.properties.creator = "tools.gen_formal.book"
    wb.properties.lastModifiedBy = "tools.gen_formal.book"
    wb.properties.created = datetime(2000, 1, 1, 0, 0, 0)
    wb.properties.modified = datetime(2000, 1, 1, 0, 0, 0)

    for name, keys in plan:
        if sheet_names is not None and name not in sheet_names:
            continue
        subs: list[Sub] = []
        for key in keys:
            subs.extend(_resolve(doc, key))
        # `#題` で引くシートは「その節が在るときだけ作る」（空シートを残さない）。
        if not subs and any(k.startswith("#") for k in keys):
            continue
        ws = wb.create_sheet(_safe_title(name))
        sb = SheetBuilder(ws, cols.get(name, 16))
        sb.banner("%s　｜　%s" % (doc.title or label, name))

        if name == "画面項目内容":
            render_item_table(sb, subs)
        elif name == "イベント一覧":
            render_event_table(sb, subs)
        elif name == "業務処理説明":
            render_process_doc(sb, subs)
        elif name == "画面概要":
            render_generic(sb, subs, first_table_form=True)
        else:
            render_generic(sb, subs)

        ws.print_title_rows = "1:1"
    return wb


# ---------------------------------------------------------------- CLI


def _normalize_zip(path: Path) -> None:
    """xlsx（= zip）のエントリ時刻を固定する。

    openpyxl は保存時に各エントリへ**現在時刻**を書くため、同じ内容でも
    バイト列が毎回変わる。規則 03 §7.1（生成は冪等）を満たすため、
    中身はそのままに時刻だけ 1980-01-01 へ置き換えて詰め直す。
    """
    import re
    import zipfile

    stamp = b"<dcterms:modified xsi:type=\"dcterms:W3CDTF\">2000-01-01T00:00:00Z</dcterms:modified>"
    created = b"<dcterms:created xsi:type=\"dcterms:W3CDTF\">2000-01-01T00:00:00Z</dcterms:created>"

    with zipfile.ZipFile(path) as zin:
        items = []
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename == "docProps/core.xml":
                # openpyxl は保存時に modified を現在時刻で上書きする。ここで固定する。
                data = re.sub(rb"<dcterms:modified[^>]*>[^<]*</dcterms:modified>", stamp, data)
                data = re.sub(rb"<dcterms:created[^>]*>[^<]*</dcterms:created>", created, data)
            items.append((info.filename, data))
    tmp = path.with_name(path.name + ".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in items:
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            zout.writestr(info, data)
    tmp.replace(path)


def _inside_docs(path: Path) -> bool:
    parts = [p.lower() for p in path.resolve().parts]
    return "docs" in parts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="gen_formal.book",
        description="機読源 md → 基本設計書（画面編）体裁の xlsx（目視・対外用）")
    ap.add_argument("--md", required=True, help="機読源の Markdown")
    ap.add_argument("--out", help="出力 xlsx。省略時は dry-run（作らない）")
    ap.add_argument("--sheets", nargs="*", help="このシートだけ生成（既定は全部）")
    ap.add_argument("--profile", choices=["auto", "画面編", "詳細設計"], default="auto",
                    help="体裁。auto は節題から判定する（既定）")
    args = ap.parse_args(argv)

    doc = parse(args.md)
    if not doc.sections:
        print("[gen_formal.book] 節が見つかりません: %s" % args.md, file=sys.stderr)
        return 1

    profile = detect_profile(doc) if args.profile == "auto" else args.profile
    plan = PROFILES[profile][0]

    if not args.out:
        print("[gen_formal.book] profile=%s（%d シート）" % (profile, len(plan)))
        for name, keys in plan:
            subs: list[Sub] = []
            for key in keys:
                subs.extend(_resolve(doc, key))
            nrows = sum(len(s.blocks) for s in subs)
            print("[dry-run] %-28s sections=%-10s blocks=%d"
                  % (name, ",".join(keys), nrows))
        print("[gen_formal.book] md=%s sections=%d -> dry-run only"
              % (Path(args.md).name, len(doc.sections)))
        return 0

    out = Path(args.out)
    if _inside_docs(out):
        print("[gen_formal.book] docs/ へは書けません（CP-R-3: docs/**/*.xlsx == 0）。"
              "出力は reports/ へ。", file=sys.stderr)
        return 2

    wb = build(doc, args.sheets or None, profile=profile)
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    _normalize_zip(out)
    print("[gen_formal.book] profile=%s wrote %s sheets=%d"
          % (profile, out.as_posix(), len(wb.sheetnames)))
    print("[gen_formal.book] " + " / ".join(wb.sheetnames))
    return 0


if __name__ == "__main__":
    sys.exit(main())

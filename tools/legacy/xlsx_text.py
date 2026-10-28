#!/usr/bin/env python3
"""xlsx_text - .xlsx を標準ライブラリだけでテキスト化する（openpyxl 非依存）。

なぜ自作するか:
  本骨架は専線環境を想定しており、勝手に外部パッケージを導入しない（規則 00 §13）。
  本机に openpyxl は無い。しかし .xlsx の実体は「zip + XML」であるため、
  zipfile と xml.etree（いずれも標準ライブラリ）だけで読める。

読み取り専用の原則:
  対象（歴史案件 `D:/AI_work`）は**他人のプロジェクトの実コードであり、永久に読み取り専用**。
  本モジュールは対象を読むだけで、対象側へは一切書かない。出力先が読み取り専用領域の
  内側を指した場合は、書く前に `guard_output()` が拒否する。

振仮名の罠（★重要）:
  `<si>` の中の `<t>` を素朴に全部集めると `<rPh>`（ルビ）の本文まで混入し、
  「機能概要キノウガイヨウ」になる。`<rPh>` / `<phoneticPr>` の部分木は必ず読み飛ばす。

出力形式:
  既定はタブ区切り（TSV）。セル内の改行・タブは空白へ潰す。
  潰さないと 1 セルが複数行に割れ、行と列の対応が読めなくなるため。
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_OFFICE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

# 読み飛ばす要素。ここを空にするとルビが本文へ混入する（上記「振仮名の罠」）。
_SKIP_TAGS = frozenset({"rPh", "phoneticPr"})

_CELL_REF_RE = re.compile(r"^([A-Za-z]+)(\d+)$")

# 出力を拒否する読み取り専用領域。唯一の真源は docs/00_registry/ingest-manifest.yml の
# `projects[].root`（read_only: true）。manifest が読めない環境ではこの既定へフォールバックする。
_FALLBACK_READONLY_ROOTS = ("D:/AI_work",)


class LegacyToolError(Exception):
    """本パッケージの想定内エラーの基底。"""


class ReadOnlyViolation(LegacyToolError):
    """読み取り専用領域へ書き込もうとした（または書き込み設定が危険）。"""


class MaskUnavailable(LegacyToolError):
    """--mask が指定されたが、脱敏辞書が無い（未マスクで外へ出るのを防ぐ）。"""


# ---------------------------------------------------------------------------
# 読み取り専用領域の解決と出力ガード
# ---------------------------------------------------------------------------


def _readonly_roots() -> tuple[Path, ...]:
    """読み取り専用領域の絶対パス一覧を返す（manifest 優先・失敗時は既定値）。"""
    try:  # 循環 import と pyyaml 不在の双方を許容する
        import yaml

        from tools.paths import find_root

        manifest = find_root() / "docs" / "00_registry" / "ingest-manifest.yml"
        data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
        roots = []
        for project in data.get("projects", []):
            if project.get("read_only") and project.get("root"):
                roots.append(Path(str(project["root"])))
        if roots:
            return tuple(roots)
    except Exception:  # noqa: BLE001 - フォールバックが目的なので握りつぶす
        pass
    return tuple(Path(p) for p in _FALLBACK_READONLY_ROOTS)


def guard_output(path: Path | str) -> Path:
    """出力先が読み取り専用領域の内側なら `ReadOnlyViolation` を投げる。

    「手が滑って歴史案件の上に書いた」を機械的に不可能にするための最終防壁。
    戻り値は解決済みの絶対パス。
    """
    resolved = Path(path).expanduser().resolve()
    for root in _readonly_roots():
        try:
            root_res = root.expanduser().resolve()
        except OSError:  # pragma: no cover - 解決不能なドライブは比較対象から外す
            continue
        if resolved == root_res or root_res in resolved.parents:
            raise ReadOnlyViolation(
                f"出力先が読み取り専用領域の内側です: {resolved}\n"
                f"  （この領域は他人のプロジェクトの実コードであり、いかなる理由でも書き込めない）\n"
                f"  書き込み可能な場所: D:/AI_work_dev 配下"
            )
    return resolved


# ---------------------------------------------------------------------------
# XML ヘルパ
# ---------------------------------------------------------------------------


def _local(tag: str) -> str:
    """名前空間接頭辞を落としたローカル名を返す。"""
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _text_of(elem: ET.Element | None) -> str:
    """要素配下の `<t>` を文書順に連結する。`<rPh>` / `<phoneticPr>` の部分木は読み飛ばす。"""
    if elem is None:
        return ""
    parts: list[str] = []

    def walk(node: ET.Element) -> None:
        name = _local(node.tag)
        if name in _SKIP_TAGS:
            return
        if name == "t":
            parts.append(node.text or "")
            return
        for child in node:
            walk(child)

    walk(elem)
    return "".join(parts)


def _child_by_local(parent: ET.Element, name: str) -> ET.Element | None:
    for child in parent:
        if _local(child.tag) == name:
            return child
    return None


def _col_index(letters: str) -> int:
    """列記号 `A` / `AB` を 0 起点の列番号へ。"""
    value = 0
    for ch in letters.upper():
        value = value * 26 + (ord(ch) - 64)
    return value - 1


def _cell_ref(ref: str) -> tuple[int, int] | None:
    """`B12` → `(row=11, col=1)`（いずれも 0 起点）。不正なら None。"""
    match = _CELL_REF_RE.match(ref.strip())
    if not match:
        return None
    return int(match.group(2)) - 1, _col_index(match.group(1))


# ---------------------------------------------------------------------------
# ワークブック / シートの読み込み
# ---------------------------------------------------------------------------


def _parse_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    return [_text_of(el) for el in root if _local(el.tag) == "si"]


def _sheet_entries(zf: zipfile.ZipFile) -> list[tuple[str, str]]:
    """`[(シート名, zip 内パス)]` をワークブック定義順に返す。"""
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    rels_path = "xl/_rels/workbook.xml.rels"
    rid_to_target: dict[str, str] = {}
    if rels_path in zf.namelist():
        rels = ET.fromstring(zf.read(rels_path))
        for rel in rels:
            rid = rel.get("Id")
            if rid:
                rid_to_target[rid] = rel.get("Target") or ""

    entries: list[tuple[str, str]] = []
    for sheets in workbook:  # <sheets> を探す（通常は 1 個）
        if _local(sheets.tag) != "sheets":
            continue
        for sheet in sheets:
            if _local(sheet.tag) != "sheet":
                continue
            name = sheet.get("name") or f"sheet{len(entries) + 1}"
            rid = sheet.get(f"{{{NS_OFFICE_REL}}}id") or ""
            target = rid_to_target.get(rid, "")
            if not target:
                # リレーションが引けない場合は位置から推定する（壊れた xlsx への保険）
                target = f"worksheets/sheet{len(entries) + 1}.xml"
            path = target.lstrip("/") if target.startswith("/") else f"xl/{target}"
            entries.append((name, path))
    return entries


def _cell_text(cell: ET.Element, shared: list[str]) -> str:
    """1 個の `<c>` の表示値を返す。"""
    cell_type = cell.get("t")
    if cell_type == "inlineStr":
        return _text_of(_child_by_local(cell, "is"))

    v = _child_by_local(cell, "v")
    raw = (v.text or "") if v is not None else ""
    if cell_type == "s":
        try:
            return shared[int(raw)]
        except (ValueError, IndexError):
            return raw  # 壊れた参照は生の数字を出す（黙って消さない）
    if cell_type == "b":
        return {"1": "TRUE", "0": "FALSE"}.get(raw, raw)
    return raw


def _grid_and_merges(zf: zipfile.ZipFile, sheet_path: str, shared: list[str]):
    root = ET.fromstring(zf.read(sheet_path))
    cells: dict[tuple[int, int], str] = {}
    merges: list[str] = []

    row_seq = -1
    for row in root.iter():
        if _local(row.tag) == "row":
            row_seq += 1
            row_idx = int(row.get("r")) - 1 if (row.get("r") or "").isdigit() else row_seq
            col_seq = -1
            for cell in row:
                if _local(cell.tag) != "c":
                    continue
                col_seq += 1
                ref = cell.get("r") or ""
                pos = _cell_ref(ref) if ref else None
                r_idx, c_idx = pos if pos else (row_idx, col_seq)
                text = _cell_text(cell, shared)
                if text != "":
                    cells[(r_idx, c_idx)] = text
        elif _local(row.tag) == "mergeCell":
            ref = row.get("ref")
            if ref:
                merges.append(ref)

    return cells, merges


def _apply_merges(cells: dict[tuple[int, int], str], merges: list[str]) -> None:
    """結合セルの左上値を範囲全体へ複製する（人が見る見た目に寄せる近似）。

    厳密には「左上だけが値を持つ」が、そのまま出すと結合タイトル行が
    第 1 列にしか見えず、表として読めないため。
    """
    for ref in merges:
        if ":" not in ref:
            continue
        start_s, end_s = ref.split(":", 1)
        start = _cell_ref(start_s)
        end = _cell_ref(end_s)
        if not (start and end):
            continue
        (r0, c0), (r1, c1) = start, end
        anchor = cells.get((r0, c0), "")
        if not anchor:
            continue
        for r in range(min(r0, r1), max(r0, r1) + 1):
            for c in range(min(c0, c1), max(c0, c1) + 1):
                cells.setdefault((r, c), anchor)


def _squash(text: str) -> str:
    """セル内の改行・タブを空白へ潰す（TSV の行構造を守るため）。"""
    return text.replace("\t", " ").replace("\r", " ").replace("\n", " ").strip()


def _inline(text: str) -> str:
    """疎表示用。セル内改行を ` / ` へ畳む（1 行 = 1 レコードを守りつつ内容を落とさない）。"""
    return _squash(text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", " / "))


def _col_letters(index: int) -> str:
    """0 起点の列番号 → 列記号（0→A, 25→Z, 26→AA）。"""
    letters = ""
    value = index + 1
    while value > 0:
        value, rem = divmod(value - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def _used_extent(cells: dict[tuple[int, int], str]) -> tuple[int, int]:
    """(使用行数, 使用列数)。空なら (0, 0)。"""
    if not cells:
        return 0, 0
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _render_grid(
    cells: dict[tuple[int, int], str],
    fill_merges: bool,
    merges: list[str],
) -> list[str]:
    """タブ区切りの格子。空行・空列を保持する（位置が意味を持つ表のため）。"""
    if fill_merges:
        _apply_merges(cells, merges)
    if not cells:
        return []
    max_row, max_col = _used_extent(cells)
    lines: list[str] = []
    for r in range(max_row):
        row = [_squash(cells.get((r, c), "")) for c in range(max_col)]
        while row and row[-1] == "":
            row.pop()
        lines.append("\t".join(row))
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def _render_sparse(cells: dict[tuple[int, int], str]) -> list[str]:
    """非空セルだけを `rN  A:値 | B:値` で出す（設計書を読むための既定形式）。

    設計書のシートは 1 つの論理セルが横に何十列も結合されていることが多く、
    格子で出すと「同じ値が 20 個並ぶ」だけで読めない。空セルを落とすと
    1 行 = 1 レコードになり、表としてそのまま読める。
    """
    rows: dict[int, list[tuple[int, str]]] = {}
    for (r, c), text in cells.items():
        if text != "":
            rows.setdefault(r, []).append((c, text))
    lines: list[str] = []
    for r in sorted(rows):
        items = " | ".join(f"{_col_letters(c)}:{_inline(t)}" for c, t in sorted(rows[r]))
        lines.append(f"r{r + 1}\t{items}")
    return lines


# ---------------------------------------------------------------------------
# 公開 API
# ---------------------------------------------------------------------------


def _open(path: Path | str) -> zipfile.ZipFile:
    p = Path(path)
    if not p.is_file():
        raise LegacyToolError(f"ファイルがありません: {p}")
    try:
        return zipfile.ZipFile(p)
    except zipfile.BadZipFile as exc:
        raise LegacyToolError(f".xlsx（zip）として読めません: {p}") from exc


def sheet_names(path: Path | str) -> list[str]:
    """シート名をワークブック定義順に返す。"""
    with _open(path) as zf:
        return [name for name, _ in _sheet_entries(zf)]


def sheet_text(
    path: Path | str,
    sheet: str | None = None,
    index: int | None = None,
    mode: str = "sparse",
    fill_merges: bool = False,
    show_merge: bool = False,
) -> str:
    """1 シートをテキストへ変換する。

    `sheet`（名前）と `index`（0 起点）は排他。どちらも省略時は先頭シート。
    `mode` は `sparse`（既定・非空セルのみ）または `grid`（タブ区切りの格子）。
    `fill_merges` は `grid` のときだけ意味を持ち、既定は無効
    （結合の複製は「無いセル」を作るため、読むときの既定は忠実側に倒す）。
    """
    if sheet is not None and index is not None:
        raise LegacyToolError("--sheet と --sheet-index は同時に指定できません")
    if mode not in ("sparse", "grid"):
        raise LegacyToolError(f"未知の mode: {mode}（sparse / grid）")

    with _open(path) as zf:
        entries = _sheet_entries(zf)
        if not entries:
            raise LegacyToolError(f"シートがありません: {path}")

        if sheet is not None:
            target = next((e for e in entries if e[0] == sheet), None)
            if target is None:
                raise LegacyToolError(
                    f"シート '{sheet}' がありません。存在するシート: {[e[0] for e in entries]}"
                )
        elif index is not None:
            if not 0 <= index < len(entries):
                raise LegacyToolError(f"シート番号 {index} は範囲外（0〜{len(entries) - 1}）")
            target = entries[index]
        else:
            target = entries[0]

        name, sheet_path = target
        shared = _parse_shared_strings(zf)
        if sheet_path not in zf.namelist():
            raise LegacyToolError(f"シート XML が zip 内にありません: {sheet_path}")
        cells, merges = _grid_and_merges(zf, sheet_path, shared)

    n_rows, n_cols = _used_extent(cells)
    if mode == "grid":
        body = _render_grid(dict(cells), fill_merges, merges)
    else:
        body = _render_sparse(cells)

    header = [f"# sheet: {name}  rows={n_rows} cols={n_cols} mode={mode}"]
    if show_merge and merges:
        header.append(f"# merged: {' '.join(merges)}")
    return "\n".join([*header, *body])


def workbook_text(
    path: Path | str,
    sheet: str | None = None,
    index: int | None = None,
    mode: str = "sparse",
    fill_merges: bool = False,
    show_merge: bool = False,
) -> str:
    """全シート（または指定 1 シート）を 1 本のテキストへ連結する。"""
    kwargs = {"mode": mode, "fill_merges": fill_merges, "show_merge": show_merge}
    if sheet is not None or index is not None:
        return sheet_text(path, sheet=sheet, index=index, **kwargs)
    with _open(path) as zf:
        names = [name for name, _ in _sheet_entries(zf)]
    return "\n\n".join(sheet_text(path, index=i, **kwargs) for i in range(len(names)))


# ---------------------------------------------------------------------------
# 脱敏（红线⑦）
# ---------------------------------------------------------------------------


def load_mask_mapping(root: Path):
    """脱敏辞書を読む。辞書が無ければ `MaskUnavailable`（未マスク出力を黙って作らない）。"""
    from tools.masking.mask_demo import DICT_NAME, load_dict

    path = root / "tools" / "masking" / DICT_NAME
    if not path.is_file():
        raise MaskUnavailable(
            f"--mask が指定されましたが脱敏辞書がありません: {path}\n"
            f"  辞書なしで出力すると未マスクの実値が外へ出ます（紅线⑦）。\n"
            f"  対処: 辞書を用意する / --mask を外す（社内に留まる出力なら不要）。"
        )
    return load_dict(path)


def mask_text_with(text: str, root: Path) -> str:
    """`tools.masking` の規格でテキストを脱敏する。"""
    from tools.masking.mask_demo import mask_text

    return mask_text(text, load_mask_mapping(root))


def read_workbook(
    path: Path | str,
    mode: str = "sparse",
    show_merge: bool = False,
) -> list[tuple[str, str]]:
    """`[(シート名, テキスト)]` を定義順に返す（シート単位でファイルを分けたい CLI 用）。"""
    with _open(path) as zf:
        names = [name for name, _ in _sheet_entries(zf)]
    return [
        (name, sheet_text(path, index=i, mode=mode, show_merge=show_merge))
        for i, name in enumerate(names)
    ]


# CLI の正規の入口は `py -3 -m tools.legacy`（`__main__.py`）。
# ただし計画に記載した `py -3 -m tools.legacy.xlsx_text` も同じ動作をしなければならない。
# 「-m で実行しても黙って何もしない」が最も危険（Exit 0 なのに検証が走っていない）ため、
# ここから明示的に CLI へ委譲する。
if __name__ == "__main__":  # pragma: no cover
    from .__main__ import main

    raise SystemExit(main())

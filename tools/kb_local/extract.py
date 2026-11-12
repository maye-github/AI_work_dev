"""案件の原資料（Excel / Word / PDF）をテキスト化し、**検査用の統計**を返す。

なぜ統計を返すのか
------------------
抽出は必ず何かを落とす（結合セル・脚注・図の中の文字）。人が 50 ページを通読して
確かめるのは続かないので、**「どこが危ないか」を先に出す**。人は報告を見て、
怪しい所だけ原本と突き合わせればよい。

対応
----
| 形式 | 方式 | 依存 |
|---|---|---|
| `.xlsx` | `tools.legacy` の標準ライブラリ抽出器 | なし |
| `.docx` | zip + `word/document.xml` を標準ライブラリで解析 | なし |
| `.pdf` | `pdftotext`（poppler） | **外部コマンド**。無ければ明示的に失敗 |
| `.md` / `.txt` | そのまま読む | なし |

★ 抽出は**忠実に**行う（要約しない）。要約すると原文との対応が切れ、限定句も落ちる。
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

SUPPORTED = (".xlsx", ".docx", ".pdf", ".md", ".txt")
_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def extract(path: Path) -> dict:
    """`{"text", "method", "stats", "warnings"}` を返す。未対応形式は `SystemExit`。"""
    suffix = path.suffix.lower()
    if suffix == ".xlsx":
        return _xlsx(path)
    if suffix == ".docx":
        return _docx(path)
    if suffix == ".pdf":
        return _pdf(path)
    if suffix in (".md", ".txt"):
        text = path.read_text(encoding="utf-8", errors="replace")
        return {"text": text, "method": "text", "stats": {"chars": len(text)},
                "warnings": [] if len(text) >= 200 else ["内容が極端に少ない"]}
    raise SystemExit(
        f"[import] 対応していない形式です: {suffix}"
        f"（対応: {' / '.join(s.lstrip('.') for s in SUPPORTED)}）"
    )


def _merge_count(path: Path) -> int:
    """ブック全体の結合セル数。**結合は内容が落ちる最大の原因**なので数える。"""
    total = 0
    try:
        with zipfile.ZipFile(path) as zf:
            for name in zf.namelist():
                if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"):
                    total += zf.read(name).count(b"<mergeCell ")
    except (OSError, zipfile.BadZipFile):
        return 0
    return total


def _xlsx(path: Path) -> dict:
    from tools.legacy import xlsx_text

    names = xlsx_text.sheet_names(path)
    parts: list[str] = []
    empty: list[str] = []
    rows = 0
    for name in names:
        body = xlsx_text.sheet_text(path, sheet=name, mode="grid").strip()
        if not body:
            empty.append(name)
            continue
        rows += len(body.splitlines())
        parts.append(f"## シート: {name}\n\n{body}")
    if not parts:
        raise SystemExit(f"[import] 取り出せる内容がありません（空のブック？）: {path}")

    text = "\n\n".join(parts)
    merges = _merge_count(path)
    warnings: list[str] = []
    if merges:
        warnings.append(f"結合セル {merges} 箇所 — 結合された内容が落ちていないか確認してください")
    if empty:
        warnings.append("空のシート: " + ", ".join(empty))
    return {
        "text": text,
        "method": "stdlib-xlsx",
        "stats": {"sheets": len(names), "rows": rows, "merges": merges, "chars": len(text)},
        "warnings": warnings,
    }


def _docx(path: Path) -> dict:
    with zipfile.ZipFile(path) as zf:
        try:
            xml = zf.read("word/document.xml")
        except KeyError:
            raise SystemExit(f"[import] Word の本文が見つかりません: {path}")
    root = ET.fromstring(xml)

    # 表の中の段落は「段落」としては出さない（表として別に出すので二重になる）。
    in_table = {id(p) for tbl in root.iter(f"{_W}tbl") for p in tbl.iter(f"{_W}p")}

    lines: list[str] = []
    paragraphs = 0
    for para in root.iter(f"{_W}p"):
        if id(para) in in_table:
            continue
        text = "".join(node.text or "" for node in para.iter(f"{_W}t")).strip()
        if text:
            lines.append(text)
            paragraphs += 1

    tables = 0
    ragged = 0
    for table in root.iter(f"{_W}tbl"):
        tables += 1
        widths: set[int] = set()
        for row in table.iter(f"{_W}tr"):
            cells = ["".join(n.text or "" for n in c.iter(f"{_W}t")).strip()
                     for c in row.iter(f"{_W}tc")]
            widths.add(len(cells))
            if any(cells):
                lines.append("| " + " | ".join(cells) + " |")
        if len(widths) > 1:
            ragged += 1

    if not lines:
        raise SystemExit(f"[import] 取り出せる内容がありません: {path}")

    text = "\n\n".join(lines)
    warnings: list[str] = []
    if ragged:
        warnings.append(f"列数が揃わない表 {ragged} 件 — 表が崩れていないか確認してください")
    if len(text) < 200:
        warnings.append("抽出が極端に短い — 図や画像だけの可能性があります")
    return {
        "text": text,
        "method": "stdlib-docx",
        "stats": {"paragraphs": paragraphs, "tables": tables,
                  "ragged_tables": ragged, "chars": len(text)},
        "warnings": warnings,
    }


def _pdf(path: Path) -> dict:
    exe = shutil.which("pdftotext")
    if not exe:
        raise SystemExit(
            "[import] PDF を読むには `pdftotext`（poppler）が必要です。\n"
            "         無い場合は PDF を Word かテキストに変換してから取り込んでください。"
        )
    # ★ Windows の pdftotext（mingw 版）は日本語・中国語のパスを開けない
    #   （実測: `I/O Error: Couldn't open file ...?<93>_1_...`）。ASCII の一時パスへ複製する。
    with tempfile.TemporaryDirectory() as tmp:
        tmp_pdf = Path(tmp) / "input.pdf"
        shutil.copy2(path, tmp_pdf)
        result = subprocess.run(
            [exe, "-layout", "-enc", "UTF-8", str(tmp_pdf), "-"],
            capture_output=True, encoding="utf-8", errors="replace",
        )
    if result.returncode != 0:
        raise SystemExit(f"[import] pdftotext が失敗しました（Exit {result.returncode}）: {path}")

    text = result.stdout.strip()
    if not text:
        raise SystemExit(
            f"[import] 文字を取り出せませんでした（スキャン PDF の可能性）: {path}\n"
            "         画像だけの PDF は、人が文字起こしするか、元の Word / Excel を入手してください。"
        )
    warnings = [] if len(text) >= 200 else ["抽出が極端に短い — 図だけのページが多い可能性"]
    return {"text": text, "method": "pdftotext",
            "stats": {"chars": len(text)}, "warnings": warnings}

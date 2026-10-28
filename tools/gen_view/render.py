"""gen_view — 節点成果物（機読源 .md）を人向け HTML ビューへ変換する。

【位置づけ：これは「生成物」であり、機読源ではない】
  機読源は .md / .yaml のまま。本ツールはそれを**読むだけ**で、書き戻さない。
  生成された .html を手で編集してはならない（gen_formal と同じ単一ソース原則、FR-3）。
  人から出た修正は必ず機読源へ入れ、本ツールで再生成する。

【なぜ必要か】
  節点成果物の .md は「機読源」と「人看版」を兼ねている。
  機読源は全・省略なし・来源付きが正しいが、そのままでは 6 列の広い表が
  折り返されず、肉眼でのレビューがつらい。本ツールは同じ .md から
  閲覧専用の HTML を作ることで、機読源は一切変えずに可読性だけを上げる。

【Phase1 の制限】
  入力は .md（人が読む方）のみ。.yaml からの直接レンダリングは Phase2 で対応する。

【依存】
  標準ライブラリのみ。CSS は埋め込み（外部リソース非依存、NFR-6）。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import html
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

# --- セクション種別（見出しキーワード → 色分け用 class） ----------------------
# 上から順に評価し、最初に一致したものを採用する。順序に意味がある。
_SECTION_RULES: tuple[tuple[str, str], ...] = (
    ("待確認", "ask"),
    ("確認事項", "ask"),
    ("待确认", "ask"),
    ("确认", "ask"),
    ("open issue", "ask"),
    # 受入は「ご確認」より具体的なので先に評価する（"受入条件のご確認" を acc にする）
    ("受入", "acc"),
    ("確認依頼", "ask"),
    ("決定いただきたい", "ask"),
    ("ご確認", "ask"),
    ("non-goals", "ng"),
    ("non goals", "ng"),
    ("不做", "ng"),
    ("異常", "err"),
    ("錯誤", "err"),
    ("异常", "err"),
    ("错误", "err"),
    ("背景", "bg"),
    ("業務規則", "br"),
    ("业务规则", "br"),
    ("規則", "br"),
    ("规则", "br"),
    ("輸入", "io"),
    ("输入", "io"),
    ("輸出", "io"),
    ("输出", "io"),
    ("トレーサ", "trace"),
    ("生成メモ", "meta"),
)

_CHIPS: dict[str, str] = {
    "ask": "★ 要拍板",
    "ng": "範囲外",
    "err": "異常",
    "bg": "前提",
    "br": "業務規則",
    "io": "項目定義",
    "acc": "合格条件",
    "trace": "追跡",
    "meta": "メモ",
}

# 中文ビュー用のチップ表記。媒体規約（規則 00 §12）により `.zh.html` は**中文のみ**なので、
# 画面の付属文言も中文にする。**実装値（画面文言・項目名）は翻訳しない**——これは
# ビューの操作性文言だけを対象にする。
_CHIPS_ZH: dict[str, str] = {
    "ask": "★ 待拍板",
    "ng": "范围外",
    "err": "异常",
    "bg": "前提",
    "br": "业务规则",
    "io": "项目定义",
    "acc": "合格条件",
    "trace": "追踪",
    "meta": "备注",
}

# HTML の chrome（lang / 目次 / 入力元・生成の表示 / 警告帯 / フッタ）。
# 本文は翻訳しない。ここだけを言語で切り替える。
_UI: dict[str, dict[str, str]] = {
    "ja": {
        "toc": "目次",
        "src": "機読源",
        "gen": "生成",
        "sec": "セクション",
        "tbl": "表",
        "warn": (
            "⚠️ 本ページは機読源 (<code>{n}</code>) から自動生成された"
            "<strong>閲覧専用ビュー</strong>です。この HTML を直接編集しないでください。"
            "修正は必ず機読源に入れ、再生成してください（単一ソース原則 / FR-3）。"
        ),
        "print": "印刷 (Ctrl+P) で PDF 化できます。",
        "foot": (
            "このビューは <code>tools/gen_view</code> が生成しました。機読源は "
            "<code>{n}</code> です。人からの指摘は「指摘シート／レビュー欄」へ。"
        ),
    },
    "zh": {
        "toc": "目录",
        "src": "机读源",
        "gen": "生成",
        "sec": "节",
        "tbl": "表",
        "warn": (
            "⚠️ 本页由机读源 (<code>{n}</code>) 自动生成，是<strong>仅供阅读的视图</strong>。"
            "请勿直接修改本 HTML。修改一律写回机读源后重新生成（单一来源原则 / FR-3）。"
        ),
        "print": "按 Ctrl+P 可存为 PDF。",
        "foot": (
            "本视图由 <code>tools/gen_view</code> 生成，机读源是 <code>{n}</code>。"
            "来自人的意见请写进「指摘单／评审栏」。"
        ),
    },
}

# 表の第 1 列見出しに含まれる語 → 表の class（行の色分け）
_TABLE_KINDS: tuple[tuple[str, str], ...] = (
    ("q-", "tbl-ask"),
    ("異常", "tbl-err"),
    ("錯誤", "tbl-err"),
    ("錯誤 id", "tbl-err"),
    ("non-goal", "tbl-ng"),
)

# --- インライン記法 ---------------------------------------------------------
_INLINE_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

# 表セル内のエスケープされたパイプ \| を退避させるための番兵
_PIPE_SENTINEL = "\u0000PIPE\u0000"
_PIPE_ESCAPE = re.compile(r"\\\|")

_HR = re.compile(r"^(?:-{3,}|\*{3,}|_{3,})$")
_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_UL_ITEM = re.compile(r"^\s*[-*+]\s+(.*)$")
_OL_ITEM = re.compile(r"^\s*\d+[.)]\s+(.*)$")
_CHECKBOX = re.compile(r"^\[([ xX])\]\s*(.*)$")
_TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(?:\|\s*:?-{2,}:?\s*)*\|?\s*$")
_TABLE_SEP_CELL = re.compile(r"^\s*:?-{2,}:?\s*$")


def _inline(text: str) -> str:
    """インライン記法を HTML へ。先にエスケープしてから自前の記法だけ戻す。"""
    out = html.escape(text, quote=False)
    out = _INLINE_CODE.sub(lambda m: f"<code>{m.group(1)}</code>", out)
    out = _BOLD.sub(lambda m: f"<strong>{m.group(1)}</strong>", out)
    out = _LINK.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', out)
    return out


def _section_kind(title: str) -> str:
    low = title.lower()
    for key, kind in _SECTION_RULES:
        if key in low:
            return kind
    return "plain"


def _split_row(line: str) -> list[str]:
    """パイプ表の 1 行をセルへ分解する。\\| はセル内の文字として扱う。"""
    row = _PIPE_ESCAPE.sub(_PIPE_SENTINEL, line.strip())
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|"):
        row = row[:-1]
    return [c.replace(_PIPE_SENTINEL, "|").strip() for c in row.split("|")]


def _aligns(sep_cells: list[str]) -> list[str]:
    out = []
    for cell in sep_cells:
        cell = cell.strip()
        if cell.startswith(":") and cell.endswith(":"):
            out.append("center")
        elif cell.endswith(":"):
            out.append("right")
        else:
            out.append("left")
    return out


def _table_kind(header: list[str]) -> str:
    if not header:
        return ""
    first = header[0].lower()
    for key, cls in _TABLE_KINDS:
        if key in first:
            return cls
    return ""


def _render_table(rows: list[str]) -> str:
    header = _split_row(rows[0])
    aligns = _aligns(_split_row(rows[1]))
    body = [_split_row(r) for r in rows[2:]]
    # 列数が合わない行は末尾を空で埋める（不完全な表でも落とさない）
    width = len(header)
    for r in body:
        while len(r) < width:
            r.append("")

    kind = _table_kind(header)
    cls = "tbl" + (f" {kind}" if kind else "")

    def cell(tag: str, text: str, idx: int) -> str:
        align = aligns[idx] if idx < len(aligns) else "left"
        return f'<{tag} style="text-align:{align}">{_inline(text)}</{tag}>'

    parts = [f'<table class="{cls}">', "<thead><tr>"]
    parts += [cell("th", h, i) for i, h in enumerate(header)]
    parts.append("</tr></thead>")
    if body:
        parts.append("<tbody>")
        for r in body:
            parts.append("<tr>")
            parts += [cell("td", c, i) for i, c in enumerate(r)]
            parts.append("</tr>")
        parts.append("</tbody>")
    parts.append("</table>")
    return "".join(parts)


def _block_kind(lines: list[str]) -> str:
    """引用ブロックの見た目を絵文字で判定する。"""
    joined = "\n".join(lines)
    if "⚠️" in joined:
        return "warn"
    if "💡" in joined:
        return "tip"
    if "👉" in joined:
        return "hint"
    return ""


def _starts_block(lines: list[str], i: int) -> bool:
    """i 行目が新しいブロックの開始かどうか（段落の終端判定）。"""
    line = lines[i]
    s = line.strip()
    if not s or s.startswith("#") or s.startswith(">") or s.startswith("```"):
        return True
    if _HR.match(s) or _UL_ITEM.match(line) or _OL_ITEM.match(line):
        return True
    if "|" in line and i + 1 < len(lines) and _TABLE_SEP.match(lines[i + 1]):
        return True
    return False


def render_markdown(text: str, chips: dict[str, str] | None = None,
                    ) -> tuple[str, list[tuple[str, str, str]]]:
    """Markdown 本文を HTML 断片へ変換する。

    戻り値: (body_html, toc)。toc は (anchor, title, kind) のリスト。

    `chips` は h2 見出しのチップ表記（kind → 表示文字列）。**言語で切り替わる**ため
    引数で受ける。既定は日本語。中文ビュー（`.zh.html`）では `_CHIPS_ZH` を渡すこと——
    ここを `_CHIPS` 固定にすると、目次（nav）は中文・見出しは日本語という
    **同一ページ内の言語混在**になる（2026-10-27 修正。媒体規約 `rules/00` §12）。
    """
    chip_table = chips if chips is not None else _CHIPS
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out: list[str] = ['<section class="sec sec-lead">']
    toc: list[tuple[str, str, str]] = []
    n = len(lines)
    i = 0
    sec_no = 0

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # --- コードフェンス ---
        if stripped.startswith("```"):
            buf: list[str] = []
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append("<pre><code>" + html.escape("\n".join(buf)) + "</code></pre>")
            continue

        # --- 空行 ---
        if not stripped:
            i += 1
            continue

        # --- 水平線 ---
        if _HR.match(stripped):
            out.append("<hr>")
            i += 1
            continue

        # --- 見出し ---
        m = _HEADING.match(stripped)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            if level == 2:
                out.append("</section>")
                sec_no += 1
                kind = _section_kind(title)
                anchor = f"sec-{sec_no}"
                toc.append((anchor, title, kind))
                out.append(f'<section class="sec sec-{kind}" id="{anchor}">')
                chip = chip_table.get(kind, "")
                chip_html = f' <span class="chip chip-{kind}">{chip}</span>' if chip else ""
                out.append(f"<h2>{_inline(title)}{chip_html}</h2>")
            else:
                out.append(f"<h{level}>{_inline(title)}</h{level}>")
            i += 1
            continue

        # --- 引用 ---
        if stripped.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            kind = _block_kind(buf)
            cls = "quote" + (f" {kind}" if kind else "")
            inner = "<br>".join(_inline(b) for b in buf if b.strip())
            out.append(f'<blockquote class="{cls}">{inner}</blockquote>')
            continue

        # --- 箇条書き（チェックボックス対応） ---
        if _UL_ITEM.match(line):
            items = []
            while i < n and _UL_ITEM.match(lines[i]):
                items.append(_UL_ITEM.match(lines[i]).group(1))
                i += 1
            rendered = []
            for item in items:
                mbox = _CHECKBOX.match(item)
                if mbox:
                    mark = "☑" if mbox.group(1).lower() == "x" else "☐"
                    cls = "task done" if mbox.group(1).lower() == "x" else "task"
                    rendered.append(
                        f'<li class="{cls}"><span class="box">{mark}</span>'
                        f"{_inline(mbox.group(2))}</li>"
                    )
                else:
                    rendered.append(f"<li>{_inline(item)}</li>")
            out.append("<ul>" + "".join(rendered) + "</ul>")
            continue

        # --- 番号付きリスト ---
        if _OL_ITEM.match(line):
            items = []
            while i < n and _OL_ITEM.match(lines[i]):
                items.append(_OL_ITEM.match(lines[i]).group(1))
                i += 1
            out.append("<ol>" + "".join(f"<li>{_inline(x)}</li>" for x in items) + "</ol>")
            continue

        # --- 表 ---
        if "|" in line and i + 1 < n and _TABLE_SEP.match(lines[i + 1]):
            rows = [line, lines[i + 1]]
            i += 2
            while i < n and lines[i].strip().startswith("|"):
                rows.append(lines[i])
                i += 1
            out.append(_render_table(rows))
            continue

        # --- 段落 ---
        buf = [stripped]
        i += 1
        while i < n and not _starts_block(lines, i):
            buf.append(lines[i].strip())
            i += 1
        out.append("<p>" + "<br>".join(_inline(x) for x in buf) + "</p>")

    out.append("</section>")
    return "\n".join(out), toc


_CSS = """
:root{
  --fg:#1f2328; --muted:#6b7280; --line:#e5e7eb; --bg:#fff; --soft:#f9fafb;
  --ask:#b45309; --ask-bg:#fffbeb; --ask-bd:#fcd34d;
  --err:#b91c1c; --err-bg:#fef2f2; --err-bd:#fca5a5;
  --ng:#4b5563;  --ng-bg:#f9fafb;  --ng-bd:#d1d5db;
  --bgc:#1d4ed8; --bgc-bg:#eff6ff; --bgc-bd:#bfdbfe;
  --br:#047857;  --br-bg:#ecfdf5;  --br-bd:#a7f3d0;
  --io:#6d28d9;  --io-bg:#f5f3ff;  --io-bd:#ddd6fe;
  --acc:#0f766e; --trace:#0369a1; --meta:#6b7280;
}
*{box-sizing:border-box}
body{
  margin:0; padding:28px 20px 80px; background:var(--bg); color:var(--fg);
  font-family:"Yu Gothic UI","Meiryo",system-ui,-apple-system,"Segoe UI",
              "Microsoft YaHei",sans-serif;
  font-size:15px; line-height:1.75;
}
.wrap{max-width:1180px;margin:0 auto}
.banner{
  border:1px solid var(--line); border-left:4px solid var(--io); border-radius:8px;
  background:var(--soft); padding:14px 18px; margin-bottom:22px;
}
.banner h1{margin:0 0 6px; font-size:20px; line-height:1.4}
.banner .meta{color:var(--muted); font-size:12.5px}
.banner .warn-note{
  margin-top:10px; padding:8px 10px; border-radius:6px; font-size:12.5px;
  background:var(--ask-bg); border:1px solid var(--ask-bd); color:var(--ask);
}
nav.toc{
  border:1px solid var(--line); border-radius:8px; padding:12px 16px;
  margin-bottom:26px; background:#fff;
}
nav.toc .toc-title{font-weight:700; font-size:13px; color:var(--muted); margin-bottom:6px}
nav.toc ol{margin:0; padding-left:22px; columns:2; column-gap:28px}
nav.toc li{margin:2px 0; font-size:13.5px; break-inside:avoid}
nav.toc a{color:var(--fg); text-decoration:none; border-bottom:1px dotted var(--line)}
nav.toc a:hover{color:var(--io); border-bottom-color:var(--io)}
section.sec{
  margin:0 0 26px; padding:16px 20px; border-radius:8px;
  border:1px solid transparent; background:transparent;
}
section.sec-ask{background:var(--ask-bg); border-color:var(--ask-bd)}
section.sec-err{background:var(--err-bg); border-color:var(--err-bd)}
section.sec-ng{background:var(--ng-bg);  border-color:var(--ng-bd)}
section.sec-bg{background:var(--bgc-bg); border-color:var(--bgc-bd)}
section.sec-br{background:var(--br-bg);  border-color:var(--br-bd)}
section.sec-io{background:var(--io-bg);  border-color:var(--io-bd)}
section.sec-ask,section.sec-err,section.sec-bg,section.sec-br,section.sec-io{color:var(--fg)}
h2{
  font-size:18px; margin:0 0 12px; padding-bottom:8px;
  border-bottom:2px solid var(--line); line-height:1.45;
}
section.sec-ask h2{border-bottom-color:var(--ask-bd)}
section.sec-err h2{border-bottom-color:var(--err-bd)}
section.sec-bg h2{border-bottom-color:var(--bgc-bd)}
section.sec-br h2{border-bottom-color:var(--br-bd)}
section.sec-io h2{border-bottom-color:var(--io-bd)}
h3{font-size:15.5px; margin:18px 0 8px}
h4,h5,h6{font-size:14.5px; margin:14px 0 6px}
p{margin:8px 0}
hr{border:0; border-top:1px solid var(--line); margin:22px 0}
ul,ol{margin:8px 0; padding-left:24px}
li{margin:3px 0}
ul:has(li.task){list-style:none; padding-left:2px}
li.task{display:flex; gap:8px; align-items:flex-start; margin:6px 0}
li.task .box{flex:0 0 auto; font-size:15px; line-height:1.75; color:var(--io)}
li.task.done{color:var(--muted); text-decoration:line-through}
li.task.done .box{color:var(--br)}
code{
  background:#f1f3f5; border:1px solid var(--line); border-radius:4px;
  padding:0 4px; font-size:12.5px;
  font-family:"Cascadia Mono",Consolas,"Courier New",monospace;
}
pre{
  background:#f6f8fa; border:1px solid var(--line); border-radius:6px;
  padding:12px 14px; overflow:auto;
}
pre code{background:none; border:0; padding:0; font-size:12.5px; line-height:1.6}
blockquote{
  margin:12px 0; padding:10px 14px; border-left:4px solid var(--line);
  background:var(--soft); border-radius:0 6px 6px 0;
}
blockquote.warn{border-left-color:var(--ask-bd); background:var(--ask-bg); color:var(--ask)}
blockquote.tip{border-left-color:var(--br-bd); background:var(--br-bg)}
blockquote.hint{border-left-color:var(--io-bd); background:var(--io-bg)}
.chip{
  display:inline-block; vertical-align:middle; margin-left:8px; padding:1px 9px;
  border-radius:999px; font-size:11.5px; font-weight:700; letter-spacing:.02em;
  background:#fff; border:1px solid var(--line); color:var(--muted);
}
.chip-ask{background:var(--ask); border-color:var(--ask); color:#fff}
.chip-err{background:var(--err); border-color:var(--err); color:#fff}
.chip-ng{background:var(--ng);  border-color:var(--ng);  color:#fff}
.chip-bg{background:var(--bgc); border-color:var(--bgc); color:#fff}
.chip-br{background:var(--br);  border-color:var(--br);  color:#fff}
.chip-io{background:var(--io);  border-color:var(--io);  color:#fff}
.chip-acc{background:var(--acc); border-color:var(--acc); color:#fff}
.chip-trace{background:var(--trace); border-color:var(--trace); color:#fff}
table.tbl{
  width:100%; border-collapse:collapse; margin:12px 0; background:#fff;
  font-size:13.5px; table-layout:auto;
}
table.tbl th{
  background:#f1f3f5; border:1px solid var(--line); padding:8px 10px;
  font-weight:700; white-space:nowrap; position:sticky; top:0; z-index:1;
}
table.tbl td{
  border:1px solid var(--line); padding:8px 10px;
  vertical-align:top; word-break:break-word; overflow-wrap:anywhere;
}
table.tbl tbody tr:nth-child(even) td{background:#fcfcfd}
table.tbl tbody tr:hover td{background:#f5f9ff}
table.tbl td:first-child{white-space:nowrap; font-weight:600; color:#374151}
table.tbl-ask th{background:#fef3c7; border-color:var(--ask-bd)}
table.tbl-ask td{border-color:#fde68a}
table.tbl-err th{background:#fee2e2; border-color:var(--err-bd)}
table.tbl-err td{border-color:#fecaca}
table.tbl-ng th{background:#e5e7eb; border-color:var(--ng-bd)}
.foot{
  margin-top:34px; padding-top:14px; border-top:1px solid var(--line);
  color:var(--muted); font-size:12px;
}
@media print{
  body{padding:0; font-size:10.5pt}
  .noprint{display:none !important}
  nav.toc ol{columns:2}
  section.sec{break-inside:auto}
  table.tbl{font-size:9.5pt}
  table.tbl th{position:static}
  tr,li,blockquote{break-inside:avoid}
  .banner{background:#fff}
}
"""


def build_html(text: str, source: Path, title: str | None = None,
               lang: str | None = None) -> str:
    """Markdown 本文から単一ファイル HTML を組み立てる。

    `lang` を渡さない場合は、入力ファイル名が `*.zh.md` なら中文ビュー、それ以外は
    日本語ビューとして組み立てる（媒体規約: `.md`＝日文 / `.zh.html`＝中文）。
    """
    if lang is None:
        lang = "zh" if source.stem.endswith(".zh") else "ja"
    ui = _UI.get(lang, _UI["ja"])
    chips = _CHIPS_ZH if lang == "zh" else _CHIPS
    body, toc = render_markdown(text, chips=chips)
    doc_title = title or source.stem
    stamp = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")

    nav = ""
    if toc:
        items = "".join(
            f'<li><a href="#{a}">{html.escape(t)}</a>'
            + (f' <span class="chip chip-{k}">{chips[k]}</span>' if k in chips else "")
            + "</li>"
            for a, t, k in toc
        )
        nav = (
            f'<nav class="toc noprint"><div class="toc-title">{ui["toc"]}</div>'
            f"<ol>{items}</ol></nav>"
        )

    tables = body.count("<table class=")
    sections = max(len(toc), 1)
    srcname = html.escape(source.name)

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(doc_title)}</title>
<style>{_CSS}</style>
</head>
<body>
<div class="wrap">
<header class="banner">
<h1>{html.escape(doc_title)}</h1>
<div class="meta">
  {ui["src"]}: <code>{srcname}</code> ／
  {ui["gen"]}: {stamp} ／
  {ui["sec"]} {sections}・{ui["tbl"]} {tables}
</div>
<div class="warn-note">
  {ui["warn"].format(n=srcname)}
  <span class="noprint">{ui["print"]}</span>
</div>
</header>
{nav}
{body}
<div class="foot">
  {ui["foot"].format(n=srcname)}
</div>
</div>
</body>
</html>
"""


def _safe_stdout() -> None:
    """コンソールの文字コードを UTF-8 へ寄せる。

    日本語 Windows の既定は cp932 で、成果物パスに含まれる簡体字
    （例: 节点1_需求）を表現できず UnicodeEncodeError で落ちる。
    ファイル出力は常に UTF-8 なので、表示だけを寛容にする。
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


# --- self-test ---------------------------------------------------------------
_VOID_TAGS = frozenset({"br", "hr", "img", "meta", "link", "input", "col"})

_SELF_TEST_MD = """# 見出し1

> ⚠️ 注意事項

## 1. 待確認事項

| Q-ID | 内容 | 区分 |
|:--|:--|--:|
| Q-1 | テスト | Y |

## 2. 異常・錯誤一覧

| 錯誤 ID | 条件 |
|---|---|
| ERR-1 | x |

## 3. Non-Goals

| Non-Goal ID | 不做的事 |
|---|---|
| NG-1 | y |

- [ ] 未チェック項目
- [x] 済み項目
- ふつうの項目

1. いち
2. に

```python
print("hi")
```

| 右寄せ | 中央 | 左 |
|---:|:--:|:--|
| 1 | 2 | 3 |
"""


class _TagBalance(HTMLParser):
    """開始/終了タグの対応を検証する。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag not in _VOID_TAGS:
            self.stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag in _VOID_TAGS:
            return
        if not self.stack:
            self.errors.append(f"対応する開始タグがない </{tag}>")
        elif self.stack[-1] != tag:
            self.errors.append(f"入れ子不一致: </{self.stack[-1]}> を期待したが </{tag}>")
            if tag in self.stack:
                while self.stack and self.stack.pop() != tag:
                    pass
        else:
            self.stack.pop()


def _self_test() -> int:
    """全ブロック種別を網羅する固定入力で変換結果を検証する。"""
    body, toc = render_markdown(_SELF_TEST_MD)
    page = build_html(_SELF_TEST_MD, Path("selftest.md"), "self-test")
    # 中文ビュー: 目次（nav）と h2 チップの**両方**が中文であること。
    # h2 チップだけ日本語になる退行を捕まえる（2026-10-27 の不具合）。
    zh_page = build_html(_SELF_TEST_MD, Path("selftest.zh.md"), "self-test")
    ja_chips = {v for v in _CHIPS.values() if v not in set(_CHIPS_ZH.values())}
    zh_chips = {v for v in _CHIPS_ZH.values() if v not in set(_CHIPS.values())}
    checks: list[tuple[str, bool]] = [
        ("中文ビューに日本語チップが無い",
         not any(f'<span class="chip chip-{k}">{v}</span>' in zh_page
                 for k, v in _CHIPS.items() if v in ja_chips)),
        ("中文ビューのチップが中文", all(
            f'<span class="chip chip-{k}">{v}</span>' in zh_page
            for k, v in _CHIPS_ZH.items()
            if f'class="sec sec-{k}"' in zh_page)),
        ("日本語ビューに中文チップが無い",
         not any(f'<span class="chip chip-{k}">{v}</span>' in page
                 for k, v in _CHIPS_ZH.items() if v in zh_chips)),
    ]
    checks += [
        ("セクション数 == 3", len(toc) == 3),
        ("要拍板の色分け (sec-ask)", 'class="sec sec-ask"' in body),
        ("異常の色分け (sec-err)", 'class="sec sec-err"' in body),
        ("範囲外の色分け (sec-ng)", 'class="sec sec-ng"' in body),
        ("Q テーブルの強調 (tbl-ask)", "tbl-ask" in body),
        ("警告引用 (blockquote warn)", 'class="quote warn"' in body),
        ("未チェックボックス (☐)", "☐" in body),
        ("済チェックボックス (☑)", "☑" in body),
        ("コードフェンス", "<pre><code>" in body),
        ("右寄せの解釈", "text-align:right" in body),
        ("中央寄せの解釈", "text-align:center" in body),
        ("目次の生成", '<nav class="toc' in page),
        ("警告帯の常時表示", "閲覧専用ビュー" in page),
        ("機読源の書き戻しなし", "selftest.md" in page),
    ]
    balance = _TagBalance()
    balance.feed(page)
    balance.close()
    checks.append(("タグの対応（未閉じなし）", not balance.stack and not balance.errors))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"[gen_view:self-test] {'ok  ' if ok else 'FAIL'} {name}")
    for err in balance.errors + [f"未閉じ: {t}" for t in balance.stack]:
        print(f"[gen_view:self-test]   - {err}", file=sys.stderr)

    total = len(checks)
    if failed:
        print(f"[gen_view:self-test] FAIL {total - len(failed)}/{total} pass", file=sys.stderr)
        return 1
    print(f"[gen_view:self-test] PASS {total}/{total} pass")
    return 0


def main(argv: list[str] | None = None) -> int:
    _safe_stdout()
    parser = argparse.ArgumentParser(
        prog="python -m tools.gen_view",
        description="節点成果物の .md を人向け閲覧ビュー (HTML) へ変換する。",
    )
    parser.add_argument("source", nargs="?", help="節点成果物の .md パス")
    parser.add_argument("-o", "--out", help="出力 .html パス（既定: 入力と同名の .html）")
    parser.add_argument("--title", help="ページタイトル（既定: 入力ファイル名）")
    parser.add_argument("--self-test", action="store_true", help="内蔵フィクスチャで自己検証する")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()

    if not args.source:
        parser.error("source を指定するか --self-test を使ってください")

    src = Path(args.source)
    if not src.is_file():
        print(f"[gen_view] 入力が見つかりません: {src}", file=sys.stderr)
        return 2

    try:
        text = src.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        print(f"[gen_view] UTF-8 として読めません: {src}", file=sys.stderr)
        return 2

    out = Path(args.out) if args.out else src.with_suffix(".html")
    # 中文ビューの判定は「出力名が *.zh.html」または「入力名が *.zh.md」のどちらでも成立させる。
    # 出力名だけで判定すると `<file>.md -o <file>.zh.html` の使い方が中文にならず、
    # 入力名だけで判定すると `zh.md` を経由しない運用で日本語のままになる。
    lang = "zh" if out.name.endswith(".zh.html") or src.stem.endswith(".zh") else "ja"
    html_text = build_html(text, src, args.title, lang=lang)
    out.write_text(html_text, encoding="utf-8")

    print(f"[gen_view] rendered: {src} -> {out}")
    print(
        f"[gen_view] sections={html_text.count('<h2>')} "
        f"tables={html_text.count('<table class=')}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

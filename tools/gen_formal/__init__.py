"""gen_formal - 機読成果物 → 日文正式 Excel の二重化ツール。

落地篇 PPT S24「成果物の二重化」の実装:
  機読源（Markdown/YAML）──変換──▶ 対外成果物（日文正式 Excel/Word）

入口は 2 つ:
  - `gen_excel` : I-ID 数と列名の検証（既定 dry-run。.xlsx は作らない）
  - `book`      : Markdown を「基本設計書（画面編）」体裁の .xlsx へ描く
                  （`--out` を渡したときだけ生成。出力は `reports/` 配下に限る）

`docs/**` へは書かない（CP-R-3: `docs/**/*.xlsx == 0`）。
手で日文 Excel を編集してはならない（生成し直すと消える）。

API は `tools.gen_formal.gen_excel` / `tools.gen_formal.book` から直接 import する
（`python -m tools.gen_formal.gen_excel` 等を壊さないため、ここでは再エクスポートしない）。
"""

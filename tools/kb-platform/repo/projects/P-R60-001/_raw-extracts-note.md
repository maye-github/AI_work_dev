---
id: KNOW-LEGACY-R60-RAW-NOTE
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 1.0.0
doc_id: r60-001-raw-extracts-note
scope: project
project_id: P-R60-001
title: 原本テキスト（抽出物）はどこへ行ったか
doc_type: howto
conf_level: 30
updated_at: '2026-10-28'
---

# 原本テキスト（抽出物）はどこへ行ったか

2026-10-28 の断舍離で、**「一度きりの抽出物」だけ**を削除した。
結論（手引 13 本・モジュール知識 36 本・画面カード 9 本）は本知識庫に残っている。
原本が必要になったら、以下で取り戻せる。

| 削除したもの | 中身 | 取り戻し方 |
|---|---|---|
| `reports/module-survey/<module>/design/*.txt`・`test/*.txt` | 13 モジュールの旧設計書・単体テスト仕様の Sheet 抽出（211 個） | `git show keep/before-cleanup-2026-10-28:<path>` ／ または `py -3 -m tools.legacy <xlsx>` で再抽出 |
| `reports/legacy-raw/R60Area/{design,unittest}/*.txt` | R60Area の抽出（29 個） | 同上 |
| `reports/ingest/JET-R60/*` | 取入の試跑結果（7 個） | `py -3 -m tools.ingest` を再実行 |
| `reports/survey/prj01-logistics-*` | 別リポジトリ（物流案件）の清点（2 個） | そのリポジトリ側にある。本骨架の資産ではない |

## 残したもの（削除していない）

- `reports/module-survey/scores/*.yaml`（13 枚の調査票）… 教材モジュール選型の根拠
- `reports/module-survey/design-sheets.tsv`・`impl-size.json`・`ab-status.json` … 機械集計の結果
- チャンク生成器 6 本 → `tools/legacy/chunkers/<module>_make_chunks.py`（`tools/kb-platform/repo/projects/P-R60-001/chunks/raw/*.jsonl` を作り直せる唯一の手段）

## 注意：`source_path` は削除前のパスを指したまま

モジュール知識 YAML と画面カードの `source_path` は、**抽出した原文の所在記録**として削除前のパスを保持している。
そのため現在そのパスは存在しない。原文を点検するときは上の tag から復元すること。

- 出典を「ファイルがあること」で確かめたい場合は復元する。
- 出典を「どの版の設計書から取ったか」で確かめたい場合は記録のままでよい。

## なぜ消したか

`docs/90_knowledge/review_diff_assets/_skeleton/review_comments.md` の RC-SK 系と同じ理由である。
**同じ結論が二箇所（抽出物と手引）にあると、どちらが正か判別できなくなる**（成果物 6 原則 ④ 単一ソース）。
抽出物は「結論を作るための材料」であり、材料は結論に吸収された時点で役目を終える。

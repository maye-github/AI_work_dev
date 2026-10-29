---
id: RD-R60Item-AFTER
type: review-diff-asset-snapshot
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-review-r60item-review-after-readme
scope: project
project_id: P-R60-001
title: R60Item review_after（審査後スナップショット）
doc_type: decision
conf_level: 30
updated_at: '2026-10-28'
---

# R60Item review_after（審査後スナップショット）

> 本ディレクトリは審査差分資産 `RD-R60Item` の **審査後スナップショット** の保管場所（プレースホルダ）。
> 実物は キックオフ週の棚卸しで格納する。現時点ではファイルは置かない。

## このディレクトリに置くもの

- レビュー指摘を反映した**是正後（審査後）の最終版**の設計・コード。
- ファイル名は `review_before/` と同名にし、1 対で 1 指摘を構成する。
  - 例: `RC-I01_key-duplicate.py`、`RC-I03_zenkaku-numeric.py`。
- 「最終版」は審査を通過した版を指し、途中版は置かない（対の意味が失われるため）。

## 実物の入手元

- `D:\AI_work\doc\00_管理` 配下の【QA票】/【修正依頼】の**回答・是正方針**、およびその反映結果。
- Git 履歴（指摘対応コミットの**直後**のバージョン、またはマージ後の最新版）。

## 機密則（必ず守る）

- 実顧客名・実業務データ値・接続情報・パスワード・実 IP・実社員名は**絶対にコミットしない**。
- 値が必要な箇所は `COL_1` / `VAL_1` 等の占位（プレースホルダ）に置換する。
- 投入前に `py -3 tools/masking/mask_demo.py --self-test` と機密スキャンを通す。

## 対になるディレクトリ

- `../review_before/` … 本スナップショットの審査前バージョン。
- `../review_comments.md` … 両者の差分を 5 テンプレートで説明する指摘一覧。

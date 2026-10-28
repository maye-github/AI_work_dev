---
id: RD-R60Item-BEFORE
type: review-diff-asset-snapshot
req_ids: []
status: draft
sensitivity: internal
owner: AI-SE
version: 0.1.0
---

# R60Item review_before（審査前スナップショット）

> 本ディレクトリは審査差分資産 `RD-R60Item` の **審査前スナップショット** の保管場所（プレースホルダ）。
> 実物は キックオフ週の棚卸しで格納する。現時点ではファイルは置かない。

## このディレクトリに置くもの

- レビュー指摘が発生した時点の**審査前**の設計・コードのスナップショット。
- ファイル名は指摘番号に対応させ、`review_after/` と同名にする（対で 1 指摘）。
  - 例: `RC-I01_key-duplicate.py`、`RC-I03_zenkaku-numeric.py`。
- 1 指摘 = 1 対（before / after）。片方だけの保管は禁止（審査差分資産として無効）。

## 実物の入手元

- `D:\AI_work\doc\00_管理` 配下の【QA票】/【修正依頼】（Excel 本文は機械可読でないため、指摘は
  親ディレクトリの `../review_comments.md` に**傾向として**記述する）。
- Git 履歴（指摘対応コミットの**直前**のバージョン）。

## 機密則（必ず守る）

- 実顧客名・実業務データ値・接続情報・パスワード・実 IP・実社員名は**絶対にコミットしない**。
- 値が必要な箇所は `COL_1` / `VAL_1` 等の占位（プレースホルダ）に置換する。
- 投入前に `py -3 tools/masking/mask_demo.py --self-test` と機密スキャンを通す。

## 対になるディレクトリ

- `../review_after/` … 本スナップショットの是正後（審査後）最終版。
- `../review_comments.md` … 両者の差分を 5 テンプレートで説明する指摘一覧。

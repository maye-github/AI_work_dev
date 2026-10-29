---
id: KNOW-LEGACY-R60-MODULE-R60PLC-TESTS-VIEW
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-modules-r60plc-05-tests
scope: project
project_id: P-R60-001
title: R60Plc — 単体テスト観点
doc_type: design-detail
conf_level: 30
updated_at: '2026-10-29'
---

# R60Plc — 単体テスト観点

> 正本は同ディレクトリの `05-tests.yaml`。本ファイルは検索用の可読表現であり、
> 手で編集しない（`py -3 -m tools.kb_migrate --apply` で作り直す）。

| 項目 | 値 |
|---|---|
| id | KNOW-LEGACY-R60-MODULE-R60PLC-TESTS |
| type | knowledge |
| status | open |
| sensitivity | internal |
| owner | AI-SE |
| version | 0.1.0 |
| check | 6 + 175 + 107 + 272 + 75 = 635 |

## summary

| 項目 | 値 |
|---|---|
| total_items | 635 |
| detected_bugs | 0 |
| fp | 24 |
| fp_note | 単体テスト仕様兼結果のヘッダに『FP 24』と記載があるが、内訳・定義は本文に無い。 ファンクションポイントの実測値か、工程別の管理値かは未確認。 |
| test_level | 単体テスト（画面単位） |
| result | 全件 OK（不具合 0 件で終了） |

## category_notes

### 画面遷移

| 項目 | 値 |
|---|---|
| what | 一覧⇔マスタ項目モーダル、新規・複製・修正の起動と戻りを検証する。 |
| cases | 6 件（01_1.画面遷移.txt） |

### レイアウト

| 項目 | 値 |
|---|---|
| what | 初期表示・検索条件・一覧・ページャ・マスタ項目モーダルの項目配置と活性状態。 |
| blocks | 5 区分（23/44/36/36/36） |

### 入力チェック

| 項目 | 値 |
|---|---|
| what | 単項目・項目間・DB整合のチェック。設計 09/10 の 40 件＋DB 整合に対応する。 |
| blocks | 6 区分（8/8/47/42/1/1） |

### イベント

| 項目 | 値 |
|---|---|
| what | 設計 12_イベント一覧 の 24 イベントを軸に、押下・変更・焦点喪失ごとの挙動を検証する。 |
| count | 272 |

### 特殊

| 項目 | 値 |
|---|---|
| what | 排他・被参照・重複・上限超過・権限による活性差など、状態をまたぐ検証。 |
| blocks | 5 区分（12/28/31/4/0） |


## coverage_observations

| 項目 | 値 |
|---|---|
| event_coverage | 設計イベント 24 件に対しイベント系 272 件。1 イベントあたり平均 11.3 件で、 押下・条件違い・異常系をかなり細かく展開している。 |
| check_coverage | 入力チェック 107 件は設計 09（40 件）と 10（7 件）の合計 47 件の約 2.3 倍。 正常・境界・異常を区別して展開していると読める。 |
| zero_bug_note | 単体テストで不具合 0 件。ただし本仕様書は『兼結果』であり、 実施前の期待値と実施後の結果が同一ファイルにある。結果欄の記載が 期待値の転記になっていないかは、原本の列構成を確認する必要がある。 |

### unreachable_areas

- R60PlcCreate.vue / R60PlcCopy.vue は参照されていないため、画面遷移テストの対象外。
- R60I0002 は画面に表示されないため、メッセージ表示のテストで検出されない。


## test_data_policy

| 項目 | 値 |
|---|---|
| observable | テスト仕様書の入力値は実データを含むが、本カードには転記しない。 必要な場合は占位（COL_1 / VAL_1）で参照する。 |
| note | 原本の実値は L3 相当のため外部出力しない。 |

## req_ids

## breakdown

| category | count | detail | blocks |
|---|---|---|---|
| 画面遷移 | 6 | 正常遷移 6 件 |  |
| レイアウト | 175 |  | [23, 44, 36, 36, 36] |
| 入力チェック | 107 |  | [8, 8, 47, 42, 1, 1] |
| イベント | 272 |  |  |
| 特殊 | 75 |  | [12, 28, 31, 4, 0] |
| 合計 | 635 |  |  |

## design_to_test_mapping

| design | tests |
|---|---|
| 検索条件（10 項目） | 入力チェック・イベント（仕掛表示/表示） |
| 一覧（31 表示項目） | レイアウト・ソート・ページ移動 |
| マスタ項目（33 項目） | レイアウト・入力チェック・登録 |
| 排他（KSN_DAT） | 特殊 |
| 被参照（R60_CHECK_PLC_INFO_FNC） | 特殊・削除 |
| 重複（業務キー） | 特殊・新規/複製 |
| REG_STS 判定（18＋6） | 登録・特殊 |
| ボタン活性 | レイアウト・権限 |

## open_questions

- 『FP 24』の定義。
- 結果欄が実施記録か期待値の転記か。
- イベント 272 件の内訳（24 イベントへの配分）。

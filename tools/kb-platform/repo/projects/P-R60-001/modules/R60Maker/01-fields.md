---
id: KNOW-LEGACY-R60-MODULE-R60MAKER-FIELDS-VIEW
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-modules-r60maker-01-fields
scope: project
project_id: P-R60-001
title: R60Maker — 項目定義（フィールド辞書）
doc_type: design-detail
conf_level: 30
updated_at: '2026-10-28'
---

# R60Maker — 項目定義（フィールド辞書）

> 正本は同ディレクトリの `01-fields.yaml`。本ファイルは検索用の可読表現であり、
> 手で編集しない（`py -3 -m tools.kb_migrate --apply` で作り直す）。

| 項目 | 値 |
|---|---|
| id | KNOW-LEGACY-R60-MODULE-R60MAKER-FIELDS |
| type | knowledge |
| status | draft |
| sensitivity | internal |
| owner | AI-SE |
| version | 0.1.0 |

## screen_item_inventory

| 項目 | 値 |
|---|---|
| discrepancy_note | 設計書の項目番号は検索シート 33 件・マスタシート 9 件である。骨架側の I-ID 枠とは 一致しない。I-ID を起こす場合は設計書の項目番号を source_locator に持たせ、 項目数そのものを ID の根拠にしない（R60Area の D-AR-01 と同じ扱い）。 |

### search_sheet

| 項目 | 値 |
|---|---|
| numbered_items | 33 |
| row_range | r15-r51 |

#### groups

| name | items | count |
|---|---|---|
| ヘッダー部 | [2, 3, 4, 5, 6] | 5 |
| 検索条件部 | [8, 9, 10, 11, 12, 13, 14] | 7 |
| 検索結果部_ページャ上部 | [16, 17, 18, 19, 20] | 5 |
| 検索結果部_件数と行操作 | [21, 22, 23] | 3 |
| 検索結果部_一覧列 | [24, 25, 26, 27] | 4 |
| 検索結果部_ページャ下部 | [28, 29, 30, 31, 32] | 5 |
| ボタン部 | [34, 35, 36, 37] | 4 |

#### structure_rows

- 1
- 7
- 15
- 33


### master_sheet

| 項目 | 値 |
|---|---|
| numbered_items | 9 |
| row_range | r16-r27 |

#### groups

| name | items | count |
|---|---|---|
| ヘッダー部 | [2] | 1 |
| マスタ項目部 | [4, 5, 6, 7, 8] | 5 |
| ボタン部 | [10, 11, 12] | 3 |

#### structure_rows

- 1
- 3
- 9


### deprecated_input_sheet

| 項目 | 値 |
|---|---|
| numbered_items | 19 |
| row_range | r15-r37 |
| note | 新規・修正・複製の 3 モード別に同じ 5 項目を繰り返す構成（各 5 項目＋ボタン 3）。 廃止シートだが、モード別の必須条件の違いを読む補助にはなる。 |


## search_result_columns

| 項目 | 値 |
|---|---|
| note | 一覧のデータ列はコード・日本語名・カナ名・削除の 4 列（No24-27）。 No23『送信』は 4 列の直前に置かれた送信ステータス表示で、列か行ラベルかは 抽出範囲では確定できない（画面レイアウトシートは未抽出）。 |

### columns

| False | name | source | lookup | status | sortable |
|---|---|---|---|---|---|
| 23 | 送信 | メーカーマスタ.SEND_STS | コード値明細マスタ(送信ステータス) 情報ID='000000057', KEYID=SEND_STS | 位置づけ未確定 |  |
| 24 | メーカー情報：コード | メーカーマスタ.MAKER_CD | 単純移送 |  | True |
| 25 | メーカー情報：日本語名 | メーカーマスタ.MAKER_NM | 単純移送 |  | True |
| 26 | メーカー情報：カナ名 | メーカーマスタ.MAKER_ANM | 単純移送 |  |  |
| 27 | 削除 | メーカーマスタ.DEL_FLG | コード値明細マスタ(論理削除) 情報ID='000000063', KEYID=DEL_FLG |  |  |


## buttons

### search_screen

| False | name | initial | behavior |
|---|---|---|---|
| 12 | 仕掛表示 | 活性 |  |
| 13 | 表示 | 活性 |  |
| 14 | 検索条件(非)表示 | 活性 | 押す度に検索条件部を縮小/拡大 |
| 22 | 複製 | 検索成功後 活性 |  |
| 34 | 戻る | 非活性 |  |
| 35 | 業務終了 | 活性（常に活性） |  |
| 36 | ダウンロード | 非活性 |  |
| 37 | 新規 | 非活性 |  |

### master_screen

| False | name | initial |
|---|---|---|
| 10 | 戻る | 活性 |
| 11 | 削除 | 新規・複製＝非活性 / 修正＝活性（DEL_FLG='1' なら非活性） |
| 12 | 登録 | 活性 |


## db_table

| 項目 | 値 |
|---|---|
| logical_name | メーカーマスタ |
| physical_name | R60_MAKER_M_TBL |
| table_id | R60_MAKER_M_TBL |
| column_count | 17 |

### columns

| False | name | column_id | length | insert | update | delete | screen_item | edit_spec |
|---|---|---|---|---|---|---|---|---|
| 1 | メーカーコード | MAKER_CD | 5 | True | False | False | メーカーコード | そのまま移送 |
| 2 | メーカー日本語名 | MAKER_NM | 30 | True | True | True | メーカー日本語名 | そのまま移送 |
| 3 | メーカーカナ名 | MAKER_ANM | 15 | True | True | True | メーカーカナ名 | そのまま移送 |
| 4 | 飲料社接続フラグ | ASD_STU_FLG | 1 | True | False | False | - | 登録:0 固定 |
| 5 | 登録ステータス | REG_STS | 1 | True | True | True | 共通仕様参照 | - |
| 6 | 送信ステータス | SEND_STS | 1 | True | True | True | 緊急配信 | チェックオン:9 / チェックオフ:0。削除時は更新前9なら変更なし、それ以外は0 |
| 7 | 送信区分 | SEND_KBN | 1 | True | False | False | - | 登録:0 固定 |
| 8 | 論理削除フラグ | DEL_FLG | 1 | True | True | True | 削除 | チェックオン:1 / チェックオフ:0。削除:1 固定 |
| 9 | 登録区分 | REG_KBN | 1 | True | False | False | 共通仕様参照 | - |
| 10 | 登録者ＩＤ | REG_STF_ID | 10 | True | False | False | 共通仕様参照 | - |
| 11 | 登録時刻 | REG_DAT |  | True | False | False | 共通仕様参照 | - |
| 12 | 登録プログラムＩＤ | REG_PGM_ID | 20 | True | False | False | 共通仕様参照 | - |
| 13 | 更新区分 | KSN_KBN | 1 | True | True | True | 共通仕様参照 | - |
| 14 | 更新者ＩＤ | KSN_STF_ID | 10 | True | True | True | 共通仕様参照 | - |
| 15 | 更新時刻 | KSN_DAT |  | True | True | True | 共通仕様参照 | - |
| 16 | 更新プログラムＩＤ | KSN_PGM_ID | 20 | True | True | True | 共通仕様参照 | - |
| 17 | リビジョン | REV_NO | 5 | True | True | True | 共通仕様参照 | - |


## key_fields

| 項目 | 値 |
|---|---|
| logical_delete | DEL_FLG |
| registration_status | REG_STS |
| emergency_distribution | SEND_STS |
| note | 被参照される側のマスタである。削除・（修正で削除選択）時に 購入品目別仕入先マスタと原材料仕入単価マスタから参照チェックを受ける（03-logic.yaml MK-LOGIC-10/11）。 |

### primary_key

- MAKER_CD

### exclusive_control

- KSN_DAT
- REV_NO


## req_ids

## search_conditions

| False | name | input | length | match | note |
|---|---|---|---|---|---|
| 8 | メーカーコード | テキストボックス | 5 | 前方一致 | ワイルドカード入力不要 |
| 9 | メーカー日本語名 | テキストボックス | 30 | 中間一致 | ×ボタンで入力内容削除 |
| 10 | 削除含む | チェックボックス | 1 | DEL_FLG 条件の有無 | 初期表示はチェックオフ |
| 11 | 1頁件数 | ドロップダウン |  |  | コード値明細マスタ 情報ID='000000488'。初期値は個別項目名10='D' |

## master_items

| False | name | control | mode | length | required | source |
|---|---|---|---|---|---|---|
| 2 | 操作モード | ラベル | 新規/複製/修正の別を表示 |  |  |  |
| 4 | メーカーコード | 新規・複製＝テキストボックス / 修正＝ラベル |  | 5 | 新規・複製のみ必須 |  |
| 5 | メーカー日本語名 | テキストボックス |  | 30 | 緊急配信または削除選択時に必須 |  |
| 6 | メーカーカナ名 | テキストボックス |  | 15 | 緊急配信または削除選択時に必須 |  |
| 7 | 緊急配信 | チェックボックス |  |  |  | SEND_STS='9' でチェックオン |
| 8 | 削除 | 新規・複製＝ラベル / 修正＝チェックボックス |  |  |  | DEL_FLG='1' でチェックオン |

## related_masters

| table | usage | key |
|---|---|---|
| 購入品目別仕入先マスタ | 削除時の被参照チェック（区分 '1'） | 未確認（本設計書に移送表なし） |
| 原材料仕入単価マスタ | 削除時の被参照チェック（区分 '2'） | 未確認（本設計書に移送表なし） |
| コード値明細マスタ | 1頁件数（情報ID='000000488'）、送信ステータス表示（'000000057'）、論理削除表示（'000000063'）、検索上限（'000000024'）、CSVファイル名（'000000099'） | ["情報ID", "KEYID"] |
| ユーザマスタ | ヘッダーの会社・部署・ユーザ名表示 | ["社員コード"] |
| メッセージ | R60_GET_MESSAGE_FNC によるメッセージ取得 | ["メッセージID"] |

---
id: KNOW-LEGACY-R60-MODULE-R60SSK-FIELDS-VIEW
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-modules-r60ssk-01-fields
scope: project
project_id: P-R60-001
title: R60Ssk — 項目定義（フィールド辞書）
doc_type: design-detail
conf_level: 30
updated_at: '2026-10-29'
generated_by: tools/kb_migrate.py
---

# R60Ssk — 項目定義（フィールド辞書）

> 正本は同ディレクトリの `01-fields.yaml`。本ファイルは検索用の可読表現であり、
> 手で編集しない（`py -3 -m tools.kb_migrate --apply` で作り直す）。

| 項目 | 値 |
|---|---|
| id | KNOW-LEGACY-R60-MODULE-R60SSK-FIELDS |
| type | knowledge |
| status | open |
| sensitivity | internal |
| owner | AI-SE |
| version | 0.1.0 |

## screen_item_inventory

| 項目 | 値 |
|---|---|
| discrepancy_note | 設計書の実項目数は検索 35 件・マスタ項目 10 件（見出し行を除く）。 骨架の I-201..I-256（56 件）とは一致しない。I-ID を起こす場合は 設計書の項目番号を source_locator に持たせ、項目数そのものを ID の根拠にしない（D-SS-01）。 |

### search_sheet

| 項目 | 値 |
|---|---|
| max_item_no | 39 |
| numbered_rows | 39 |
| actual_items | 35 |
| row_range | r15-r53 |
| total_check | 5 + 5 + 2 + 5 + 1 + 8 + 5 + 4 = 35 |

#### section_rows

- 1
- 7
- 15
- 35

#### groups

| name | items | count |
|---|---|---|
| ヘッダー部 | [2, 3, 4, 5, 6] | 5 |
| 検索条件部 | [8, 9, 10, 11, 12] | 5 |
| 検索条件部ボタン | [13, 14] | 2 |
| 検索結果部_ページャ上部 | [16, 17, 18, 19, 20] | 5 |
| 検索結果部_件数 | [21] | 1 |
| 検索結果部_一覧列 | [22, 23, 24, 25, 26, 27, 28, 29] | 8 |
| 検索結果部_ページャ下部 | [30, 31, 32, 33, 34] | 5 |
| ボタン部 | [36, 37, 38, 39] | 4 |


### master_sheet

| 項目 | 値 |
|---|---|
| max_item_no | 13 |
| numbered_rows | 13 |
| actual_items | 10 |
| row_range | r16-r28 |
| total_check | 1 + 6 + 3 = 10 |

#### section_rows

- 1
- 3
- 10

#### groups

| name | items | count |
|---|---|---|
| ヘッダー部 | [2] | 1 |
| マスタ項目部 | [4, 5, 6, 7, 8, 9] | 6 |
| ボタン部 | [11, 12, 13] | 3 |


### deprecated_input_sheet

| 項目 | 値 |
|---|---|
| max_item_no | 23 |
| numbered_rows | 23 |
| actual_items | 19 |
| note | 新規・修正・複製の 3 モード別に 5 項目＋ボタン 3 を繰り返す構成。 ただし項目名はメーカーマスタのものであり、R60Ssk の廃止仕様ではなく流用残骸である。 |

#### section_rows

- 2
- 8
- 14
- 20



## search_result_columns

| 項目 | 値 |
|---|---|
| note | 一覧のデータ列は No23-29 の 7 列。No22『送信』は送信ステータスの表示ラベルで、 列そのものか行ラベルかは抽出範囲では確定できない（画面レイアウトシート未抽出）。 |
| naming_caution | No24 の項目名称は『事業場組織ユニット』だが、エンティティ項目は SSK_UNIT（組織ユニット）。 No25 は名称が『組織ユニット：コード』で、エンティティ項目は JIG_SSK_UNIT。 名称と項目の対応が入れ替わって見えるため、実装・移送表と突合して読むこと（D-SS-05）。 |

### columns

| False | name | source | lookup | status | sortable |
|---|---|---|---|---|---|
| 22 | 送信 | 部署マスタ.SEND_STS | コード値マスタ(明細)(送信ステータス) 情報ID='000000057', KEYID=SEND_STS | 位置づけ未確定 |  |
| 23 | 会社 | 部署マスタ.CMP_CD | コード値マスタ(明細)(HR会社) 情報ID='000000104', KEYID=CMP_CD |  | True |
| 24 | 事業場組織ユニット | 部署マスタ.SSK_UNIT | 単純移送 |  | True |
| 25 | 組織ユニット：コード | 部署マスタ.JIG_SSK_UNIT | 単純移送 |  | True |
| 26 | 組織ユニット：正式名称 | 部署マスタ.SEI_NM | 単純移送 |  |  |
| 27 | 経理用：会社 | 部署マスタ.S_CMP_CD | 単純移送 |  |  |
| 28 | 経理用：事業場 | 部署マスタ.S_JIG_CD | 単純移送 |  |  |
| 29 | 削除 | 部署マスタ.DEL_FLG | コード値マスタ(明細)(論理削除) 情報ID='000000063', KEYID=DEL_FLG |  |  |


## buttons

### search_screen

| False | name | initial | note | behavior | activation |
|---|---|---|---|---|---|
| 13 | 表示 | 活性 | 会社未選択なら組織ユニット検索は非活性 |  |  |
| 14 | 検索条件非表示 | 活性 |  | 標準仕様（条件部の縮小/拡大） |  |
| 36 | 戻る | 非活性 |  |  | 検索結果 1 件以上で活性 |
| 37 | 業務終了 | 活性 |  |  |  |
| 38 | ダウンロード | 非活性 |  |  | 検索結果 1 件以上で活性 |
| 39 | 新規 | 非活性 | 本画面では新規を提供しない（設計上も非活性のまま） |  |  |

### master_screen

| False | name | initial | note | activation |
|---|---|---|---|---|
| 11 | 戻る | 活性 |  |  |
| 12 | 削除 | 非活性 | 修正モードでも非活性。本画面は更新のみ（D-SS-03） |  |
| 13 | 登録 | 活性 |  | 権限区分:Y の時のみ活性（BP r147） |


## db_columns

| 項目 | 値 |
|---|---|
| table | R60_SSK_M_TBL |
| table_name | 部署マスタ |
| column_count | 19 |
| business_key_locator | BP r117-r118（一覧リンクの検索条件）/ r211（更新条件） |

### operation_flags

| 項目 | 値 |
|---|---|
| implication | 項目移送表に登録（INSERT）・削除（DELETE）の ○ が 1 つも無い。本画面は IDM から受信済みの行を更新するだけであり、新規作成・論理削除は提供しない。 削除ボタンが初期非活性であることと一致する（D-SS-03）。 |

#### insert_columns

#### update_columns

- S_CMP_CD
- S_JIG_CD
- REG_STS
- SEND_STS
- KSN_KBN
- KSN_STF_ID
- KSN_DAT
- KSN_PGM_ID
- REV_NO

#### delete_columns


### business_key

- CMP_CD
- SSK_UNIT

### columns

| False | name | column | length | insert | update | delete | screen | edit |
|---|---|---|---|---|---|---|---|---|
| 1 | 会社コード | CMP_CD | 4 | - | - | - |  |  |
| 2 | 組織ユニット | SSK_UNIT | 8 | - | - | - |  |  |
| 3 | 事業場組織ユニット | JIG_SSK_UNIT | 8 | - | - | - |  |  |
| 4 | 正式名称 | SEI_NM | 40 | - | - | - |  |  |
| 5 | Ｓ会社コード | S_CMP_CD | 4 | - | ○ | - | 経理用会社 | リスト選択値 |
| 6 | Ｓ事業場コード | S_JIG_CD | 4 | - | ○ | - | 経理用事業場 | リスト選択値 |
| 7 | 登録ステータス | REG_STS | 1 | - | ○ | - |  | プログラム内設定値 |
| 8 | 送信ステータス | SEND_STS | 1 | - | ○ | - |  | 固定値 '0':未送信 |
| 9 | 送信区分 | SEND_KBN | 1 | - | - | - |  |  |
| 10 | 論理削除フラグ | DEL_FLG | 1 | - | - | - |  |  |
| 11 | 登録区分 | REG_KBN | 1 | - | - | - |  |  |
| 12 | 登録者ＩＤ | REG_STF_ID | 10 | - | - | - |  |  |
| 13 | 登録時刻 | REG_DAT |  | - | - | - |  |  |
| 14 | 登録プログラムＩＤ | REG_PGM_ID | 20 | - | - | - |  |  |
| 15 | 更新区分 | KSN_KBN | 1 | - | ○ | - |  | 共通仕様参照 |
| 16 | 更新者ＩＤ | KSN_STF_ID | 10 | - | ○ | - |  | 共通仕様参照 |
| 17 | 更新時刻 | KSN_DAT |  | - | ○ | - |  | 共通仕様参照 |
| 18 | 更新プログラムＩＤ | KSN_PGM_ID | 20 | - | ○ | - |  | 共通仕様参照 |
| 19 | リビジョン | REV_NO | 5 | - | ○ | - |  | 共通仕様参照 |


## field_naming_rules

| 項目 | 値 |
|---|---|
| definition_layer | snake_case（YAML / Python） |
| interface_layer | camelCase（TS / JSON wire） |
| conversion_point | BaseCamelModel（alias_generator=to_camel） |
| note | 実装の BaseCamelModel は extra='ignore'（骨架規則は 'forbid'）。02-api.yaml / D-SS-04 を参照。 |

## req_ids

## search_conditions

| False | name | input | source | initial | note | max | match | behavior |
|---|---|---|---|---|---|---|---|---|
| 8 | 会社 | ドロップダウン | コード値マスタ(明細) 情報ID='000000104'（HR会社） | ログインユーザの会社 | 先頭にブランク行。ブランク時は WHERE に加えない |  |  |  |
| 9 | 組織ユニット | テキストボックス |  |  | ワイルドカード入力不要。入力支援は SSK_UNIT + 会社選択値 | 8 | 前方一致 |  |
| 10 | 組織ユニット検索 | アイコン |  |  |  |  |  | 一覧型入力支援(択一式)を起動 |
| 11 | 正式名称 | テキストボックス |  |  | ワイルドカード入力不要 | 40 | 中間一致 |  |
| 12 | １頁件数 | ドロップダウン |  |  | 標準仕様参照 |  |  |  |

## master_items

| False | name | control | value | source | lookup | required |
|---|---|---|---|---|---|---|
| 2 | 操作モード | ラベル | 検索結果一覧リンククリック → 修正 |  |  |  |
| 4 | 会社 | ラベル |  | 部署マスタ.CMP_CD | コード値マスタ(明細)(HR会社) 情報ID='000000104' |  |
| 5 | 事業場組織ユニット | ラベル |  | 部署マスタ.JIG_SSK_UNIT |  |  |
| 6 | 組織ユニットコード | ラベル |  | 部署マスタ.SSK_UNIT |  |  |
| 7 | 組織ユニット正式名称 | ラベル |  | 部署マスタ.SEI_NM |  |  |
| 8 | 経理用会社 | ドロップダウン |  | 会社マスタ（論理削除フラグ='0'、会社コード昇順） |  | False |
| 9 | 経理用事業場 | ドロップダウン |  | 会社マスタ＋事業場マスタ（双方 DEL_FLG='0'、表示順 NOT NULL） |  | False |

## open_points

- 画面レイアウトシートが未抽出のため、No22『送信』が列か行ラベルか確定できない。
- 項目移送表は主キー列を持たない。業務キーは BP の検索条件・更新条件から CMP_CD + SSK_UNIT と読んだ。
- 『廃止_画面項目内容(入力)』は R60Maker の項目を残したまま廃止されており、R60Ssk の履歴資料としては使えない。

---
id: KNOW-LEGACY-R60-MODULE-R60USER-FIELDS-VIEW
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-modules-r60user-01-fields
scope: project
project_id: P-R60-001
title: R60User — 項目定義（フィールド辞書）
doc_type: design-detail
conf_level: 30
updated_at: '2026-10-29'
generated_by: tools/kb_migrate.py
---

# R60User — 項目定義（フィールド辞書）

> 正本は同ディレクトリの `01-fields.yaml`。本ファイルは検索用の可読表現であり、
> 手で編集しない（`py -3 -m tools.kb_migrate --apply` で作り直す）。

| 項目 | 値 |
|---|---|
| id | KNOW-LEGACY-R60-MODULE-R60USER-FIELDS |
| type | knowledge |
| status | open |
| sensitivity | internal |
| owner | AI-SE |
| version | 0.1.0 |

## identification

| 項目 | 値 |
|---|---|
| screen_id | R60User |
| screen_name | ユーザーマスタメンテナンス |
| subsystem | 生産系共通マスタシステム |
| build_mode_observed | migration |
| screen_class | 検索一覧＋マスタ項目モーダル（修正のみ） |
| premise | IDM、3G からのデータ受信が完了していること |
| exclusive | あり（KSN_DAT による排他） |
| frequency | 月次・随時 |
| permission | 利用権限保持者のみ |

## item_counts

| 項目 | 値 |
|---|---|
| total_actual_items | 62 |
| count_rule | No の最大値ではなく、節見出し行を除いた実項目で数える。 |
| skeleton_comparison | 検索 42 ＋ マスタ 20 ＝ 62。R60Area の 56・R60Plc の 102 と同列に比較できる。 項目数は画面規模の指標であって骨架の固定値ではない。 |

### search_sheet

| 項目 | 値 |
|---|---|
| max_no | 46 |
| actual_items | 42 |
| check | 5 + 9 + 24 + 4 = 42 |

#### breakdown

| 項目 | 値 |
|---|---|
| header | 5 |
| search_conditions | 9 |
| result_section | 24 |
| bottom_buttons | 4 |

#### section_rows

- 1
- 7
- 17
- 42


### master_sheet

| 項目 | 値 |
|---|---|
| max_no | 23 |
| actual_items | 20 |
| check | 1 + 16 + 3 = 20 |

#### breakdown

| 項目 | 値 |
|---|---|
| header | 1 |
| master_items | 16 |
| buttons | 3 |

#### section_rows

- 1
- 3
- 20



## result_columns

| 項目 | 値 |
|---|---|
| count | 18 |

### sortable

- 会社
- 社員コード
- 組織ユニットコード
- 経理用会社
- 経理用事業場

### columns

| False | name | source | format |
|---|---|---|---|
| 24 | 送信 | コード値マスタ 000000057 / 個別項目名1 |  |
| 25 | 会社 | コード値マスタ 000000104 / コード値名称 |  |
| 26 | 社員コード | ユーザマスタ STF_CD |  |
| 27 | 社員氏名 | ユーザマスタ STF_NM |  |
| 28 | 発令日 | ユーザマスタ HTR_YMD | YYYY/MM/DD |
| 29 | 組織ユニットコード | ユーザマスタ SSK_UNIT |  |
| 30 | 組織ユニット名称 | R60_Get_User_Information_FNC(社員コード,'6') → 部署マスタ.正式名称 |  |
| 31 | メールアドレス１ | ユーザマスタ MAIL_ADRS_1 |  |
| 32 | メールアドレス２ | ユーザマスタ MAIL_ADRS_2 |  |
| 33 | パスワード設定日 | ユーザマスタ PWD_STE_YMD | YYYY/MM/DD |
| 34 | 経理用会社 | ユーザマスタ S_CMP_CD |  |
| 35 | 経理用事業場 | ユーザマスタ S_JIG_CD |  |
| 36 | 役割 | R60_Get_Hany_Meisai_FNC('000000046', 役割コード, '0') |  |
| 37 | 帳票共有グループ | R60_Get_Hyo_Kyo_Grp_Info_FNC(コード, '1') |  |
| 38 | 帳票参照 | R60_Get_Code_Chi_Meisai_FNC('000000116', フラグ, '0') |  |
| 39 | 帳票権限 | R60_Get_Hany_Meisai_FNC('000000051', コード, '0') |  |
| 40 | ユーザタイプ | R60_Get_User_Typ_Info_FNC(コード, '1') |  |
| 41 | 削除 | R60_Get_Code_Chi_Meisai_FNC('000000063', DEL_FLG, '1') |  |

### buttons

| False | name | initial |
|---|---|---|
| 43 | 戻る | 非活性 |
| 44 | 業務終了 | 活性 |
| 45 | ダウンロード | 非活性 |
| 46 | 新規 | 非活性 |


## master_items

| 項目 | 値 |
|---|---|
| mode_label | 固定値「〔 修正 〕」 |

### emergency_checkbox

| 項目 | 値 |
|---|---|
| column | SEND_STS |
| True | 9（緊急送信指示） |
| False | 0（未送信） |

### label_only

- 会社（所属会社コード）
- 社員コード
- 氏名（社員日本語名称）
- 発令日
- 組織ユニット（コード／名称）
- メールアドレス１
- パスワード設定日

### editable

- メールアドレス２（半角英数 50）
- 経理用会社（ドロップダウン）
- 経理用事業場（ドロップダウン）
- 役割（ドロップダウン、緊急配信時必須）
- 帳票共有グループ（ドロップダウン、緊急配信時必須）
- 帳票参照（ドロップダウン、緊急配信時必須）
- 帳票権限（ドロップダウン、緊急配信時必須）
- ユーザタイプ（ドロップダウン、緊急配信時必須）
- 緊急配信（チェックボックス）

### buttons

| False | name | initial |
|---|---|---|
| 21 | 戻る | 活性 |
| 22 | 削除 | 非活性 |
| 23 | 登録 | 活性 |


## dropdowns

| 項目 | 値 |
|---|---|
| common_rule | 先頭に空白行（未選択）を追加する。 |

### items

| item | table | key | filter | order |
|---|---|---|---|---|
| 経理用会社 | R60_COMPANY_M_TBL | CMP_CD | DEL_FLG=0 | CMP_CD |
| 経理用事業場 | R60_COMPANY_M_TBL × R60_JIG_M_TBL | CMP_CD + ',' + JIG_CD | 双方 DEL_FLG=0、HYJ_SEQ NOT NULL | HYJ_SEQ, CMP_CD, JIG_CD |
| 役割 | R60_HANY_MES_M_TBL × R60_MENU_KINO_ACS_M_TBL | KEY_ID | 情報ID 000000046、双方 DEL_FLG=0 | HYJ_SEQ, KEY_ID |
| 帳票共有グループ | R60_HYO_KYO_GRP_M_TBL | HYO_KYO_GRP_CD | DEL_FLG=0 | HYO_KYO_GRP_CD |
| 帳票参照 | R60_CODE_MES_M_TBL | KEY_ID | 情報ID 000000116、DEL_FLG=0 | HYJ_SEQ, KEY_ID |
| 帳票権限 | R60_HANY_MES_M_TBL × R60_HYO_ACS_M_TBL | KEY_ID | 情報ID 000000051、双方 DEL_FLG=0 | HYJ_SEQ, KEY_ID |
| ユーザタイプ | R60_USER_TYP_M_TBL | USER_TYP_CD | DEL_FLG=0 | USER_TYP_CD |


## db_model

| 項目 | 値 |
|---|---|
| table | R60_USER_M_TBL |
| table_id | ユーザマスタ |
| columns_total | 28 |

### operation_flags

| 項目 | 値 |
|---|---|
| insert_columns | 0 |
| update_columns | 15 |
| delete_columns | 0 |
| physical_delete | False |
| note | 本画面は UPDATE のみ。新規・削除の operation は実装されていない（D-US-01）。 |

### update_columns_detail

| 項目 | 値 |
|---|---|
| check | 業務 10 ＋ 管理 5 ＝ 15。項目移送表の更新 ○ と一致。 |

#### business

- MAIL_ADRS_2
- S_CMP_CD
- S_JIG_CD
- YAK_CD
- HYO_KYO_GRP_CD
- GRP_KJN_FLG
- HYO_ACS_CD
- USER_TYP_CD
- REG_STS
- SEND_STS

#### management

- KSN_KBN
- KSN_STF_ID
- KSN_DAT
- KSN_PGM_ID
- REV_NO


### primary_key

- STF_CD


## reg_sts_rule

| 項目 | 値 |
|---|---|
| True | 役割・帳票共有グループ・帳票参照・帳票権限・ユーザタイプがすべて選択済み |
| False | 上記のいずれかが未選択 |
| source | 14_項目移送表(DB) No16、R60UserController.py set_reg_sts:1442-1458 |

## req_ids

## search_conditions

| False | name | type | condition | initial | source | role | readonly | note |
|---|---|---|---|---|---|---|---|---|
| 8 | 会社 | dropdown | 完全一致 | ログインユーザーの所属会社（設計） | 情報ID 000000104 |  |  |  |
| 9 | 組織ユニット | textbox | 前方一致 8 桁 | 空白 |  |  |  |  |
| 10 | 組織ユニット検索 | icon |  |  |  | 入力支援画面 SSK_UNIT を起動 |  |  |
| 11 | 組織ユニット名称 | textbox | 表示のみ | 空白 |  |  | True |  |
| 12 | 社員コード | textbox | 前方一致 8 桁 | 空白 |  |  |  |  |
| 13 | 発令日 | textbox | 前方一致 8 桁 | 空白 |  |  |  |  |
| 14 | １頁件数 | dropdown | 情報ID 000000064、既定は個別項目名10='D' | 情報ID 既定値 |  |  |  |  |
| 15 | 表示 | button |  |  |  |  |  |  |
| 16 | 検索結果非表示 | button |  |  |  |  |  | 標準仕様 |

## key_columns

| name | label | len | note |
|---|---|---|---|
| STF_CD | 社員コード | 8 | 主キー |
| SZK_CMP_CD | 所属会社コード | 4 | 検索条件・既定ソート |
| HTR_YMD | 発令日 | 8 |  |
| STF_NM | 社員日本語名称 | 30 |  |
| SSK_UNIT | 組織ユニット | 8 |  |
| MAIL_ADRS_2 | メールアドレス２ | 50 | 本画面で編集可 |
| S_CMP_CD | Ｓ会社コード | 4 | 経理用会社 |
| S_JIG_CD | Ｓ事業場コード | 4 | 経理用事業場。画面の複合キーから 2 番目を保存（D-US-04） |
| REG_STS | 登録ステータス | 1 | 5 項目（役割・帳票共有グループ・帳票参照・帳票権限・ユーザタイプ）が揃えば 1 |
| SEND_STS | 送信ステータス | 1 | 緊急配信チェックで 9 |
| KSN_DAT | 更新時刻 |  | 排他チェックの比較対象 |
| REV_NO | リビジョン | 5 | 更新時 +1 |

## design_defects_in_field_sheet

- 検索シート No11 組織ユニット名称のエンティティが『部署マスタ.組織ユニット』で、名称ではない（D-US-03）。
- 検索シート No30 組織ユニット名称のエンティティが『ユーザマスタ.社員コード』で、名称ではない（D-US-03）。
- 検索シート No8 会社のエンティティが『ユーザマスタ.会社コード』。ユーザマスタの列名は SZK_CMP_CD（所属会社コード）である。
- 経理用事業場のリストキーが複合値（会社コード + ',' + 事業場コード）だが、移送先 S_JIG_CD は 4 桁のみで、分解規則が設計に無い（D-US-04）。
- マスタ項目シートは『新規・複製操作時』の列が空で、修正・削除のみを定義する（D-US-01 の前提）。

## open_questions

- 検索の会社初期値は所属会社（cmp_cd）か S 会社（scmp_cd）か（D-US-02）。
- 部署マスタの正式名称は R60_SSK_M_TBL.SEI_NM でよいか（【推測】同一）。
- 新規・ダウンロードボタンは設計に機能イベントが無い。残すのか削除するのか。

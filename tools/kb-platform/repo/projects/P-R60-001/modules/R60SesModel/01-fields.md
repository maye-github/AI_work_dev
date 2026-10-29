---
id: KNOW-LEGACY-R60-MODULE-R60SESMODEL-FIELDS-VIEW
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-modules-r60sesmodel-01-fields
scope: project
project_id: P-R60-001
title: R60SesModel — 項目定義（フィールド辞書）
doc_type: design-detail
conf_level: 30
updated_at: '2026-10-28'
---

# R60SesModel — 項目定義（フィールド辞書）

> 正本は同ディレクトリの `01-fields.yaml`。本ファイルは検索用の可読表現であり、
> 手で編集しない（`py -3 -m tools.kb_migrate --apply` で作り直す）。

| 項目 | 値 |
|---|---|
| id | KNOW-LEGACY-R60-MODULE-R60SESMODEL-FIELDS |
| type | knowledge |
| status | draft |
| sensitivity | internal |
| owner | AI-SE |
| version | 0.1.0 |

## identification

| 項目 | 値 |
|---|---|
| screen_id | R60SesModel |
| screen_name | 生産モデルマスタメンテナンス |
| subsystem | 生産系共通マスタシステム |
| build_mode_observed | migration |
| screen_class | 検索一覧＋明細一覧＋ヘッダマスタ項目モーダル＋明細マスタ項目モーダル（主従） |
| screen_count | 4 |
| exclusive | あり（KSN_DAT による排他） |
| permission | 利用権限保持者のみ。権限区分='Y'（更新可）で複製・明細・登録・削除の活性が変わる |
| premise | 概要シートには『前提条件：なし／あり』『使用頻度：月次／日次／随時』の選択肢が並ぶが、 抽出行には選択記号が残っていないため、選択状態は判別できない（未確認）。 実装上は init でセッションとオンライン可否のみを確認し、業務前提のチェックは持たない。 |
| screen_kubun | 概要シートの画面区分は「参照／登録／更新／削除／DL／UL／その他」の選択肢。 選択状態は抽出から判別できないが、実装上は参照・登録・更新・削除・DL の 5 種を持つ。 |

### variants

- オプション区分='1'（アイテム）→ タイトル『アイテム生産モデルマスタメンテナンス』
- オプション区分='2'（半製品）→ タイトル『半製品生産モデルマスタメンテナンス』
- オプション区分='3'（原材料）→ タイトル『原材料生産モデルマスタメンテナンス』


## item_counts

| 項目 | 値 |
|---|---|
| count_rule | 各シートの No は節見出し行を含み、欠番もある。No の最大値ではなく 節見出し行を除いた実項目で数える（R60Plc の D-PL-01 と同じ数え方）。 調査票の『33 項目 / 39 項目 / 31 イベント』は最大値であり実件数ではない（D-SM-15）。 |
| total_actual_items | 99 |
| total_check | 42 + 12 + 30 + 15 = 99 |

### search_sheet

| 項目 | 値 |
|---|---|
| max_no | 50 |
| actual_items | 42 |
| check | 5 + 14 + 18 + 5 = 42 |

#### breakdown

| 項目 | 値 |
|---|---|
| header | 5 |
| search_conditions | 14 |
| result_section | 18 |
| buttons | 5 |

#### section_rows

- 1
- 7
- 26
- 45

#### missing_numbers

- 15
- 19
- 20
- 21


### header_master_sheet

| 項目 | 値 |
|---|---|
| max_no | 15 |
| actual_items | 12 |
| check | 1 + 8 + 3 = 12 |

#### breakdown

| 項目 | 値 |
|---|---|
| header | 1 |
| master_items | 8 |
| buttons | 3 |

#### section_rows

- 1
- 3
- 12

#### missing_numbers


### detail_sheet

| 項目 | 値 |
|---|---|
| max_no | 35 |
| actual_items | 30 |
| check | 1 + 2 + 22 + 5 = 30 |

#### breakdown

| 項目 | 値 |
|---|---|
| header | 1 |
| detail_header | 2 |
| result_section | 22 |
| buttons | 5 |

#### section_rows

- 1
- 3
- 4
- 7
- 30

#### missing_numbers


### detail_master_sheet

| 項目 | 値 |
|---|---|
| max_no | 18 |
| actual_items | 15 |
| check | 1 + 11 + 3 = 15 |

#### breakdown

| 項目 | 値 |
|---|---|
| header | 1 |
| master_items | 11 |
| buttons | 3 |

#### section_rows

- 1
- 3
- 15

#### missing_numbers



## result_columns

| 項目 | 値 |
|---|---|
| count | 5 |
| note | 一覧の列は 5 つと少ない。主従構造のため、詳細（子コード・所要量・基準値）は 明細画面へ遷移して表示する。 |

### sortable

- 生産モデルコード
- 生産モデル名

### columns

| name | source | display | note | link |
|---|---|---|---|---|
| 送信 | 生産モデルマスタ.送信ステータス | '' / 未 / 済 / 緊 | コード値マスタ(明細) 情報ID 000000057 |  |
| 生産モデルコード | 生産モデルマスタ.生産モデルコード |  |  | True |
| 生産モデル名 | 生産モデルマスタ.生産モデル名 |  |  | True |
| 親コード区分 | 生産モデルマスタ.親コード区分 |  | コード値マスタ(明細) 情報ID 000000091 |  |
| 削除 | 生産モデルマスタ.論理削除フラグ | '' / 削 | コード値マスタ(明細) 情報ID 000000063 |  |

### buttons

- 複製
- 明細


## detail_columns

| 項目 | 値 |
|---|---|
| count | 11 |

### columns

| name | source | note | display |
|---|---|---|---|
| 送信 | 生産モデル明細マスタ.送信ステータス | 情報ID 000000057 |  |
| 子コード区分 | 生産モデル明細マスタ.子コード区分 | 情報ID 000000092 |  |
| 子コード | 生産モデル明細マスタ.子コード |  |  |
| 子コード名称 | 半製品M / 購入品目M から名称を取得 | R60_Get_Hsh_Information_FNC / R60_Get_KonHmk_Information_FNC |  |
| 所要量 | 生産モデル明細マスタ.所要量 |  | 99,999.99999 |
| 所要量単位 | 購入品目M.在庫管理単位コード → コード値名称 |  |  |
| 基準値 | 生産モデル明細マスタ.基準値 |  | 9,999,999,999 |
| 基準値単位 | 所要量単位と同じ | 設計は『所要量単位と同様』とだけ書く |  |
| 調達対象外フラグ | 生産モデル明細マスタ.調達対象外フラグ | 情報ID 000000455 |  |
| 展開区分 | 生産モデル明細マスタ.展開区分 | 情報ID 000000457 |  |
| 削除 | 生産モデル明細マスタ.論理削除フラグ |  | '' / 削 |

### sortable


## master_items

### header_modal

#### editable

- 生産モデルコード：親番（新規・複製。自動採番 OFF 時）
- 生産モデルコード：枝番（新規・複製。自動採番 OFF 時）
- 生産モデル名
- 半製品コード自動採番（オプション区分='2'・新規/複製・会社が 0093/0452 の時のみ表示）

#### label_only

- 操作モード
- 親コード区分（オプション区分によりアイテム／半製品／原材料）

#### modify_only

- 緊急配信（送信ステータス='9' の時チェック）
- 削除（論理削除フラグ='1' の時チェック）

#### buttons

- 戻る
- 削除
- 登録


### detail_modal

#### editable

- 子コード区分（ドロップダウン）
- 子コード（区分が空白なら非活性）
- 所要量（0.001〜99,999.999）
- 基準値（1〜9,999,999,999）
- 調達対象外フラグ（ドロップダウン）
- 展開区分（ドロップダウン）

#### label_only

- 操作モード
- 子コード名称
- コメント挿入１（"(0.001 ～ 99,999.999)"）
- コメント挿入２（"(1 ～ 9,999,999,999)"）

#### modify_only

- 削除（論理削除フラグ）

#### buttons

- 戻る
- 削除
- 登録


### conditional_disable

- 飲料社接続フラグ='1' の時、生産モデル名・所要量・基準値は非活性
- 子コード区分が空白の時、子コードと子コード検索は非活性
- 半製品コード自動採番 ON の時、親番・検索・枝番は非活性


## db_model

| 項目 | 値 |
|---|---|
| tables | 6 |

### operation_sheets

| 項目 | 値 |
|---|---|
| note | 項目移送表は 12 枚あるが実テーブルは 6 つ。同一テーブルが 登録・更新・削除の別シートに分かれているため、更新列はシートごとに読み分ける（D-SM-13）。 |

#### mapping

| sheet | table | pattern |
|---|---|---|
| DB1 | R60_SES_MODEL_M_TBL | insert |
| DB2 | R60_SES_MODEL_MES_M_TBL | insert |
| DB3 | R60_SYOHO_M_TBL | update |
| DB4 | R60_HAN_SEIHIN_M_TBL | update/delete |
| DB5 | R60_HSH_SES_MODEL_REF_M_TBL | delete |
| DB6 | R60_KJO_SES_MODEL_M_TBL | delete |
| DB7 | R60_SES_MODEL_M_TBL | delete |
| DB8 | R60_SES_MODEL_MES_M_TBL | delete |
| DB9 | R60_KJO_SES_MODEL_M_TBL | delete/update |
| DB10 | R60_HAN_SEIHIN_M_TBL | insert（ダミー半製品） |
| DB11 | R60_SES_MODEL_MES_M_TBL | insert/update（明細マスタ項目） |
| DB12 | R60_SES_MODEL_MES_M_TBL | update（子コード変更） |


### column_inventory

#### R60_SES_MODEL_M_TBL

| 項目 | 値 |
|---|---|
| count | 18 |
| insert | 18 |
| update | 10 |
| delete | 9 |
| note | 登録のみの列（SES_MDL_CD / ASD_STU_FLG / SEND_KBN / REG_*）は更新しない |

##### columns

| False | col | len |
|---|---|---|
| 1 | SES_MDL_CD | 17 |
| 2 | SES_MDL_NM | 30 |
| 3 | OYA_CD_KBN | 1 |
| 4 | ASD_STU_FLG | 1 |
| 5 | REG_STS | 1 |
| 6 | SEND_STS | 1 |
| 7 | SEND_KBN | 1 |
| 8 | DEL_FLG | 1 |
| 9 | REG_KBN | 1 |
| 10 | REG_STF_ID | 10 |
| 11 | REG_DAT |  |
| 12 | REG_PGM_ID | 20 |
| 13 | KSN_KBN | 1 |
| 14 | KSN_STF_ID | 10 |
| 15 | KSN_DAT |  |
| 16 | KSN_PGM_ID | 20 |
| 17 | REV_NO | 5 |


#### R60_SES_MODEL_MES_M_TBL

| 項目 | 値 |
|---|---|
| count | 21 |
| insert | 21 |
| update | 8 |
| delete | 8 |

##### columns

| False | col | len |
|---|---|---|
| 1 | SES_MDL_CD | 17 |
| 2 | KO_CD_KBN | 1 |
| 3 | KO_CD | 7 |
| 4 | SYRYO | 10 |
| 5 | KIJ_CHI | 10 |
| 6 | CYOT_TSOGAI_FLG | 1 |
| 7 | TKI_KBN | 1 |
| 8 | ASD_STU_FLG | 1 |
| 9 | REG_STS | 1 |
| 10 | SEND_STS | 1 |
| 11 | SEND_KBN | 1 |
| 12 | DEL_FLG | 1 |
| 13 | REG_KBN | 1 |
| 14 | REG_STF_ID | 10 |
| 15 | REG_DAT |  |
| 16 | REG_PGM_ID | 20 |
| 17 | KSN_KBN | 1 |
| 18 | KSN_STF_ID | 10 |
| 19 | KSN_DAT |  |
| 20 | KSN_PGM_ID | 20 |
| 21 | REV_NO | 5 |


#### R60_SYOHO_M_TBL

| 項目 | 値 |
|---|---|
| count | 27 |
| note | 画面から直接 INSERT しない。処方マスタ自動生成（パッケージ／共通処理）が作成し、 本画面は SEND_STS と監査列のみ更新する。 |
| update | 6 |

#### R60_HAN_SEIHIN_M_TBL

| 項目 | 値 |
|---|---|
| count | 62 |
| insert | 40 |
| update | 8 |
| delete | 8 |
| insert_columns_note | 実装（auto_number_hsh_cd）の INSERT 列は 40。 HSH_NM=生産モデル名、GNK_CD=半製品コード自身、HYJ_SEQ=NULL を明示する。 移送表 DB10 はテーブル全 62 列を示すが、登録列はその一部である。 |

##### dummy_defaults

| 項目 | 値 |
|---|---|
| GZR_NYU_GRP_CD | 50 |
| CYOT_KBN | 0 |
| HSH_HMK_BNR_CD_1 | H000 |
| HSH_HMK_BNR_CD_2 | 1600 |
| HSH_HMK_BNR_CD_3 | 1650 |
| HSH_HMK_BNR_CD_4 |  |
| SUU_TNI_CD | 902 |
| HYJ_SEQ |  |
| HSH_TYP_CD | 9 |
| KIJ_GNS_KNW_RAT | 0 |
| TSK_KNW_RAT | 0 |
| ALC_DSU_STE_FLG | 0 |
| TEM_STE_FLG | 0 |
| KNSN_HHO_KBN | 1 |
| ZNB_GNR_JRY_KNSN_KEIS | 0 |
| BAK_KNSN_KEIS | 0 |
| BAK_SIY_JRY_KNSN_KEIS | 0 |
| SSEI_IST_SKK_SAKE_CD | 999 |
| IST_MES_SAKE_CD | 999 |
| SST_BNR_CD | 99 |
| KMZ_KBN | 0 |
| KON_HIN_FLG | 0 |
| ESS_STE_FLG | 0 |
| SAKE_STE_FLG | 0 |
| GNK_RENK_KBN | 2 |
| GEN_BAJ_ESS_SHH_KKU_CHI | 0 |
| REG_STS | 0 |
| SEND_STS | 0 |
| SEND_KBN | 0 |
| DEL_FLG | 0 |
| REG_KBN | 1 |
| REG_PGM_ID | R60SesModel |

##### key_columns

| col | len |
|---|---|
| HSH_CD | 6 |
| HSH_NM | 40 |


#### R60_HSH_SES_MODEL_REF_M_TBL

| 項目 | 値 |
|---|---|
| count | 17 |
| delete | 4 |
| note | 登録・更新は行わない。削除時の 4 列のみ。 |

#### R60_KJO_SES_MODEL_M_TBL

| 項目 | 値 |
|---|---|
| count | 21 |
| delete | 4 |
| update | 4 |
| note | DB6 と DB9 は同一テーブルの別パターン。DB9 は REG_STS も更新する。 |


### logical_to_physical

| logical | physical | columns | key |
|---|---|---|---|
| 生産モデルマスタ | R60_SES_MODEL_M_TBL | 18 | ["SES_MDL_CD"] |
| 生産モデル明細マスタ | R60_SES_MODEL_MES_M_TBL | 21 | ["SES_MDL_CD", "KO_CD_KBN", "KO_CD"] |
| 処方マスタ | R60_SYOHO_M_TBL | 27 | ["CMP_CD", "JIG_CD", "SEZ_RET_CD", "OYA_CD_KBN", "OYA_CD", "TEK_KIK_BGN_YMD", "SES_MDL_CD", "KO_CD_KBN", "KO_CD"] |
| 半製品マスタ | R60_HAN_SEIHIN_M_TBL | 62 | ["HSH_CD"] |
| 半製品生産モデル関連マスタ | R60_HSH_SES_MODEL_REF_M_TBL | 17 | ["AB_ITEM_CD", "ASD_SES_MDL_CD"] |
| 工場生産モデルマスタ | R60_KJO_SES_MODEL_M_TBL | 21 | ["CMP_CD", "JIG_CD", "SEZ_RET_CD", "OYA_CD", "TEK_KIK_BGN_YMD", "SES_MDL_CD"] |


## business_constants_in_design

| 項目 | 値 |
|---|---|
| note | 会社区分（0093 / 0452）が業務ルールの中核に埋め込まれている（D-SM-12）。 骨架の greenfield 案件では、この種の顧客固有事実をコードへ直書きせず、 マスタ／設定として外出しする設計を検討する。 |

### dummy_semi_product

| 項目 | 値 |
|---|---|
| pattern | 4[A-Z][0-9]{4} |
| range | 4A0000 ～ 4Z9999 |
| note | ダミー半製品コード。自動採番の採番範囲と判定に使う。 |

### reg_sts

| 項目 | 値 |
|---|---|
| 0 | 未確定 |
| 1 | 確定 |

### send_sts

| 項目 | 値 |
|---|---|
| 0 | 未送信 |
| 9 | 緊急配信 |

### companies

| code | label |
|---|---|
| 0093 | 飲料社 |
| 0452 | カルピス社 |

### factory

| code | label |
|---|---|
| 0001 | ビール社工場（BP の条件に現れる） |
| P030 | ビール社工場の事業場（BP の条件に現れる） |


## req_ids

## search_conditions

| False | name | type | condition | initial | len | note |
|---|---|---|---|---|---|---|
| 8 | 生産モデルコード | textbox | 前方一致 | 空白 | 17 |  |
| 9 | 生産モデルコード検索 | icon | - | - |  | オプション区分でアイテム／半製品／購入品目の入力支援を切替。戻り値に '-' を付けて設定 |
| 10 | アイテム名称 | textbox | 中間一致 | 空白 |  | オプション区分='1' の時のみ表示。シートの種別は誤って『ボタン』（D-SM-17） |
| 11 | 削除含む | checkbox | 未チェックなら DEL_FLG='0' | チェックなし |  |  |
| 12 | 購入品目コード | textbox | 前方一致 | 空白 | 6 |  |
| 13 | 購入品目コード検索 | icon | - | - |  |  |
| 14 | 購入品目名称 | textbox | 中間一致 | 空白 |  | 購入品目日本語名・略名の OR 検索 |
| 16 | 半製品コード | textbox | 前方一致 | 空白 | 6 |  |
| 17 | 半製品コード検索 | icon | - | - |  | ダミー半製品も検索対象 |
| 18 | 半製品名称 | textbox | 中間一致 | 空白 |  | 日本語名・略名・カナ名・略称2 の OR 検索 |
| 22 | １頁件数選択 | dropdown | - | 標準仕様 |  |  |
| 23 | 仕掛表示 | button | - | - |  | REG_STS='0'（未確定）を条件に加える |
| 24 | 表示 | button | - | - |  | REG_STS を条件に加えない |
| 25 | 検索結果非表示 | button | - | - |  |  |

## key_columns

| name | label | len | note |
|---|---|---|---|
| SES_MDL_CD | 生産モデルコード | 17 | 親番（'-' の前）と枝番（'-' の後）を 1 列に保持 |
| OYA_CD_KBN | 親コード区分 | 1 | 1=アイテム / 2=半製品 / 3=原材料。オプション区分と一致 |
| KO_CD_KBN | 子コード区分 | 1 | 1=半製品 / 2=購入品目 |
| KO_CD | 子コード | 7 |  |
| KSN_DAT | 更新時刻 |  | 排他チェックの比較対象 |
| REV_NO | リビジョン | 5 | 更新時 +1 |
| DEL_FLG | 論理削除フラグ | 1 |  |

## design_defects_in_field_sheet

- 検索シート No10『アイテム名称』の種別が『ボタン』になっている。テキストボックスが正（D-SM-17）。
- 明細マスタ項目シート No13『展開区分』の初期値が『リンクを押下した同行の調達対象外フラグ』になっている。展開区分が正（D-SM-16）。
- 検索シート No12/No16 はエンティティ桁 7 に対し表示桁 6。モデルコードの枝番が 6 桁であることと整合するが、桁欄が混在（D-SM-22）。
- 検索シートは No15 / 19 / 20 / 21 が欠番。行の挿入・削除の履歴とみられる（D-SM-15）。

## open_questions

- 概要シートの前提条件・使用頻度・画面区分の選択状態（抽出から判別不能）。
- 処方マスタ R60_SYOHO_M_TBL の自動生成は本画面のパッケージ呼出しに依存する。生成ロジックの詳細は本モジュール外。
- ダミー半製品の既定値 26 項目（DB10）は業務上の意味づけが設計に書かれていない。
- R60_HSH_SES_MODEL_REF_M_TBL / R60_KJO_SES_MODEL_M_TBL の削除で KSN_KBN / KSN_STF_ID を更新しないのは意図か。

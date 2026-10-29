---
id: KNOW-LEGACY-R60-MODULE-R60AREA-FIELDS-VIEW
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-modules-r60area-01-fields
scope: project
project_id: P-R60-001
title: R60Area — 項目定義（フィールド辞書）
doc_type: design-detail
conf_level: 30
updated_at: '2026-10-28'
---

# R60Area — 項目定義（フィールド辞書）

> 正本は同ディレクトリの `01-fields.yaml`。本ファイルは検索用の可読表現であり、
> 手で編集しない（`py -3 -m tools.kb_migrate --apply` で作り直す）。

| 項目 | 値 |
|---|---|
| id | KNOW-LEGACY-R60-MODULE-R60AREA-FIELDS |
| type | knowledge |
| status | draft |
| sensitivity | internal |
| owner | AI-SE |
| version | 0.1.0 |

## screen_item_inventory

| 項目 | 値 |
|---|---|
| discrepancy_note | 設計書の項目番号は検索シート 76 件・マスタシート 45 件である。 骨架側の I-201..I-256（56 件）とは一致しない。56 は R60Area の画面項目数を 表す値ではなく、骨架構築時に置いた仮の ID 枠である。→ 06-review.yaml D-AR-01。 |

### search_sheet

| 項目 | 値 |
|---|---|
| numbered_items | 76 |
| row_range | r15-r90 |

#### groups

| name | items | count |
|---|---|---|
| ヘッダー部 | [2, 3, 4, 5, 6] | 5 |
| 検索条件部 | [8, 9, 10, 11, 12, 13, 14, 15] | 8 |
| 検索結果部_ページャ | [17, 18, 19, 20, 21, 22] | 6 |
| 検索結果部_行操作 | [23, 24] | 2 |
| 検索結果部_一覧列 | 25-66 | 42 |
| 検索結果部_ページャ_下部 | [67, 68, 69, 70, 71] | 5 |
| ボタン部 | [73, 74, 75, 76] | 4 |

#### structure_rows

- 1
- 7
- 16
- 72


### master_sheet

| 項目 | 値 |
|---|---|
| numbered_items | 45 |
| row_range | r16-r60 |

#### groups

| name | items | count |
|---|---|---|
| ヘッダー部 | [2] | 1 |
| マスタ項目部 | 4-41 | 38 |
| ボタン部 | [43, 44, 45] | 3 |

#### structure_rows

- 1
- 3
- 42



## search_result_columns

| 項目 | 値 |
|---|---|
| note | 一覧はコード列と名称列の対で構成される。名称列は FUNCTION 経由で取得する。 |

### columns

| False | name | source | lookup | sortable |
|---|---|---|---|---|
| 24 | 送信 | エリアマスタ.SEND_STS | R60_Get_Code_Chi_Meisai_FNC('000000057', SEND_STS, '1') |  |
| 25 | 会社 | エリアマスタ.CMP_CD | R60_Get_Cmp_Information_FNC(CMP_CD, '1') | True |
| 26 | 事業場 | エリアマスタ.JIG_CD | R60_Get_Jig_Information_FNC(CMP_CD, JIG_CD, '2') | True |
| 27 | エリア情報：コード | エリアマスタ.ARA_CD | 単純移送 | True |
| 28 | エリア情報：名称 | エリアマスタ.ARA_NM | 右側全角スペース削除 |  |
| 29 | エリア情報：略称 | エリアマスタ.ARA_RNM | 右側全角スペース削除 |  |
| 30 | 受払場所：コード | エリアマスタ.UKH_PLC_CD | 単純移送 |  |
| 31 | 受払場所：名称 | エリアマスタ.UKH_PLC_CD | R60_Get_Ukh_Plc_Info_FNC(CMP_CD, JIG_CD, UKH_PLC_CD, '1') |  |
| 32 | 受払計上事業場：コード | エリアマスタ.UKH_KEIJ_JIG_CD | 単純移送 |  |
| 33 | 受払計上事業場：名称 | エリアマスタ.UKH_KEIJ_JIG_CD | R60_Get_Jig_Information_FNC(CMP_CD, UKH_KEIJ_JIG_CD, '2') |  |
| 34 | 受払計上部署：コード | エリアマスタ.UKH_KEIJ_BSY_CD | 単純移送 |  |
| 35 | 受払計上部署：名称 | エリアマスタ.UKH_KEIJ_BSY_CD | R60_Get_Hiyo_Keij_Bsy_Info_FNC(CMP_CD, UKH_KEIJ_BSY_CD, '1') |  |
| 36 | 債務計上事業場：コード | エリアマスタ.SAIM_KEIJ_JIG_CD | 単純移送 |  |
| 37 | 債務計上事業場：名称 | エリアマスタ.SAIM_KEIJ_JIG_CD | R60_Get_Jig_Information_FNC(CMP_CD, SAIM_KEIJ_JIG_CD, '2') |  |
| 38 | 債務計上部署：コード | エリアマスタ.SAIM_KEIJ_BSY_CD | 単純移送 |  |
| 39 | 債務計上部署：名称 | エリアマスタ.SAIM_KEIJ_BSY_CD | R60_Get_Hiyo_Keij_Bsy_Info_FNC(CMP_CD, SAIM_KEIJ_BSY_CD, '1') |  |
| 40 | 債権計上事業場：コード | エリアマスタ.SAIKN_KEIJ_JIG_CD | 単純移送 |  |
| 41 | 債権計上事業場：名称 | エリアマスタ.SAIKN_KEIJ_JIG_CD | R60_Get_Jig_Information_FNC(CMP_CD, SAIKN_KEIJ_JIG_CD, '2') |  |
| 42 | 債権計上部署：コード | エリアマスタ.SAIKN_KEIJ_BSY_CD | 単純移送 |  |
| 43 | 債権計上部署：名称 | エリアマスタ.SAIKN_KEIJ_BSY_CD | R60_Get_Hiyo_Keij_Bsy_Info_FNC(CMP_CD, SAIKN_KEIJ_BSY_CD, '1') |  |
| 44 | 自動払出承認フラグ | エリアマスタ.JID_HAR_SYN_FLG | R60_Get_Code_Chi_Meisai_FNC('000000115', JID_HAR_SYN_FLG, '0') |  |
| 45 | 支払案内書に表示する届先名 | エリアマスタ.SHR_ANSY_TDK_NM | 右側全角スペース削除 |  |
| 46 | 移動デフォルトロケーション（原材料）：コード | エリアマスタ.IDO_DFLT_PLC_CD_GZR | 単純移送 |  |
| 47 | 移動デフォルトロケーション（原材料）：名称 | エリアマスタ.IDO_DFLT_PLC_CD_GZR | R60_Get_Plc_Infomation_FNC(CMP_CD, JIG_CD, IDO_DFLT_PLC_CD_GZR, '1') |  |
| 48 | 移動デフォルトロケーション（半製品）：コード | エリアマスタ.IDO_DFLT_PLC_CD_HSH | 単純移送 |  |
| 49 | 移動デフォルトロケーション（半製品）：名称 | エリアマスタ.IDO_DFLT_PLC_CD_HSH | R60_Get_Plc_Infomation_FNC(CMP_CD, JIG_CD, IDO_DFLT_PLC_CD_HSH, '1') |  |
| 50 | 集中購買会社：コード | エリアマスタ.SYCH_KBI_CMP_CD | 単純移送 |  |
| 51 | 集中購買会社：名称 | エリアマスタ.SYCH_KBI_CMP_CD | R60_Get_Cmp_Information_FNC(SYCH_KBI_CMP_CD, '1') |  |
| 52 | 集中購買事業場：コード | エリアマスタ.SYCH_KBI_JIG_CD | 単純移送 |  |
| 53 | 集中購買事業場：名称 | エリアマスタ.SYCH_KBI_JIG_CD | R60_Get_Jig_Information_FNC(SYCH_KBI_CMP_CD, SYCH_KBI_JIG_CD, '2') |  |
| 54 | 集中購買受払計上事業場：コード | エリアマスタ.SYCH_KBI_UKH_KEIJ_JIG_CD | 単純移送 |  |
| 55 | 集中購買受払計上事業場：名称 | エリアマスタ.SYCH_KBI_UKH_KEIJ_JIG_CD | R60_Get_Jig_Information_FNC(SYCH_KBI_CMP_CD, SYCH_KBI_UKH_KEIJ_JIG_CD, '2') |  |
| 56 | 集中購買受払計上部署：コード | エリアマスタ.SYCH_KBI_UKH_KEIJ_BSY_CD | 単純移送 |  |
| 57 | 集中購買受払計上部署：名称 | エリアマスタ.SYCH_KBI_UKH_KEIJ_BSY_CD | R60_Get_Hiyo_Keij_Bsy_Info_FNC(SYCH_KBI_CMP_CD, SYCH_KBI_UKH_KEIJ_BSY_CD, '1') |  |
| 58 | 集中購買債務計上事業場：コード | エリアマスタ.SYCH_KBI_UKH_SAIM_JIG_CD | 単純移送 |  |
| 59 | 集中購買債務計上事業場：名称 | エリアマスタ.SYCH_KBI_UKH_SAIM_JIG_CD | R60_Get_Jig_Information_FNC(SYCH_KBI_CMP_CD, SYCH_KBI_UKH_SAIM_JIG_CD, '2') |  |
| 60 | 集中購買債務計上部署：コード | エリアマスタ.SYCH_KBI_UKH_SAIM_BSY_CD | 単純移送 |  |
| 61 | 集中購買債務計上部署：名称 | エリアマスタ.SYCH_KBI_UKH_SAIM_BSY_CD | R60_Get_Hiyo_Keij_Bsy_Info_FNC(SYCH_KBI_CMP_CD, SYCH_KBI_UKH_SAIM_BSY_CD, '1') |  |
| 62 | 集中購買債権計上事業場：コード | エリアマスタ.SYCH_KBI_UKH_SAIKN_JIG_CD | 単純移送 |  |
| 63 | 集中購買債権計上事業場：名称 | エリアマスタ.SYCH_KBI_UKH_SAIKN_JIG_CD | R60_Get_Jig_Information_FNC(SYCH_KBI_CMP_CD, SYCH_KBI_UKH_SAIKN_JIG_CD, '2') |  |
| 64 | 集中購買債権計上部署：コード | エリアマスタ.SYCH_KBI_UKH_SAIKN_BSY_CD | 単純移送 |  |
| 65 | 集中購買債権計上部署：名称 | エリアマスタ.SYCH_KBI_UKH_SAIKN_BSY_CD | R60_Get_Hiyo_Keij_Bsy_Info_FNC(SYCH_KBI_CMP_CD, SYCH_KBI_UKH_SAIKN_BSY_CD, '1') |  |
| 66 | 削除 | エリアマスタ.DEL_FLG | R60_Get_Code_Chi_Meisai_FNC('000000063', DEL_FLG, '1') |  |


## db_table

| 項目 | 値 |
|---|---|
| logical_name | エリアマスタ |
| physical_name | R60_AREA_M_TBL |
| table_id | R60_AREA_M_TBL |
| column_count | 37 |

### columns

| False | name | column_id | length | insert | update | delete | screen_item | edit_spec |
|---|---|---|---|---|---|---|---|---|
| 1 | 会社コード | CMP_CD | 4 | True | False | False | 会社 | リスト選択値 |
| 2 | 事業場コード | JIG_CD | 4 | True | False | False | 事業場 | リスト選択値 |
| 3 | エリアコード | ARA_CD | 7 | True | False | False | エリアコード | 画面入力値 |
| 4 | エリア日本語名称 | ARA_NM | 30 | True | True | True | エリア名 | 画面入力値 |
| 5 | エリア略称 | ARA_RNM | 16 | True | True | True | エリア略称 | 画面入力値 |
| 6 | 受払場所コード | UKH_PLC_CD | 4 | True | True | True | 受払場所 | 画面入力値 |
| 7 | 受払計上事業場コード | UKH_KEIJ_JIG_CD | 4 | True | True | True | 受払計上事業場 | リスト選択値 |
| 8 | 受払計上部署コード | UKH_KEIJ_BSY_CD | 8 | True | True | True | 受払計上部署 | リスト選択値 |
| 9 | 債務計上事業場コード | SAIM_KEIJ_JIG_CD | 4 | True | True | True | 債務計上事業場 | リスト選択値 |
| 10 | 債務計上部署コード | SAIM_KEIJ_BSY_CD | 8 | True | True | True | 債務計上部署 | リスト選択値 |
| 11 | 債権計上事業場コード | SAIKN_KEIJ_JIG_CD | 4 | True | True | True | 債権計上事業場 | リスト選択値 |
| 12 | 債権計上部署コード | SAIKN_KEIJ_BSY_CD | 8 | True | True | True | 債権計上部署 | リスト選択値 |
| 13 | 自動払出承認フラグ | JID_HAR_SYN_FLG | 1 | True | True | True | 自動払出承認フラグ | リスト選択値 |
| 14 | 支払案内書に表示する届先名 | SHR_ANSY_TDK_NM | 50 | True | True | True | 支払案内書に表示する届先名 | 画面入力値 |
| 15 | 移動デフォルトロケーション(原材料) | IDO_DFLT_PLC_CD_GZR | 8 | True | True | True | 移動デフォルトロケーション(原材料) | 画面入力値 |
| 16 | 移動デフォルトロケーション(半製品) | IDO_DFLT_PLC_CD_HSH | 8 | True | True | True | 移動デフォルトロケーション(半製品) | 画面入力値 |
| 17 | 集中購買会社コード | SYCH_KBI_CMP_CD | 4 | True | True | True | 集中購買会社 | リスト選択値 |
| 18 | 集中購買事業場コード | SYCH_KBI_JIG_CD | 4 | True | True | True | 集中購買事業場 | リスト選択値 |
| 19 | 集中購買受払計上事業場コード | SYCH_KBI_UKH_KEIJ_JIG_CD | 4 | True | True | True | 集中購買受払計上事業場 | リスト選択値 |
| 20 | 集中購買受払計上部署コード | SYCH_KBI_UKH_KEIJ_BSY_CD | 8 | True | True | True | 集中購買受払計上部署 | リスト選択値 |
| 21 | 集中購買債務計上事業場コード | SYCH_KBI_UKH_SAIM_JIG_CD | 4 | True | True | True | 集中購買債務計上事業場 | リスト選択値 |
| 22 | 集中購買債務計上部署コード | SYCH_KBI_UKH_SAIM_BSY_CD | 8 | True | True | True | 集中購買債務計上部署 | リスト選択値 |
| 23 | 集中購買債権計上事業場コード | SYCH_KBI_UKH_SAIKN_JIG_CD | 4 | True | True | True | 集中購買債権計上事業場 | リスト選択値 |
| 24 | 集中購買債権計上部署コード | SYCH_KBI_UKH_SAIKN_BSY_CD | 8 | True | True | True | 集中購買債権計上部署 | リスト選択値 |
| 25 | 登録ステータス | REG_STS | 1 | True | True | True | 共通仕様参照 | - |
| 26 | 送信ステータス | SEND_STS | 1 | True | True | True | 緊急配信 | 画面入力値(チェックオン:9、チェックオフ:0) |
| 27 | 送信区分 | SEND_KBN | 1 | True | False | False | - | 登録:0固定 |
| 28 | 論理削除フラグ | DEL_FLG | 1 | True | True | True | 削除 | 登録:0固定、更新・削除:画面値(チェックオン:1、チェックオフ:0) |
| 29 | 登録区分 | REG_KBN | 1 | True | False | False | 共通仕様参照 | - |
| 30 | 登録者ＩＤ | REG_STF_ID | 10 | True | False | False | 共通仕様参照 | - |
| 31 | 登録刻 | REG_DAT |  | True | False | False | 共通仕様参照 | - |
| 32 | 登録プログラムＩＤ | REG_PGM_ID | 20 | True | False | False | 共通仕様参照 | - |
| 33 | 更新区分 | KSN_KBN | 1 | True | True | True | 共通仕様参照 | - |
| 34 | 更新者ＩＤ | KSN_STF_ID | 10 | True | True | True | 共通仕様参照 | - |
| 35 | 更新刻 | KSN_DAT |  | True | True | True | 共通仕様参照 | - |
| 36 | 更新プログラムＩＤ | KSN_PGM_ID | 20 | True | True | True | 共通仕様参照 | - |
| 37 | リビジョン | REV_NO | 5 | True | True | True | 共通仕様参照 | - |


## key_fields

| 項目 | 値 |
|---|---|
| logical_delete | DEL_FLG |
| registration_status | REG_STS |
| emergency_distribution | SEND_STS |

### primary_key

- CMP_CD
- JIG_CD
- ARA_CD

### exclusive_control

- KSN_DAT
- REV_NO


## req_ids

## related_masters

| table | usage | key |
|---|---|---|
| R60_COMPANY_M_TBL | 会社ドロップダウン / 集中購買会社 | CMP_CD |
| R60_JIG_M_TBL | 事業場ドロップダウン / 各計上事業場 | ["CMP_CD", "JIG_CD"] |
| R60_UKH_PLC_M_TBL | 受払場所ドロップダウン | ["CMP_CD", "JIG_CD", "UKH_PLC_CD"] |
| R60_HIYO_KEIJ_BSY_M_TBL | 各計上部署ドロップダウン | ["CMP_CD", "JIG_CD", "BSY_CD"] |
| R60_PLC_M_TBL | 移動デフォルトロケーション存在チェック / 名称取得 | ["CMP_CD", "JIG_CD", "PLC_CD"] |
| コード値マスタ(明細) | 自動払出承認フラグ / 送信ステータス / 論理削除 / 初期値 | ["情報ID", "KEYID"] |

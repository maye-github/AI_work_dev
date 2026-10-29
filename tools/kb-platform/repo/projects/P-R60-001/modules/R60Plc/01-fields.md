---
id: KNOW-LEGACY-R60-MODULE-R60PLC-FIELDS-VIEW
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-modules-r60plc-01-fields
scope: project
project_id: P-R60-001
title: R60Plc — 項目定義（フィールド辞書）
doc_type: design-detail
conf_level: 30
updated_at: '2026-10-29'
generated_by: tools/kb_migrate.py
---

# R60Plc — 項目定義（フィールド辞書）

> 正本は同ディレクトリの `01-fields.yaml`。本ファイルは検索用の可読表現であり、
> 手で編集しない（`py -3 -m tools.kb_migrate --apply` で作り直す）。

| 項目 | 値 |
|---|---|
| id | KNOW-LEGACY-R60-MODULE-R60PLC-FIELDS |
| type | knowledge |
| status | open |
| sensitivity | internal |
| owner | AI-SE |
| version | 0.1.0 |

## identification

| 項目 | 値 |
|---|---|
| screen_id | R60Plc |
| screen_name | ロケーションマスタメンテナンス |
| subsystem | 生産系共通マスタシステム |
| build_mode_observed | migration |
| screen_class | 検索一覧＋マスタ項目モーダル（新規・複製・修正） |
| premise | なし |
| exclusive | あり（KSN_DAT による排他） |
| frequency | 月次・随時 |
| permission | 利用権限保持者のみ（登録・削除は権限区分 Y の時に関数で判定） |

## item_counts

| 項目 | 値 |
|---|---|
| total_actual_items | 102 |
| count_rule | No の最大値ではなく、節見出し行を除いた実項目で数える。 最大値で数えると 109 になり 7 件多く見える（D-PL-01）。 |
| skeleton_comparison | 骨架の貫通例（R60Area）は 56 画面項目。本画面は検索 65 ＋ マスタ 37 ＝ 102 で、 R60Area より大きい。項目数は画面規模の指標であって骨架の固定値ではない。 |

### search_sheet

| 項目 | 値 |
|---|---|
| max_no | 69 |
| actual_items | 65 |
| check | 5 + 10 + 3 + 5 + 1 + 32 + 5 + 4 = 65 |

#### breakdown

| 項目 | 値 |
|---|---|
| header | 5 |
| search_conditions | 10 |
| condition_buttons | 3 |
| upper_pager | 5 |
| result_count | 1 |
| result_section | 32 |
| lower_pager | 5 |
| bottom_buttons | 4 |

#### section_rows

- 1
- 7
- 21
- 65


### master_sheet

| 項目 | 値 |
|---|---|
| max_no | 40 |
| actual_items | 37 |
| check | 1 + 33 + 3 = 37 |

#### breakdown

| 項目 | 値 |
|---|---|
| header | 1 |
| master_items | 33 |
| buttons | 3 |

#### section_rows

- 1
- 3
- 37



## result_columns

| 項目 | 値 |
|---|---|
| count | 31 |

### sortable

- 会社
- 事業場
- ロケーション：コード

### groups

| group | columns |
|---|---|
| キー | ["会社", "事業場", "エリア", "ロケーション：コード"] |
| 名称 | ["ロケーション：名称", "ロケーション：略称"] |
| 分類 | ["ロケグループ：コード", "ロケグループ：名称", "ロケタイプ：コード", "ロケタイプ：名称", "ロケ属性"] |
| 容量・深度 | ["最大容量(L)", "最大容量(KG)", "最大深さ", "開始検定深さ"] |
| 管理フラグ | ["FIFO", "後残管理", "流量管理", "検尺管理", "検尺検定", "検尺単位", "実／仮区分：タンク", "実／仮区分：サイロ", "複数品目", "受入品目チェック", "マイナス在庫", "外貨受入", "ALC別在庫管理", "補助材料投入可能", "並び順区分"] |
| 状態 | ["削除"] |


## master_items

| 項目 | 値 |
|---|---|
| delete_checkbox | 削除（エンティティは設計上エリアマスタ／論理削除フラグと書かれるが、実装はロケーションマスタ） |

### editable

- エリア / ロケーションコード（新規・複製のみ） / ロケーション名称 / ロケーション略称
- ロケグループ / ロケタイプ / ロケ属性 / 最大容量(L) / 最大容量(KG)
- FIFO / 後残管理 / 流量管理 / 検尺管理 / 検尺検定 / 検尺単位
- 最大深さ / 開始検定深さ / 仮想タンク区分 / 仮想サイロ区分
- 複数品目 / 受入品目チェック / マイナス在庫 / 外貨受入 / ALC別在庫管理 / 補助材料投入可能 / 並び順区分

### label_only

- 会社（新規・複製はドロップダウン、修正はラベル）
- 事業場（同上）


## db_model

| 項目 | 値 |
|---|---|
| table | R60_PLC_M_TBL |
| table_id | ロケーションマスタ |
| columns_total | 41 |
| check | 更新 ○ は No4-30（27 列）、No32（DEL_FLG）、No37-41（5 列）で計 33 列。 No31（SEND_KBN）と No33-36（登録系）は更新対象外。 |
| survey_note | reports/module-survey/scores/R60Plc.yaml は『42 カラム』と記録するが、 項目移送表の実列は No1-41 の 41 列である。調査票の数え方は未確認。本カードは 41 を採る（D-PL-14）。 |

### operation_flags

| 項目 | 値 |
|---|---|
| insert_columns | 41 |
| update_columns | 33 |
| delete_columns | 33 |
| physical_delete | False |

### business_key

- CMP_CD
- JIG_CD
- PLC_CD


## conditional_required

| 項目 | 値 |
|---|---|
| trigger | ロケーション属性区分 = 02（タンク） |
| note | 設計は同じ条件を箇所により「2:タンク」「02:タンク」と書く。実装は "02" で判定する（D-PL-06）。 |

### extra_required

- 検尺管理区分
- 検尺検定区分
- 検尺単位
- 最大深さ
- 開始検定深さ
- 仮想タンク区分


## deprecated_sheet

| 項目 | 値 |
|---|---|
| path | reports/module-survey/R60Plc/design/14_廃止_画面項目内容(入力).txt |
| actual_items | 19 |
| finding | シート名は『廃止_画面項目内容(入力)』だが、内容はメーカーコード・メーカー日本語名・ メーカーカナ名・緊急配信・削除で、R60Maker の項目が残っている。 R60Plc の入力仕様として読んではならない。 |
| retracted | True |

## req_ids

## search_conditions

| False | name | type | condition | initial | role |
|---|---|---|---|---|---|
| 8 | 会社 | dropdown | 完全一致 | ログインユーザーの所属会社 |  |
| 9 | 事業場 | dropdown | 完全一致 | ログインユーザーの所属事業場 |  |
| 10 | エリア | dropdown | 完全一致 | ブランク |  |
| 11 | ロケーションコード | textbox | 前方一致 | 未設定 |  |
| 13 | ロケーション名 | textbox | 中間一致 | 未設定 |  |
| 14 | 削除含む | checkbox | チェックなしなら DEL_FLG=0 | チェックなし |  |
| 15 | ロケーショングループ | dropdown | 完全一致 | ブランク |  |
| 16 | ロケーションタイプ | dropdown | 完全一致 | ブランク |  |
| 17 | １頁件数 | dropdown | 明細 情報ID 000000174 | 個別項目名10='D' |  |
| 12 | ロケーションコード検索 | button |  |  | 入力支援画面 R60PlcSup を起動 |

## key_columns

| name | label | len | note |
|---|---|---|---|
| CMP_CD | 会社コード | 4 | 業務キー |
| JIG_CD | 事業場コード | 4 | 業務キー |
| PLC_CD | ロケーションコード | 8 | 業務キー、半角英数大文字と記号 _ - ( ) のみ |
| ARA_CD | エリアコード | 7 |  |
| PLC_NM | ロケーション名 | 24 |  |
| PLC_RNM | ロケーション略称 | 16 |  |
| DEL_FLG | 論理削除フラグ | 1 | 本画面の『削除』はこの列を 1 にする UPDATE |
| REG_STS | 登録ステータス | 1 | 必須 18 項目＋タンク時 6 項目が揃えば 1 |
| KSN_DAT | 更新時刻 |  | 排他チェックの比較対象 |
| REV_NO | リビジョン | 5 | 更新時 +1 |

## design_defects_in_field_sheet

- マスタ項目 No8 エリアの初期値が『一覧で選択されたデータの事業場』と書かれ、エリアになっていない（D-PL-05）。
- マスタ項目 No24 開始検定深さの初期値が『一覧で選択されたデータの最大深さ』と書かれている（D-PL-05）。
- マスタ項目 No34 削除のエンティティが『エリアマスタ／論理削除フラグ』で、ロケーションマスタではない（D-PL-05）。

## open_questions

- ロケーション属性区分の選択肢値が 2 なのか 02 なのか。設計内で表記が揺れる。
- 削除チェックボックスの対象テーブルが設計ではエリアマスタ。実装はロケーションマスタ。どちらが正か。

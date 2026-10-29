---
id: KNOW-LEGACY-R60-MODULE-R60KKUCHI-FIELDS-VIEW
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-modules-r60kkuchi-01-fields
scope: project
project_id: P-R60-001
title: R60KkuChi — 項目定義（フィールド辞書）
doc_type: design-detail
conf_level: 30
updated_at: '2026-10-28'
---

# R60KkuChi — 項目定義（フィールド辞書）

> 正本は同ディレクトリの `01-fields.yaml`。本ファイルは検索用の可読表現であり、
> 手で編集しない（`py -3 -m tools.kb_migrate --apply` で作り直す）。

| 項目 | 値 |
|---|---|
| id | KNOW-LEGACY-R60-MODULE-R60KKUCHI-FIELDS |
| type | knowledge |
| status | draft |
| sensitivity | internal |
| owner | AI-SE |
| version | 0.1.0 |

## identification

| 項目 | 値 |
|---|---|
| screen_id | R60KkuChi |
| screen_name | 規格値マスタメンテナンス |
| subsystem | 生産系共通マスタシステム |
| build_mode_observed | migration |
| screen_class | 検索一覧＋マスタ項目領域（同一画面内）／12 キーパターン同居 |
| premise | なし |
| exclusive | あり（KSN_DAT による排他。行なしも W0006 → D-KK-05） |
| frequency | 月次・随時 |
| permission | 利用権限保持者のみ |

### operation_modes

| mode | name | note |
|---|---|---|
| 1 | 新規 |  |
| 2 | 複製 |  |
| 3 | 修正 |  |
|  | 削除 | 独立した /delete 端点。モード番号は使わない（del_flg=1 の UPDATE） |


## pattern_matrix

| 項目 | 値 |
|---|---|
| note | キーパターン（管理項目コード）ごとに、意味を持つキー列が決まる。 物理的な KEY_KMK_1〜6 への詰め方は実装の build_where が決める。 |
| item_count_rule | 各シートの No 採番の個数（節見出し行を含む）。実項目数ではない。 |

### item_total_observed

| 項目 | 値 |
|---|---|
| search_all | 218 |
| master_all | 173 |

### patterns

| code | screen | keys | search_items | master_items |
|---|---|---|---|---|
| 0010 | P1 | ["会社", "事業場", "半製品", "ロケタイプ"] | 28 | 25 |
| 0020 | P2 | ["会社", "半製品"] | 13 | 12 |
| 0030 | P3 | ["会社", "事業場", "製造列"] | 13 | 11 |
| 0040 | P4 | ["会社", "欠減区分"] | 11 | 10 |
| 0050 | P5 | ["会社", "事業場", "製造列", "購入品目分類4", "容器形態区分", "容器容量区分"] | 20 | 14 |
| 0060 | P6 | ["会社", "受払区分", "半製品品目分類4"] | 16 | 13 |
| 0070 | P7 | ["会社", "事業場", "半製品", "受払区分", "受払場所", "ロケグループ"] | 25 | 18 |
| 0080 | P8 | ["会社", "事業場", "受払場所", "仕込記号", "仕込系列"] | 21 | 14 |
| 0090 | P9 | ["会社", "半製品", "受払区分"] | 17 | 15 |
| 0100 | P10 | ["会社", "事業場", "半製品", "受払場所"] | 18 | 14 |
| 0110 | P11 | ["会社", "事業場", "ロケタイプ", "受払場所"] | 16 | 12 |
| 0120 | P12 | ["会社", "事業場", "半製品", "ロケタイプ", "受払場所"] | 20 | 15 |


## common_items

| 項目 | 値 |
|---|---|
| selection_rule | 項目が空白なら管理項目は空白のみ。項目を選ぶと、その項目を含むキーパターンだけを管理項目に並べる。 選択肢「会社」「事業場」は管理項目には表示しない（キー列としては使う）。 |

### key_sheet

| False | name | type | spec | source | note |
|---|---|---|---|---|---|
| 2 | 画面タイトル | label | 固定値「規格値マスタメンテナンス」 |  |  |
| 3 | システム日時 | label | YYYY/MM/DD hh:mm:ss |  |  |
| 4 | ログインユーザー会社 | label |  |  |  |
| 5 | ログインユーザー部署 | label |  |  |  |
| 6 | ログインユーザー名 | label |  |  |  |
| 8 | 項目 | dropdown |  | 情報ID 000000199 / 個別項目名2='1' / DEL_FLG=0 | 先頭に空白行 |
| 9 | 管理項目 | dropdown |  | 情報ID 000000197 / 個別項目名1 IN 0010..0120 / DEL_FLG=0 | 先頭に空白行 |
| 12 | 管理項目：{選択値} | label |  |  |  |
| 13 | << | link |  |  |  |
| 14 | < | link |  |  |  |
| 15 | ページ番号 | link |  |  |  |
| 16 | > | link |  |  |  |
| 17 | >> | link |  |  |  |
| 18 | 検索結果件数 | label |  |  |  |
| 19 | 複製 | button |  |  |  |


## p1_search

### conditions

| False | name | type | spec | len | condition | action | source | initial | rule |
|---|---|---|---|---|---|---|---|---|---|
| 2 | 会社 | dropdown | S 会社を表示し変更不可（他工更新権限がある場合のみ事業場を再生成） |  |  |  |  |  |  |
| 3 | 事業場 | dropdown | 複合値 会社コード,事業場コード。初期は S 事業場。他工更新権限なしは変更不可 |  |  |  |  |  |  |
| 4 | 半製品コード | textbox |  | 6 | 前方一致 |  |  |  |  |
| 5 | 半製品検索 | icon |  |  |  | 半製品入力支援を起動 |  |  |  |
| 6 | ロケタイプ | dropdown |  |  |  |  | ロケーションタイプマスタ |  |  |
| 7 | 1 頁件数 | dropdown | 標準仕様 |  |  |  |  |  |  |
| 8 | 削除含む | checkbox |  |  |  |  |  | False | オフなら DEL_FLG='0' を検索条件に追加 |
| 9 | 表示 | button |  |  |  |  |  |  |  |
| 10 | 検索条件(非)表示 | button |  |  |  |  |  |  |  |

### result_columns

| False | name | sortable | format | 999 | 990.999999 | source |
|---|---|---|---|---|---|---|
| 12 | 会社 | True |  |  |  |  |
| 13 | 事業場 | True |  |  |  |  |
| 14 | 半製品：コード | True |  |  |  |  |
| 15 | 半製品：名称 | False |  |  |  |  |
| 16 | ロケタイプ | True |  |  |  |  |
| 17 | 規格値(相対値)：下限％ | False | FM999 |  |  |  |
| 18 | 規格値(相対値)：上限％ | False |  |  |  |  |
| 19 | 規格値(相対値)：区分 | False |  |  |  | 000000192 |
| 20 | 規格値(相対値)：チェックレベル | False |  |  |  | 000000193 |
| 21 | 規格値(相対値)：メッセージID | False |  |  |  | 000000328 |
| 22 | 規格値(絶対値)：下限値 | False |  |  |  |  |
| 23 | 規格値(絶対値)：上限値 | False |  |  |  |  |
| 24 | 規格値(絶対値)：区分 | False |  |  |  |  |
| 25 | 規格値(絶対値)：チェックレベル | False |  |  |  |  |
| 26 | 規格値(絶対値)：メッセージID | False |  |  |  |  |
| 27 | 標準規格値 | False |  |  |  |  |
| 28 | 削除 | False |  |  |  | 000000063 |


## master_p1

| 項目 | 値 |
|---|---|
| button_rule | キーパターン 0020/0040/0060/0090 とそれ以外で、参照する権限判定の共通関数が変わる （登録は ①/②、削除は ①/③）。 |

### fields

| False | name | type | editable | len | note |
|---|---|---|---|---|---|
| 4 | 会社 | dropdown | False |  |  |
| 5 | 事業場 | dropdown | conditional |  |  |
| 6 | 半製品：コード | textbox | True | 6 |  |
| 7 | 半製品検索 | icon |  |  |  |
| 8 | 半製品：名称 | label | False |  |  |
| 9 | ロケタイプ | dropdown | True |  |  |
| 10 | 規格値下限％ | numeric | True | 15 |  |
| 11 | 規格値上限％ | numeric | True | 15 |  |
| 12 | 規格値上下限％区分 | dropdown | True |  |  |
| 13 | 規格値上下限％チェックレベル | dropdown | True |  |  |
| 14 | 規格値上下限％メッセージID | textbox | True | 9 |  |
| 15 | 規格値下限値 | numeric | True | 15 |  |
| 16 | 規格値上限値 | numeric | True | 15 |  |
| 17 | 規格値上下限値区分 | dropdown | True |  |  |
| 18 | 規格値上下限値チェックレベル | dropdown | True |  |  |
| 19 | 規格値上下限値メッセージID | textbox | True | 9 |  |
| 20 | 標準規格値 | numeric | True | 15 |  |
| 21 | 削除 | label |  |  | 論理削除フラグ |

### buttons

| False | name | initial |
|---|---|---|
| 23 | 戻る | 活性 |
| 24 | 削除 | 非活性（新規時）。削除済の行も非活性。権限区分 Y のときのみ活性判定を行う |
| 25 | 登録 | 活性 |


## db_model

| 項目 | 値 |
|---|---|
| table | R60_KKU_CHI_M_TBL |
| table_id | 規格値マスタ |
| columns_total | 32 |
| numeric_columns_note | 規格値の 6 列（下限％・上限％・下限値・上限値・標準規格値・その他）は 画面のカンマを除去して保存する（実装 .replace(",", "")）。 |

### operation_columns

| 項目 | 値 |
|---|---|
| insert | all_32 |
| delete | same_as_update |
| physical_delete | False |

#### update

- KKU_CHI_KAG
- KKU_CHI_JOG
- KKU_CHI_JOG_KAG_KBN
- KKU_CHI_JOG_KAG_CHK_LVL
- KKU_CHI_JOG_KAG_MSG_ID
- KKU_CHI_KAG_CHI
- KKU_CHI_JOG_CHI
- KKU_CHI_JOG_KAG_CHI_KBN
- KKU_CHI_JOG_KAG_CHI_CHK_LVL
- KKU_CHI_JOG_KAG_CHI_MSG_ID
- HJN_KKU_CHI
- DEL_FLG
- KSN_KBN
- KSN_STF_ID
- KSN_DAT
- KSN_PGM_ID
- REV_NO


### primary_key

- KNR_KMK_CD
- KEY_KMK_1
- KEY_KMK_2
- KEY_KMK_3
- KEY_KMK_4
- KEY_KMK_5
- KEY_KMK_6

### fixed_values

| column | value | timing |
|---|---|---|
| REG_STS | 1 | insert |
| SEND_STS | 0 | insert |
| SEND_KBN | 0 | insert |
| REG_KBN | 1 | insert |
| KSN_KBN | 1 | insert_and_update |
| DEL_FLG | 1 | delete |


## req_ids

## key_columns

| name | label | len | note |
|---|---|---|---|
| KNR_KMK_CD | 管理項目コード | 3 | 主キー（1 列目） |
| KEY_KMK_1 | キー項目１ | 10 | 主キー。パターンにより名称が変わる |
| KEY_KMK_2 | キー項目２ | 10 | 主キー |
| KEY_KMK_3 | キー項目３ | 10 | 主キー |
| KEY_KMK_4 | キー項目４ | 10 | 主キー |
| KEY_KMK_5 | キー項目５ | 10 | 主キー |
| KEY_KMK_6 | キー項目６ | 10 | 主キー |
| KSN_DAT | 更新時刻 |  | 排他の比較対象 |
| KSN_KBN | 更新区分 | 1 | オンライン='1' |
| REV_NO | リビジョン | 5 | 更新時 +1 |

## design_defects_in_field_sheet

- 各検索／マスタシートの項目数は No 採番の個数で、節見出し行を含む。実項目数として使わない。
- 「会社」「事業場」は項目ドロップダウンには出るが管理項目には出さない。設計 r64 の注記どおり。
- 事業場は複合値（会社コード,事業場コード）で持つが、KEY_KMK_2 には 2 番目のみを入れる。分解規則は本文に明記が無い。
- 画面区分のチェックボックスは抽出で記号が落ちており、どれが印されているか未確認。
- キー項目の物理位置はパターンごとに異なるが、設計の対応表は『意味のあるキー』の一覧で、位置までは書かない。

## open_questions

- 端点の単項目チェックをサーバー側へ寄せるか（D-KK-02）。
- 未知の mode をエラーにするか（D-KK-11）。
- 一括コピー画面を本画面の一部とみなすか、別モジュールとみなすか（D-KK-15）。
- KEY_KMK_1〜6 の詰め方の正本は設計のどこにあるか（実装の build_where が唯一の実装）。

---
id: KNOW-LEGACY-R60-MODULE-R60SESMODEL-API-VIEW
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-modules-r60sesmodel-02-api
scope: project
project_id: P-R60-001
title: R60SesModel — API 契約
doc_type: design-detail
conf_level: 30
updated_at: '2026-10-29'
generated_by: tools/kb_migrate.py
---

# R60SesModel — API 契約

> 正本は同ディレクトリの `02-api.yaml`。本ファイルは検索用の可読表現であり、
> 手で編集しない（`py -3 -m tools.kb_migrate --apply` で作り直す）。

| 項目 | 値 |
|---|---|
| id | KNOW-LEGACY-R60-MODULE-R60SESMODEL-API |
| type | knowledge |
| status | open |
| sensitivity | internal |
| owner | AI-SE |
| version | 0.1.0 |
| api_triggering_events | 17 |
| non_api_events | 11 |
| event_count_note | 実イベントは 28 件（No2-19 の 18 件＋No21-25 の 5 件＋No27-31 の 5 件）。 うち API を呼ぶもの 17 件（No2/6/7/9/10/11/12/15/16/17/18/19/24/25/27/30/31）、 呼ばないもの 11 件（No3/4/5/8/13/14/21/22/23/28/29）。 17 + 11 = 28。No8/18/19 は標準仕様で BP に記述がない。 |

## contract_conventions

| 項目 | 値 |
|---|---|
| transport | HTTP POST / JSON |
| base_path | /api/R60SesModel |
| request_envelope | { params: {...} }（edit のみ { params, child_list }） |
| wire_case | camelCase |
| internal_case | snake_case |
| case_conversion | BaseCamelModel(alias_generator=to_camel, populate_by_name=True, serialize_by_alias=True, extra='ignore') |
| online_gate | 全 12 端点の先頭で r60util.chk_onl_flg()。NG は OnlineException |
| simulation_tables | sim_kbn='0'（通常）以外は R60SimUtil.set_sim_info_all() で モジュール別のテーブル名へ差し替える（R60_SES_MODEL_M_TBL / R60_SES_MODEL_MES_M_TBL / R60_ITEM_M_TBL）。 |
| error_contract | 業務エラーは HTTP 200 のまま {error_code:'1', error_id, error_flg?} で返し、 画面側が message_info から文言を引く。error_code='3' はセッションエラー画面への遷移。 |
| note | extra='ignore' は骨架規則（03-design-coding.md §2 の extra='forbid'）と異なる。 実装の事実として記録し、骨架規則は変更しない（D-SM-04）。 |

## endpoint_inventory

| 項目 | 値 |
|---|---|
| observed | 12 |
| service_methods | 12 |
| survey_score_note | reports/module-survey/scores/R60SesModel.yaml の complexity.signals.endpoints は 16 と記録するが、 同ファイル自身が【推測】と注記している。実測は @router.post 12 件、Service メソッド 12 件（D-SM-01）。 |
| note | 死んだモデル定義が 2 組ある。旧 Java の品目検索・子コード名称取得を移植した残骸とみられる（D-SM-20）。 |

### decorators

| 項目 | 値 |
|---|---|
| init | 1735 |
| search | 1880 |
| download | 2172 |
| data_init | 2287 |
| init_edit | 2345 |
| edit | 2488 |
| delete | 3313 |
| search_child | 3740 |
| init_edit_child | 3850 |
| get_kon_hmk | 3950 |
| edit_child | 3984 |
| delete_child | 4382 |

### names

- init
- search
- download
- dataInit
- initEdit
- edit
- delete
- searchChild
- initEditChild
- getKonHmk
- editChild
- deleteChild

### dead_models

- GetItemParams / GetItemRequest / GetItemData / GetItemResponse（1001-1115 行）— 端点なし
- GetKoCdNmParams / GetKoCdNmRequest / GetKoCdNmResponse（1675-1732 行）— 端点なし。getKonHmk と役割が重複


## req_ids

## endpoints

| name | method | path | purpose | handler | request | response | behavior | message_ids | note | source_locator | response_item | risk_notes | behavior_new | behavior_modify | success | initial_values |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| init | POST | /api/R60SesModel/init | 検索画面の初期表示。事業場・頁件数・工場ユーザーフラグ・メッセージ情報を返す。 | R60SesModelController.py:1735-1873 | {"params": {"sim_kbn": "str（必須）", "login_cmp_cd": "str \| null", "login_jig_cd": "str \| null"}} | {"error_code": "str（'0' / '3'）", "sim_info": "SimInfo（シミュレーション区分に紐づくテーブル名）", "jig_list": "list[str]（情報ID 000000375、DEL_FLG=0、HYJ_SEQ・KEY_ID 昇順）", "page_limit_list": "list[{value: KOB_KMK_NM_1, label: CD_CHI_NM}]（情報ID 000000089）", "default_page_limit": "str（情報ID 000000089 で KOB_KMK_NM_10='D'、無ければ '10'）", "kjo_usr_flg": "str（'1'=工場ユーザー。情報ID 000000412 に 'CMP_CD\|\|JIG_CD' が存在）", "message_info": "dict[message_id, message_text]（36 件）"} | ["sim_kbn が空なら {'error_code':'3'} を返す（セッションエラー）。", "工場ユーザー判定はコード値マスタの情報ID 000000412 を COUNT する。"] | ["R60W0103", "R60W0010", "R60W0005", "R60I0001", "R60A0003", "R60W0006", "R60A0008", "R60W0007", "R60W0118", "R60W0012", "R60W0016", "R60W0015", "R60I0002", "R60A0004", "R60W0014", "R60W0011", "R60W0121", "R60W0009", "R60W0017", "R60W0018", "R60W0019", "R60W0108", "R60W0102", "R60W2050", "R60W2051", "R60W0020", "R60W2007", "R60E0025", "R60W0131", "R60W0031", "R60W0032", "R60W2019", "R60A0021", "R60I0022", "R60E0023", "R60W0101"] | R60W0001 は dataInit が返すが、この 36 件に含まれない（D-SM-10）。 R60W0101 / R60E0023 / R60A0021 / R60I0022 は画面側の使用箇所が薄い（未確認）。 | BP r14-r20（イベント No2） |  |  |  |  |  |  |
| search | POST | /api/R60SesModel/search | 表示／仕掛表示／ページ移動／ソートで一覧を返す。 | R60SesModelController.py:1880-2169 | {"params": {"sim_kbn": "str（必須）", "opt_kbn": "str（必須。'1'=アイテム, '2'=半製品, '3'=原材料）", "ses_mdl_cd": "str \| null（前方一致）", "item_nm": "str \| null（アイテム名称。opt_kbn='1' のみ有効）", "kon_hmk_cd": "str \| null（前方一致）", "kon_hmk_nm": "str \| null（購入品目名称）", "hsh_cd": "str \| null（前方一致）", "hsh_nm": "str \| null（半製品名称）", "is_deleted": "str（既定 '0'。'1' の時だけ削除済みを含む）", "btn": "str（'0'=仕掛表示, '1'=表示）", "current_page": "int（既定 1）", "page_limit": "str（既定 '10'）", "sort_field": "str \| null（SES_MDL_CD / SES_MDL_NM のみ許可）", "sort_order": "int \| null（1=昇順, それ以外=降順）", "login_cmp_cd": "str \| null（半製品の工場生産モデル判定に使用）", "login_jig_cd": "str \| null"}} | {"error_code": "str（'0' / '1'）", "error_id": "str \| null（R60W0010 / R60W0005）", "total": "int", "max_count": "str \| null（上限値）", "data": "list[SearchItemData]"} | ["上限件数は R60_GET_CODE_CHI_MEISAI_FNC('000000024','R60SesModel','0')。取得できなければ 500。", "件数 0 → R60W0010、上限超過 → R60W0005（total・max_count を返す）。", "仕掛表示（btn='0'）の時だけ REG_STS='0' を加える。表示（btn='1'）は REG_STS を絞らない。設計どおり（R60Plc の D-PL-07 と対照的）。", "削除含むが未チェック（is_deleted != '1'）なら DEL_FLG='0'。", "購入品目・半製品の名称/コード条件は get_ses_mdl_cd_condition() が再帰 SQL（CONNECT BY）で生産モデルコード集合を作る。", "並び順は DEL_FLG, {ソート列}, ROWID。ページングは OFFSET {n} ROWS FETCH FIRST {m} ROWS ONLY。", "SELECT 列は R60_GET_SELECT_COLUMN_FNC(tbl,'L') を直接埋め込む。"] | ["R60W0010", "R60W0005"] |  | BP r21-r425（イベント No6/No7） | {"send_sts_nm": "str", "ses_mdl_cd": "str", "ses_mdl_nm": "str", "oya_cd_kbn_nm": "str", "oya_cd_kbn": "str", "del_flg_nm": "str", "del_flg": "str", "kojo_cmp_cd": "str \| null（半製品のみ）", "kojo_jig_cd": "str \| null（半製品のみ）"} | ["件数取得 SQL は count_sb へ文字列連結する。ses_mdl_cd はクォート未エスケープで埋め込まれる（D-SM-05）。", "本検索は bind 変数を使うが、get_ses_mdl_cd_condition() の戻り文字列はそのまま埋め込む（D-SM-05）。"] |  |  |  |  |
| download | POST | /api/R60SesModel/download | 直前の検索条件・並び順で CSV を返す。 | R60SesModelController.py:2172-2286 | {"params": "search と同じ（current_page / page_limit / login_* を除く）"} | {"content_type": "text/csv（添付ファイル）", "filename": "R60CsvUtil（R60_SES_MODEL_M_VW の定義から生成）"} | ["明細ビュー R60_SES_MODEL_M_VW を検索する。", "WHERE 句は f-string で組み立て、ses_mdl_cd のみ replace(\"'\", \"''\") する。", "削除条件は is_deleted == '0' の時だけ DEL_FLG='0'（search の is_deleted != '1' と同値だが表現が異なる。D-SM-06）。", "ソートは search と同じ白名单＋ORDER BY。"] |  |  | BP r426-r471（イベント No15） |  | ["search は bind、download は文字列連結。方式が異なる（D-SM-05）。"] |  |  |  |  |
| dataInit | POST | /api/R60SesModel/dataInit | シミュレーション環境の生産モデル系データを初期化する。 | R60SesModelController.py:2287-2342 | {"params": {"sim_kbn": "str（必須）"}} | {"error_code": "str", "error_id": "str（R60W0001）", "message": "str \| null（モデル定義にあるが実装は返さない）"} | ["sim_kbn='0'（通常）は R60W0001 を返して拒否。", "R60L550BBean.do_r60l550b() を SES → SES_MES の順で 2 回実行し、commit する。", "Java は errMsgId='R60I0022' を設定するが、実装は error_id='' を返す。画面側が messageInfo.R60I0022 を自前で表示する。"] |  | R60W0001 は init の message_info に含まれないため、画面がこのエラーを 文言化できない可能性がある（D-SM-10）。 | BP r472-r493（イベント No17） |  |  |  |  |  |  |
| initEdit | POST | /api/R60SesModel/initEdit | ヘッダマスタ項目モーダルの初期化（新規／複製／修正）。 | R60SesModelController.py:2345-2481 | {"params": {"sim_kbn": "str（必須）", "opt_kbn": "str（必須）", "mode": "str（'1'=新規, '2'=複製, '3'=修正）", "ses_mdl_cd": "str \| null（mode=2/3 で使用）", "login_cmp_cd": "str \| null（mode=1・半製品の自動採番判定）"}} | {"error_code": "str", "error_id": "str \| null", "header_data": {"opt_kbn": "str", "oya_cd_kbn_nm": "str（親コード区分の表示名）", "oya_ban": "str \| null", "eda_ban": "str \| null", "ses_mdl_cd": "str \| null", "ses_mdl_nm": "str \| null", "del_flg": "str \| null", "send_sts": "str \| null", "send_kbn": "str \| null", "ksn_dat": "str \| null", "rev_no": "str \| null", "asd_stu_flg": "str \| null", "hsh_cd_chk_auto_val": "str（'on'/'off'）"}} | ["mode=1: 既定値のみ。opt_kbn='2' かつ login_cmp_cd in ('0093','0452') の時 hsh_cd_chk_auto_val='on'。", "mode=2: 複製元の生産モデルコード・名称を取得。ksn_dat/rev_no は空にリセット。", "mode=3: 選択行のフル項目を取得。", "明細は initEdit では返さない。別途 searchChild を呼ぶ。"] |  | InitEditHeaderData に mode フィールドは定義されていないが、 mode=3 の分岐で mode='修正' を渡している（extra='ignore' により応答へ出ない）（D-SM-21）。 | BP r494-r663（イベント No9/No11/No16） |  |  |  |  |  |  |
| edit | POST | /api/R60SesModel/edit | ヘッダの新規・複製・修正。必要に応じて明細の複製・削除・周辺マスタ更新まで行う。 | R60SesModelController.py:2488-3312 | {"params": {"sim_kbn": "str", "opt_kbn": "str", "mode": "str（'1'=新規, '2'=複製, '3'=修正）", "ses_mdl_cd": "str \| null", "oya_ban": "str \| null", "eda_ban": "str \| null", "ses_mdl_nm": "str \| null", "del_flg": "str \| null", "send_sts": "str \| null", "ksn_dat": "str \| null（mode=3 の排他）", "rev_no": "str \| null", "stf_id": "str \| null", "asd_stu_flg": "str \| null", "hsh_cd_chk_auto": "str（'on'/'off'）", "chk_knk_dist": "str（'9'=緊急配信 ON）"}, "child_list": "list[ChildEditData]（複製元の明細を渡す）"} | {"error_code": "str", "error_id": "str（R60W0014 / R60W0032 / R60W2019 / R60W0006 / R60E0025 / R60W0018 / R60W2007 / R60W2051 / R60W0017 / R60W0020）", "error_flg": "str \| null（R60W2019: 1=枯渇, 2=イベント(登録), 3=イベント(削除/修正) / R60W0017: 1=親子, 2=生産工場）", "message_id": "str \| null（モデル定義にあるが実装は返さない）", "ses_mdl_cd": "str（採番後の生産モデルコード）"} |  |  |  | BP r664-r1577（イベント No25） |  |  | ["単項目（フロント）→ 重複 R60W0014 → 親コード存在 R60W0011 → コピー元子コード存在 R60W0032 → ダミー半製品登録（DB10）→ イベント R60W2019 → ヘッダ INSERT（DB1）→ 明細複製（DB2）→ 処方マスタ生成 → 緊急配信パッケージ。"] | ["排他 R60W0006 → 親コード R60W0011 → イベント R60W2019 → 被参照 R60E0025/R60W0018 → 明細取得・状態確認 R60W2007 → ヘッダ UPDATE（DB1）→ 明細 UPDATE（DB2/7/8）→ ダミー半製品 UPDATE（DB4/10）→ I-Pro → 工場生産モデル削除（DB6/DB9）→ 処方マスタ UPDATE（DB3）→ 緊急配信。"] | ["error_code='0', error_id=''。完了文言はフロントが R60I0001（削除時は R60I0002）を表示する。"] |  |
| delete | POST | /api/R60SesModel/delete | ヘッダと配下の明細・ダミー半製品・工場生産モデル・関連マスタを削除する。 | R60SesModelController.py:3313-3737 | {"params": {"sim_kbn": "str", "opt_kbn": "str", "ses_mdl_cd": "str", "ses_mdl_nm": "str \| null", "ksn_dat": "str \| null", "stf_id": "str \| null", "chk_knk_dist": "str \| null"}} | {"error_code": "str", "error_id": "str（R60W0010 / R60W0006 / R60W2019 / R60W2007 / R60W2051 / R60W0017）", "error_flg": "str \| null", "message_id": "str \| null（実装は返さない）"} | ["W0010（対象なし）→ W0006（排他）→ W2019（イベント）→ W2007（緊急配信対象に明細なし）→ W2051（子マスタ未確定）→ W0017（親子）。", "SES_MODEL 論理削除（DB7）→ SES_MODEL_MES（DB8）→ ダミー半製品削除（DB4/DB10）→ 処方マスタ UPDATE（DB3）→ KJO 削除（DB6/DB9）→ I-Pro → 緊急配信 → commit。", "完了文言はフロントが R60I0002 を表示する。"] |  |  | BP r1266-r1577（イベント No24） |  |  |  |  |  |  |
| searchChild | POST | /api/R60SesModel/searchChild | 生産モデル明細一覧を返す。 | R60SesModelController.py:3740-3847 | {"params": {"sim_kbn": "str", "ses_mdl_cd": "str", "kjo_usr_flg": "str \| null（工場ユーザーフィルタ）", "reg_kbn_flg": "str \| null（工場コピー時）", "del_flg_param": "str \| null（'1'=削除済み明細も表示・全件カウント）"}} | {"error_code": "str", "error_id": "str \| null", "ko_cnt": "int（削除されていない明細件数）", "data": "list[SearchChildItemData]"} |  |  | 子コード名称は半製品マスタ／購入品目マスタから取得する。 名称取得に失敗しても行自体は返し、名称を空にする（設計の W0011 は 明細マスタ項目のチェックで発火する）。 | BP r566-r644（イベント No10/No12） | ["send_sts_nm", "ko_cd_kbn", "ko_cd_kbn_nm", "ko_cd", "ko_cd_nm", "syryo", "kij_chi", "tni", "del_flg_nm", "del_flg", "cyot_tsogai_flg", "tki_kbn", "ksn_dat", "rev_no"] |  |  |  |  |  |
| initEditChild | POST | /api/R60SesModel/initEditChild | 明細マスタ項目モーダルの初期化と 3 つのドロップダウン生成。 | R60SesModelController.py:3850-3948 | {"params": {"sim_kbn": "str", "ses_mdl_cd": "str", "mode": "str（'1'=新規, '2'=複製, '3'=修正）", "ko_cd_kbn": "str \| null", "ko_cd": "str \| null"}} | {"error_code": "str", "error_id": "str \| null", "data": "ChildEditData \| null", "ko_cd_kbn_list": "list[{value,label}]", "cyotgai_flg_list": "list[{value,label}]", "tki_kbn_list": "list[{value,label}]", "asd_stu_flg": "str \| null"} |  |  | 既定値の会社判定はフロント／バックのどちらで行うか設計に明記が無い。 実装は「仕入先区分」等の要求により分岐する（詳細は 03-logic を参照）。 | BP r1600-r1608（イベント No12/No16） |  |  |  |  |  | {"ko_cd_kbn": "会社が 0093/0452 なら '2'（購入品目）、それ以外は空", "cyot_tsogai_flg": "会社が 0093/0452 なら '0'", "kij_chi": "1"} |
| getKonHmk | POST | /api/R60SesModel/getKonHmk | 入力支援画面から返った子コードの名称を取得する。 | R60SesModelController.py:3950-3981 | {"params": {"sim_kbn": "str", "ko_cd_kbn": "str（'1'=半製品, '2'=購入品目）", "ko_cd": "str"}} | {"error_code": "str", "error_id": "str \| null（R60W0011）", "ko_cd_nm": "str \| null"} | ["半製品なら R60_Get_Hsh_Information_FNC、購入品目なら R60_Get_KonHmk_Information_FNC で名称を取得する。", "名称が取れなければ R60W0011。画面は ##1=『子コード(値)』、##2=『半製品マスタ／購入品目マスタ』を埋める。"] |  |  | BP r1609-r1618（イベント No27） |  |  |  |  |  |  |
| editChild | POST | /api/R60SesModel/editChild | 明細の新規・複製・修正。 | R60SesModelController.py:3984-4379 | {"params": {"sim_kbn": "str", "ses_mdl_cd": "str", "mode": "str（'1'=新規, '2'=複製, '3'=修正）", "stf_id": "str \| null", "kjo_usr_flg": "str \| null", "ko_cd_kbn": "str \| null", "ko_cd": "str \| null", "original_ko_cd": "str \| null（複製時に子コードを変えた場合の変更前コード）", "syryo": "str \| null", "kij_chi": "str \| null", "cyot_tsogai_flg": "str \| null", "tki_kbn": "str \| null", "del_flg": "str \| null", "ksn_dat": "str \| null", "rev_no": "str \| null"}} | {"error_code": "str", "error_id": "str（R60W0019 / R60W0018 / R60W0011 / R60W2050 / R60W2019 / R60W0014 / R60E0025 / R60W0006）", "error_flg": "str \| null", "message_id": "str \| null（実装は返さない）"} |  |  |  | BP r1710-r1935（イベント No31） |  |  | ["親削除 R60W0019 → 子コード存在 R60W0011 → 飲料社の購入品目分類 R60W2050 → イベント R60W2019 → 重複 R60W0014 → INSERT（DB11）→ 処方マスタ生成 → I-Pro。", "複製で子コードを変えた場合は、変更前の行を物理削除（DB12 相当）してから INSERT する。"] | ["復活是非 R60W0018 / E0025 → 存在 R60W0011 → 排他 R60W0006 → UPDATE（DB11）→ 処方マスタ生成 → I-Pro。"] |  |  |
| deleteChild | POST | /api/R60SesModel/deleteChild | 明細の論理削除。 | R60SesModelController.py:4382-4576 | {"params": {"sim_kbn": "str", "ses_mdl_cd": "str", "ko_cd_kbn": "str", "ko_cd": "str", "ksn_dat": "str \| null", "rev_no": "str \| null", "syryo": "str \| null", "kij_chi": "str \| null", "cyot_tsogai_flg": "str \| null", "tki_kbn": "str \| null", "stf_id": "str \| null"}} | {"error_code": "str", "error_id": "str（R60W0011 / R60W0006 / R60W2019）", "error_flg": "str \| null", "message_id": "str \| null（実装は返さない）"} | ["子コード存在 R60W0011 → 排他 R60W0006 → イベント R60W2019（flg=3）→ DEL_FLG='1' UPDATE（DB11）→ 処方マスタ生成 → I-Pro。", "完了文言はフロントが R60I0002 を表示する。"] |  |  | BP r1578-r1599（イベント No30） |  |  |  |  |  |  |

## event_to_endpoint_map

| event_no | name | endpoint | api | note |
|---|---|---|---|---|
| 2 | 初期表示 | init | True |  |
| 3 | 生産モデルコード検索アイコン |  | False | 入力支援画面（オプション区分で切替） |
| 4 | 購入品目コード検索アイコン |  | False |  |
| 5 | 半製品コードアイコン |  | False |  |
| 6 | 表示ボタン | search | True |  |
| 7 | 仕掛表示ボタン | search | True |  |
| 8 | 検索条件(非)表示 |  | False | 標準仕様 |
| 9 | 複製ボタン | initEdit | True | mode=2 |
| 10 | 明細ボタン | searchChild | True |  |
| 11 | 生産モデル(ヘッダ)リンク | initEdit | True | mode=3。併せて searchChild |
| 12 | 生産モデル(明細)リンク | initEditChild | True | mode=3 |
| 13 | 戻る |  | False |  |
| 14 | 業務終了 |  | False |  |
| 15 | ダウンロード | download | True |  |
| 16 | 新規ボタン | initEdit | True | mode=1。明細画面では initEditChild |
| 17 | データ初期化 | dataInit | True |  |
| 18 | ページ移動 | search | True | 標準仕様 |
| 19 | 一覧項目ソート | search | True | 標準仕様 |
| 21 | 半製品コード自動採番 |  | False |  |
| 22 | 生産モデルコード検索（ヘッダ） |  | False |  |
| 23 | マスタ項目(ヘッダ)戻る |  | False |  |
| 24 | マスタ項目(ヘッダ)削除 | delete | True |  |
| 25 | マスタ項目(ヘッダ)登録 | edit | True | 新規・複製・修正で共通 |
| 27 | 子コード検索 | getKonHmk | True | 入力支援画面の戻り値で名称取得 |
| 28 | 子コード区分変更 |  | False |  |
| 29 | マスタ項目(明細)戻る |  | False |  |
| 30 | マスタ項目(明細)削除 | deleteChild | True |  |
| 31 | マスタ項目(明細)登録 | editChild | True | 新規・複製・修正で共通 |

## open_points

- init の message_info 36 件に R60W0001 が無いのに dataInit が R60W0001 を返す（D-SM-10）。
- search の件数 SQL と get_ses_mdl_cd_condition が入力値をエスケープせず埋め込む（D-SM-05）。
- search と download で DEL_FLG 条件の書き方が異なる（D-SM-06）。
- dataInit は成功時に error_id='' を返すだけで、R60I0022 を返さない。
- 各更新系は message_id を返さず、フロントが固定文言を出す。設計のメッセージ契約と実装が一致しない。
- GetItem / GetKoCdNm のモデル定義が端点なしで残る（D-SM-20）。

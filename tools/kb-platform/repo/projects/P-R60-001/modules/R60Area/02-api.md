---
id: KNOW-LEGACY-R60-MODULE-R60AREA-API-VIEW
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-modules-r60area-02-api
scope: project
project_id: P-R60-001
title: R60Area — API 契約
doc_type: design-detail
conf_level: 30
updated_at: '2026-10-29'
generated_by: tools/kb_migrate.py
---

# R60Area — API 契約

> 正本は同ディレクトリの `02-api.yaml`。本ファイルは検索用の可読表現であり、
> 手で編集しない（`py -3 -m tools.kb_migrate --apply` で作り直す）。

| 項目 | 値 |
|---|---|
| id | KNOW-LEGACY-R60-MODULE-R60AREA-API |
| type | knowledge |
| status | open |
| sensitivity | internal |
| owner | AI-SE |
| version | 0.1.0 |

## contract_conventions

| 項目 | 値 |
|---|---|
| transport | HTTP POST / JSON |
| base_path | /api/R60Area |
| request_envelope | { params: {...} } |
| wire_case | camelCase |
| internal_case | snake_case |
| case_conversion | BaseCamelModel(alias_generator=to_camel, populate_by_name=True, serialize_by_alias=True, extra=ignore) |
| authentication | セッション情報（呼び出し元から引き継ぎ）。未確立時はセッションエラー画面へ遷移 |
| online_gate | 全端点の先頭で r60util.chk_onl_flg()。NG は OnlineException |

## req_ids

## endpoints

| name | method | path | purpose | handler | request | response | behavior | search_conditions | paging | sorting | risk_notes | validation_order | validation_order_new | validation_order_update |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| init | POST | /api/R60Area/init | 一覧画面の初期表示。ユーザ情報・メッセージ・検索条件ドロップダウンを返す。 | R60AreaController.py:1235 init | {"params": {}} | {"error_code": "str", "cmp_data": "list[{value: CMP_CD, label: CMP_NM}]", "jig_data": "list[{value: 'CMP_CD,JIG_CD', label: JIG_NM}]", "page_list": "list[{value, label}]", "page_default": "str \| null", "message_info": "dict[message_id, message_text]"} | ["ユーザ情報は標準仕様（セッション）から取得する。", "メッセージは R60_GET_MESSAGE_FNC で取得する。", "会社リスト：R60_COMPANY_M_TBL、DEL_FLG='0'、CMP_CD 昇順。", "事業場リスト：R60_JIG_M_TBL、DEL_FLG='0' かつ HYJ_SEQ IS NOT NULL、HYJ_SEQ・CMP_CD・JIG_CD 昇順。", "1 頁件数リストは標準仕様。"] |  |  |  |  |  |  |  |
| search | POST | /api/R60Area/search | 検索条件に該当するエリアマスタをページングして返す。 | R60AreaController.py:1429 search | {"params": {"cmp_cd": "str \| null（会社コード完全一致）", "jig_cd": "str \| null（'CMP_CD,JIG_CD' 形式。完全一致）", "ara_cd": "str \| null（前方一致。ワイルドカード不要）", "btn": "str（'0'=仕掛表示、'1'=表示）", "is_deleted": "str（'0'=削除を含まない、'1'=削除を含む）", "current_page": "int（1 起算）", "page_limit": "str（既定 10）", "sort_field": "str \| null（CMP_CD / JIG_CD / ARA_CD のみ許可）", "sort_order": "int \| null（1=昇順、その他=降順）"}} | {"error_code": "str", "error_id": "str \| null（R60W0010 / R60W0005）", "total": "int", "data": "list[SearchItemData]", "max_count": "str \| null（超過時のみ）"} |  | ["cmp_cd 指定時：CMP_CD = :CMP_CD", "jig_cd 指定時：JIG_CD = :JIG_CD（カンマ区切りの後半）", "ara_cd 指定時：ARA_CD LIKE :ARA_CD ESCAPE '\\'（前方一致）", "btn='0'（仕掛表示）：REG_STS = '0'", "is_deleted='0'：DEL_FLG = '0'"] | {"count_sql": "SELECT COUNT(CMP_CD) FROM R60_AREA_M_TBL WHERE ...", "page_sql": "SELECT ... ORDER BY {sort}, ROWID OFFSET {offset} ROWS FETCH FIRST {page_limit} ROWS ONLY", "max_count_source": "コード値マスタ(明細) 情報ID='000000024'", "max_count_behavior": "0 件 → R60W0010、上限超過 → R60W0005（上限値と HIT 件数を返す）"} | {"allowed_fields": ["CMP_CD", "JIG_CD", "ARA_CD"], "requested_sort": "ORDER BY DEL_FLG, {field} {ASC\|DESC}, ROWID", "default_sort": "ORDER BY DEL_FLG, CMP_CD, TO_NUMBER(R60_Get_Jig_Information_FNC(CMP_CD, JIG_CD, '3')), JIG_CD, ROWID"} |  |  |  |  |
| download | POST | /api/R60Area/download | 一覧に表示中の検索条件で CSV を生成して返す。 | R60AreaController.py:1650 download | {"params": {"cmp_cd": "str \| null", "jig_cd": "str \| null", "ara_cd": "str \| null", "btn": "str", "is_deleted": "str", "sort_field": "str \| null", "sort_order": "int \| null"}} | {"content_type": "text/csv（添付ファイル）", "filename": "R60CsvUtil.get_csv_name(R60_AREA_M_TBL)"} | ["CSV ヘッダ・データ項目は R60_GET_SELECT_COLUMN_FNC（H/D）で取得する。", "検索条件とソート順は表示／仕掛表示で使用したものを引き継ぐ。"] |  |  |  | ["検索条件の値を SQL 文字列へ直接連結している（search は bind パラメータ）。→ 06-review.yaml D-AR-05"] |  |  |  |
| initEdit | POST | /api/R60Area/initEdit | マスタ項目画面（新規・複製・修正）の初期データとドロップダウンを返す。 | R60AreaController.py:1713 init_edit | {"params": {"mode": "str（'1'=新規、'2'=複製、'3'=修正）", "cmp_cd": "str", "jig_cd": "str（'CMP_CD,JIG_CD' 形式）", "ara_cd": "str"}} | {"error_code": "str", "cmp_data": "list[{value, label}]", "jig_data": "list[{value, label}]", "ukh_plc_data": "list[{value, label}]", "hiyo_keiji_bsy_data": "list[{value, label}]", "jid_har_syn_flg_data": "list[{value, label}]", "sych_kbi_cmp_data": "list[{value, label}]", "jid_har_syn_flg_default": "str \| null（新規のみ）", "sych_kbi_cmp_cd_default": "str \| null（新規のみ）", "sych_kbi_ukh_saim_jig_cd_default": "str \| null（新規のみ）", "sych_kbi_ukh_saim_bsy_cd_default": "str \| null（新規のみ）", "sych_kbi_ukh_saikn_jig_cd_default": "str \| null（新規のみ）", "sych_kbi_ukh_saikn_bsy_cd_default": "str \| null（新規のみ）", "data": "InitEditDetailData \| null（複製・修正時）"} | ["mode='1' のとき、コード値マスタ(明細) 情報ID 000000315〜000000320 から初期値を取得する。", "mode in ('1','2') のとき会社・事業場リストを生成する。", "受払場所・費用計上部署・自動払出承認フラグ・集中購買会社リストは全モードで返す。", "mode='3' のとき対象行を R60_AREA_M_TBL から取得して data に返す。"] |  |  |  |  |  |  |  |
| getPlcNm | POST | /api/R60Area/getPlcNm | ロケーションコードからロケーション名称を取得する（入力補助）。 | R60AreaController.py:1992 get_plc_nm | {"params": {"plc_cd": "str", "cmp_cd": "str", "jig_cd": "str（'CMP_CD,JIG_CD' 形式）"}} | {"error_code": "str", "data": "str（ロケーション名称。未登録時は空）"} | ["R60_PLC_M_TBL を CMP_CD・JIG_CD・PLC_CD で検索する。"] |  |  |  |  |  |  |  |
| delete | POST | /api/R60Area/delete | エリアマスタを論理削除する（DEL_FLG='1'）。 | R60AreaController.py:2033 delete | {"params": {"cmp_cd": "str", "jig_cd": "str（'CMP_CD,JIG_CD' 形式）", "ara_cd": "str", "ksn_dat": "str", "stf_id": "str", "rev_no": "str", "ara_nm": "str \| null", "ara_rnm": "str \| null", "ukh_plc_cd": "str \| null", "ukh_keij_jig_cd": "str \| null", "ukh_keij_bsy_cd": "str \| null", "saim_keij_jig_cd": "str \| null", "saim_keij_bsy_cd": "str \| null", "saikn_keij_jig_cd": "str \| null", "saikn_keij_bsy_cd": "str \| null", "jid_har_syn_flg": "str \| null", "shr_ansy_tdk_nm": "str \| null", "ido_dflt_plc_cd_gzr": "str \| null", "ido_dflt_plc_cd_hsh": "str \| null", "sych_kbi_cmp_cd": "str \| null", "sych_kbi_jig_cd": "str \| null", "sych_kbi_ukh_keij_jig_cd": "str \| null", "sych_kbi_ukh_keij_bsy_cd": "str \| null", "sych_kbi_ukh_saim_jig_cd": "str \| null", "sych_kbi_ukh_saim_bsy_cd": "str \| null", "sych_kbi_ukh_saikn_jig_cd": "str \| null", "sych_kbi_ukh_saikn_bsy_cd": "str \| null", "send_sts": "str \| null"}} | {"error_code": "str", "error_id": "str \| null（R60E0025 / R60W0024 / R60W0006 / R60W0033）", "msg": "str \| null", "error_flg": "str \| null（ロケーション未登録時の項目識別）"} |  |  |  |  |  | ["1. 被参照チェック R60_Check_Area_Info_FNC（null → R60E0025、'1' → R60W0024）", "2. 排他チェック（KSN_DAT 不一致 かつ オンライン更新 → R60W0006）", "3. ロケーション存在チェック（未登録 → R60W0033）", "4. REG_STS 判定", "5. UPDATE（DEL_FLG='1'、SEND_STS、KSN_*、REV_NO+1）", "6. 緊急配信（SEND_STS='9' のとき R60_EMERGENCY_SEND_CTL_PKG）", "7. commit"] |  |  |
| edit | POST | /api/R60Area/edit | エリアマスタを新規登録・更新・論理削除する（登録ボタン共通）。 | R60AreaController.py:2324 edit | {"params": {"mode": "str（'1'=新規、'2'=複製、'3'=修正）", "stf_id": "str", "cmp_cd": "str", "jig_cd": "str（'CMP_CD,JIG_CD' 形式）", "ara_cd": "str", "ara_nm": "str \| null", "ara_rnm": "str \| null", "ukh_plc_cd": "str \| null", "ukh_keij_jig_cd": "str \| null", "ukh_keij_bsy_cd": "str \| null", "saim_keij_jig_cd": "str \| null", "saim_keij_bsy_cd": "str \| null", "saikn_keij_jig_cd": "str \| null", "saikn_keij_bsy_cd": "str \| null", "jid_har_syn_flg": "str \| null", "shr_ansy_tdk_nm": "str \| null", "ido_dflt_plc_cd_gzr": "str \| null", "ido_dflt_plc_cd_hsh": "str \| null", "sych_kbi_cmp_cd": "str \| null", "sych_kbi_jig_cd": "str \| null", "sych_kbi_ukh_keij_jig_cd": "str \| null", "sych_kbi_ukh_keij_bsy_cd": "str \| null", "sych_kbi_ukh_saim_jig_cd": "str \| null", "sych_kbi_ukh_saim_bsy_cd": "str \| null", "sych_kbi_ukh_saikn_jig_cd": "str \| null", "sych_kbi_ukh_saikn_bsy_cd": "str \| null", "send_sts": "str \| null", "del_flg": "str \| null", "rev_no": "str \| null", "ksn_dat": "str \| null"}} | {"error_code": "str", "error_id": "str \| null", "msg": "str \| null", "error_flg": "str \| null"} |  |  |  |  |  |  | ["1. 重複キーチェック（CMP_CD・JIG_CD・ARA_CD 存在 → R60W0014）", "2. ロケーション存在チェック（未登録 → R60W0033）", "3. REG_STS 判定", "4. INSERT", "5. 緊急配信（SEND_STS='9'）", "6. commit"] | ["1. 排他チェック（KSN_DAT 不一致 かつ オンライン更新 → R60W0006）", "2. ロケーション存在チェック（未登録 → R60W0033）", "3. REG_STS 判定", "4. DEL_FLG='1' のとき被参照チェック（null → R60E0025、'1' → R60W0024）", "5. UPDATE", "6. 緊急配信（SEND_STS='9'）", "7. commit"] |

## endpoint_to_event_mapping

| event_no | event | endpoint |
|---|---|---|
| 1 | 初期表示 | init |
| 3 | 仕掛表示ボタンクリック | search（btn='0'） |
| 4 | 表示ボタンクリック | search（btn='1'） |
| 6 | 複製ボタンクリック | initEdit（mode='2'） |
| 7 | 検索結果一覧リンククリック | initEdit（mode='3'） |
| 10 | ダウンロードボタンクリック | download |
| 11 | 新規ボタンクリック | initEdit（mode='1'） |
| 18 | 原材料ロケーション検索 | 入力支援画面（別画面） |
| 19 | 半製品ロケーション検索 | 入力支援画面（別画面） |
| 25 | 削除ボタンクリック | delete |
| 26 | 登録ボタンクリック | edit |
| 2,12,13,15,16,17,20,21,22,23 | ドロップダウン変更 | フロント内でリスト再生成（API 呼び出しなし） |
| 5,8,9,24 | 検索条件表示切替・戻る・業務終了 | 標準仕様（共通部品） |

## notes

- 設計書のイベント番号は 1..26。API は 7 端点で、イベント 2/12/13/15/16/17/20/21/22/23 はフロント側のリスト再生成であり API を持たない。
- 設計書 14_業務処理説明 のイベント番号（No16=ダウンロード、No25=削除、No26=登録）は 12_イベント一覧 と一致しない箇所がある。→ 06-review.yaml D-AR-04

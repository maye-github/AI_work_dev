---
id: KNOW-LEGACY-R60-MODULE-R60SSK-API-VIEW
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-modules-r60ssk-02-api
scope: project
project_id: P-R60-001
title: R60Ssk — API 契約
doc_type: design-detail
conf_level: 30
updated_at: '2026-10-28'
---

# R60Ssk — API 契約

> 正本は同ディレクトリの `02-api.yaml`。本ファイルは検索用の可読表現であり、
> 手で編集しない（`py -3 -m tools.kb_migrate --apply` で作り直す）。

| 項目 | 値 |
|---|---|
| id | KNOW-LEGACY-R60-MODULE-R60SSK-API |
| type | knowledge |
| status | draft |
| sensitivity | internal |
| owner | AI-SE |
| version | 0.1.0 |

## contract_conventions

| 項目 | 値 |
|---|---|
| transport | HTTP POST / JSON |
| base_path | /api/R60Ssk |
| request_envelope | { params: {...} } |
| wire_case | camelCase |
| internal_case | snake_case |
| case_conversion | BaseCamelModel(alias_generator=to_camel, populate_by_name=True, serialize_by_alias=True, extra='ignore') |
| authentication | セッション情報（呼び出し元から引き継ぎ）。未確立時はセッションエラー画面へ遷移 |
| online_gate | 全 5 端点の先頭で r60util.chk_onl_flg()。NG は OnlineException |
| note | extra='ignore' は骨架規則（03-design-coding.md §2 の extra='forbid'）と異なる。 実装の事実として記録し、骨架規則は変更しない（D-SS-04）。 |

## endpoint_inventory

| 項目 | 値 |
|---|---|
| observed | 5 |
| service_methods | 5 |
| survey_score_note | reports/module-survey/scores/R60Ssk.yaml は『8 端点』と記録しているが、 コントローラの @router.post と Service のメソッドはいずれも 5 件である。 調査票の端点数の数え方は未確認。本カードは実測 5 件を採る（D-SS-02）。 |

### names

- init
- search
- download
- initEdit
- edit


## req_ids

## endpoints

| name | method | path | purpose | handler | request | response | design_mapping | message_ids | note | source_locator | search_conditions | paging | sorting | behavior | risk_notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| init | POST | /api/R60Ssk/init | 一覧画面の初期表示。メッセージ・会社リスト・1 頁件数リストを返す。 | R60SskController.py:391-515 | {"params": {}} | {"error_code": "str", "messages": "dict[message_id, message_text]（16 件）", "cmp_data": "list[{value: KEY_ID, label: CD_CHI_NM}]（情報ID='000000104'、HYJ_SEQ・KEY_ID 昇順）", "page_list": "list[{value: KOB_KMK_NM_1, label: CD_CHI_NM}]（情報ID='000000065'）", "page_default": "str \| null（KOB_KMK_NM_10='D' の行）"} | ["BP r30-r34：ユーザ情報・権限情報は『標準仕様参照』。実装はメッセージ・会社・頁件数のみ返す。", "BP r39-r40：R60_GET_MESSAGE_FNC でメッセージを取得する。", "BP r45-r47：会社未選択なら組織ユニット検索を非活性。フロント側で制御する。"] | ["R60W0118", "R60W0113", "R60W0005", "R60W0010", "R60A0008", "R60W0009", "R60W0006", "R60W0007", "R60I0001", "R60A0003", "R60I0002", "R60A0004", "R60W0016", "R60W0106", "R60W0131", "R60W2002"] | R60W0118 / R60W0113 / R60I0002 / R60A0004 の 4 件は、本画面の設計シートにも フロント／バックエンドの実装にも使用箇所が無い（他画面からの流用と読める。D-SS-07）。 R60W0007 は設計シートに無いが、実装が戻る時の破棄確認に使う。 | BP r23-r47 |  |  |  |  |  |
| search | POST | /api/R60Ssk/search | 検索条件に該当する部署マスタをページングして返す。 | R60SskController.py:520-633 | {"params": {"cmp_cd": "str \| null（完全一致。ブランク時は条件に加えない）", "ssk_unit": "str \| null（前方一致。LIKE エスケープあり）", "sei_nm": "str \| null（中間一致。LIKE エスケープあり）", "sort_field": "str \| null（CMP_CD / SSK_UNIT / JIG_SSK_UNIT のみ許可）", "sort_order": "int \| null（1=昇順、-1=降順）", "current_page": "int（1 起算）", "page_limit": "str（1 頁件数）"}} | {"error_code": "str", "error_id": "str \| null（R60W0010 / R60W0005）", "total": "int", "total_pages": "int \| null", "max_count": "str \| null（上限超過時のみ）", "data": "list[{send_sts_nm, cmp_cd, cmp_nm, ssk_unit, jig_ssk_unit, sei_nm, s_cmp_cd, s_jig_cd, del_flg_nm, del_flg}]"} |  |  |  | BP r69-r108（イベントNo4） | ["cmp_cd 指定時：CMP_CD = :CMP_CD", "ssk_unit 指定時：SSK_UNIT LIKE :SSK_UNIT ESCAPE '\\'（値は ssk_unit + '%'）", "sei_nm 指定時：SEI_NM LIKE :SEI_NM ESCAPE '\\'（値は '%' + エスケープ + '%'）"] | {"count_sql": "SELECT COUNT(*) FROM R60_SSK_M_TBL WHERE ...", "page_sql": "SELECT {select_column} FROM R60_SSK_M_TBL WHERE ... ORDER BY {sort}, ROWID OFFSET {offset} ROWS FETCH FIRST {page_limit} ROWS ONLY", "max_count_source": "r60util.get_cod_mes_info(dbapi_conn, '000000024', 'R60Ssk', '0')", "max_count_behavior": "0 件 → R60W0010（total=0）、上限超過 → R60W0005（上限値と HIT 件数を返す）", "page_clamp": "current_page が総頁を超えたら最終頁へ、1 未満なら 1 へ補正する"} | {"allowed_fields": ["CMP_CD", "SSK_UNIT", "JIG_SSK_UNIT"], "requested_sort": "ORDER BY DEL_FLG, {field} {ASC\|DESC}, ROWID", "default_sort": "ORDER BY DEL_FLG, CMP_CD, SSK_UNIT, ROWID（方向未指定＝Oracle 既定の ASC）", "design_locator": "BP r92-r96（論理削除フラグ・会社コード・組織ユニットの昇順）", "sort_click_events": "イベント No7/8/9 は『標準仕様参照』で本文が無い（D-SS-08）"} |  |  |
| download | POST | /api/R60Ssk/download | 直前の表示で使った検索条件とソート順で CSV を生成して返す。 | R60SskController.py:638-683 | {"params": {"cmp_cd": "str \| null", "ssk_unit": "str \| null", "sei_nm": "str \| null", "sort_field": "str \| null", "sort_order": "int \| null"}} | {"content_type": "text/csv（添付ファイル）", "filename": "R60_GET_CODE_CHI_MEISAI_FNC('000000099', 'R60_SSK_M_TBL', '1')"} |  |  |  | BP r150-r174（イベントNo13） |  |  |  | ["CSV ヘッダは R60_GET_SELECT_COLUMN_FNC（H）、データは同（D）で取得する（BP r158-r167）。", "検索条件とソート順は表示ボタンで使用したものを引き継ぐ（BP r168-r169）。"] | ["cmp_cd / ssk_unit / sei_nm を WHERE 句へ文字列連結している（search は bind パラメータ）。→ D-SS-09"] |
| initEdit | POST | /api/R60Ssk/initEdit | マスタ項目画面（修正モード）の初期化。会社・事業場ドロップダウンと選択行を返す。 | R60SskController.py:690-783 | {"params": {"cmp_cd": "str（必須）", "ssk_unit": "str（必須）"}} | {"error_code": "str", "cmp_data": "list[{cmp_cd, cmp_nm}]（会社マスタ、DEL_FLG='0'、CMP_CD 昇順）", "jig_data": "list[{cmp_cd, jig_cd, jig_nm}]（会社＋事業場、双方 DEL_FLG='0'、HYJ_SEQ NOT NULL、HYJ_SEQ・CMP_CD・JIG_CD 昇順）", "row_data": "dict \| null（部署マスタ 1 行＋send_sts, ksn_kbn, ksn_dat, rev_no）"} | ["BP r113-r142：修正モードで起動し、ドロップダウンを生成する。", "BP r124-r127：経理用事業場リストは経理用会社の選択に連動する。実装は全件を返し、連動はフロント側で行う。"] |  |  | BP r111-r147（イベントNo10） |  |  |  |  |  |
| edit | POST | /api/R60Ssk/edit | 部署マスタを更新する（INSERT / DELETE は行わない）。 | R60SskController.py:788-885 | {"params": {"cmp_cd": "str（キー）", "ssk_unit": "str（キー）", "ksn_dat": "str（排他チェック用の更新日時 'YYYY/MM/DD HH24:MI:SS'）", "jig_ssk_unit": "str \| null", "sei_nm": "str \| null", "s_cmp_cd": "str \| null（経理用会社）", "s_jig_cd": "str \| null（経理用事業場）", "ksn_stf_id": "str（更新者 ID）", "rev_no": "str（現在のリビジョン）"}} | {"error_code": "str", "error_id": "str \| null（R60W0006）", "note": "完了メッセージは返さない。フロントが R60I0001 を表示する。"} | ["BP r193-r204：単項目・項目間チェック。実装はチェックをフロントに委ね、排他のみサーバで再実行する。", "BP r206-r208：REG_STS の設定。設計本文に『定数 REG_STS_ON を設定しているのでこの設定は無効』という実装メモが混入している（D-SS-10）。"] |  |  | BP r191-r215（イベントNo16） |  |  |  | ["排他：KSN_DAT を再読込し、不一致かつ KSN_KBN='1'（オンライン）なら R60W0006。", "REG_STS：会社・組織ユニット・事業場組織ユニット・正式名称の 4 項目がすべて非空なら '1'、それ以外は '0'。", "UPDATE は 9 列のみ（S_CMP_CD, S_JIG_CD, REG_STS, KSN_KBN, KSN_STF_ID, KSN_DAT, KSN_PGM_ID, REV_NO, SEND_STS）。", "KSN_KBN='1'、KSN_DAT=システム日時、KSN_PGM_ID='R60Ssk'、REV_NO=取得値+1、SEND_STS='0' を設定する。"] |  |

## event_to_endpoint_map

| event_no | name | endpoint | design |
|---|---|---|---|
| 1 | 初期表示 | init | BP r23-r47 |
| 2 | 会社ドロップダウン変更 |  | BP r49-r57（フロントのみ） |
| 3 | 組織ユニット検索アイコン |  | BP r59-r67（入力支援画面） |
| 4 | 表示ボタン | search | BP r69-r108 |
| 5 | 検索条件(非)表示 |  | 標準仕様参照 |
| 6 | ページ移動 | search | 標準仕様参照（実装上は search 再呼出） |
| 7 | ソート：会社 | search | 標準仕様参照（sort_field=CMP_CD） |
| 8 | ソート：事業場組織ユニット | search | 標準仕様参照（sort_field は名称から一意に決まらない） |
| 9 | ソート：組織ユニットコード | search | 標準仕様参照（sort_field は名称から一意に決まらない） |
| 10 | 一覧データリンク | initEdit | BP r111-r147 |
| 11 | 戻る（検索結果） |  | 標準仕様参照 |
| 12 | 業務終了 |  | 標準仕様参照（R60A0008） |
| 13 | ダウンロード | download | BP r150-r174 |
| 14 | 経理用会社変更 |  | BP r178-r188（フロントのみ） |
| 15 | 戻る（マスタ項目） |  | 標準仕様参照 |
| 16 | 登録 | edit | BP r191-r215 |

## open_points

- イベント No7/8/9 のソートキーは名称しか無く、実装の許可項目（CMP_CD / SSK_UNIT / JIG_SSK_UNIT）との対応が一意でない。
- search の requested_sort は指定列だけになり、既定の第 2・第 3 ソートキーが落ちる。設計の『会社→組織ユニット』の安定順序は ROWID でしか担保されない。
- download の SQL 連結はセキュリティ課題として記録するが、骨架側では修正しない（人（ユーザー）の裁定事項）。

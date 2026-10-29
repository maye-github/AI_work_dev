---
id: KNOW-LEGACY-R60-MODULE-R60MAKER-API-VIEW
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-modules-r60maker-02-api
scope: project
project_id: P-R60-001
title: R60Maker — API 契約
doc_type: design-detail
conf_level: 30
updated_at: '2026-10-29'
---

# R60Maker — API 契約

> 正本は同ディレクトリの `02-api.yaml`。本ファイルは検索用の可読表現であり、
> 手で編集しない（`py -3 -m tools.kb_migrate --apply` で作り直す）。

| 項目 | 値 |
|---|---|
| id | KNOW-LEGACY-R60-MODULE-R60MAKER-API |
| type | knowledge |
| status | open |
| sensitivity | internal |
| owner | AI-SE |
| version | 0.1.0 |

## contract_conventions

| 項目 | 値 |
|---|---|
| transport | HTTP POST / JSON |
| base_path | /api/R60Maker |
| request_envelope | { params: {...} } |
| wire_case | camelCase |
| internal_case | snake_case |
| case_conversion | BaseCamelModel(alias_generator=to_camel, populate_by_name=True, serialize_by_alias=True, extra='ignore') |
| authentication | セッション情報（呼び出し元から引き継ぎ）。未確立時はセッションエラー画面へ遷移 |
| online_gate | 全端点の先頭で r60util.chk_onl_flg()。NG は OnlineException |
| note | extra='ignore' は骨架規則（03-design-coding.md §2 の extra='forbid'）と異なる。 実装の事実として記録し、骨架規則は変更しない（06-review.yaml D-MK-04）。 |

## req_ids

## endpoints

| name | method | path | purpose | handler | request | response | behavior | source_locator | search_conditions | paging | sorting | risk_notes | mode_note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| init | POST | /api/R60Maker/init | 一覧画面の初期表示。ユーザ情報・メッセージ・1頁件数リストを返す。 | R60MakerController.py:561-669 | {"params": {}} | {"error_code": "str", "page_list": "list[{value: '個別項目名1', label: 'コード値名称'}]", "page_default": "str \| null（個別項目名10='D' の行）", "message_info": "dict[message_id, message_text]（19 件）"} | ["ユーザ情報は標準仕様（セッション）から取得する。", "権限情報を取得する（BP r32-r33。詳細は標準仕様参照で、本設計書に条件は無い）。", "R60_GET_MESSAGE_FNC で使用メッセージを取得する（BP r38-r39）。", "1頁件数リスト：R60_CODE_MES_M_TBL、情報ID='000000488'、DEL_FLG='0'、HYJ_SEQ・KEY_ID 昇順。"] | BP r22-r48 |  |  |  |  |  |
| search | POST | /api/R60Maker/search | 検索条件に該当するメーカーマスタをページングして返す。表示／仕掛表示を btn で切り替える。 | R60MakerController.py:670-816 | {"params": {"maker_cd": "str \| null（前方一致。値に % を付与）", "maker_nm": "str \| null（中間一致。LIKE エスケープあり）", "btn": "str（'0'=仕掛表示、'1'=表示）", "is_deleted": "str（'0'=削除を含まない、'1'=削除を含む）", "current_page": "int（1 起算）", "page_limit": "str（既定 10）", "sort_field": "str \| null（MAKER_CD / MAKER_NM のみ許可）", "sort_order": "int \| null（1=昇順、その他=降順）"}} | {"error_code": "str", "error_id": "str \| null（R60W0010 / R60W0005）", "total": "int", "data": "list[SearchItemData]（maker_cd, maker_nm, maker_anm, send_sts, del_flg_kanji, del_flg）", "max_count": "str \| null（上限超過時のみ）"} |  | BP r50-r87（イベントNo2）/ r89-r126（イベントNo3） | ["maker_cd 指定時：MAKER_CD LIKE :MAKER_CD（値は maker_cd + '%'）", "maker_nm 指定時：MAKER_NM LIKE :MAKER_NM ESCAPE '\\'（値は '%' + エスケープ + '%'）", "btn='0'（仕掛表示）：REG_STS = '0'", "is_deleted='0'：DEL_FLG = '0'"] | {"count_sql": "SELECT COUNT(ROWID) FROM R60_MAKER_M_TBL WHERE ...", "page_sql": "SELECT ... ORDER BY {sort}, ROWID OFFSET {offset} ROWS FETCH FIRST {page_limit} ROWS ONLY", "max_count_source": "コード値マスタ(明細) 情報ID='000000024'（BP r67-r68 は『共通仕様参照』）", "max_count_behavior": "0 件 → R60W0010、上限超過 → R60W0005（上限値と HIT 件数を返す）"} | {"allowed_fields": ["MAKER_CD", "MAKER_NM"], "requested_sort": "ORDER BY DEL_FLG, {field} {ASC\|DESC}, ROWID", "default_sort": "ORDER BY DEL_FLG, MAKER_CD, ROWID", "design_locator": "BP r63（論理削除フラグ昇順＋メーカーコード昇順）"} |  |  |
| download | POST | /api/R60Maker/download | 直前の表示／仕掛表示で使った検索条件とソート順で CSV を生成して返す。 | R60MakerController.py:817-883 | {"params": {"maker_cd": "str \| null", "maker_nm": "str \| null", "btn": "str", "is_deleted": "str", "sort_field": "str \| null", "sort_order": "int \| null"}} | {"content_type": "text/csv（添付ファイル）", "filename": "R60_GET_CODE_CHI_MEISAI_FNC('000000099', 'R60_MAKER_M_TBL', '1')"} | ["CSV ヘッダは R60_GET_SELECT_COLUMN_FNC（H）、データは同（D）で取得する。", "検索条件とソート順は表示／仕掛表示で使用したものを引き継ぐ。"] | BP r220-r246（イベントNo8） |  |  |  | ["検索条件の値を SQL 文字列へ直接連結している（search は bind パラメータ）。→ 06-review.yaml D-MK-02"] |  |
| initEdit | POST | /api/R60Maker/initEdit | マスタ項目画面（新規／複製／修正）の初期データを返す。 | R60MakerController.py:884-978 | {"params": {"mode": "str（'1'=新規、'2'=複製、'3'=修正）", "maker_cd": "str \| null（複製・修正では必須）"}} | {"error_code": "str", "data": "InitEditDetailData \| null（maker_cd, maker_nm, maker_anm, send_sts, send_kbn, del_flg, ksn_kbn, ksn_dat, rev_no, asd_stu_flg）"} | ["mode='1'：全項目を初期値で返す（コード・名称は空、SEND_STS='0'、DEL_FLG='0'、REV_NO=開始値）。", "mode='2'（複製）：元レコードを取得し、コード・名称・カナ名を引き継ぐ。緊急配信はオフ。", "mode='3'（修正）：元レコードの値（SEND_STS / DEL_FLG / KSN_* / REV_NO）を引き継ぐ。"] | BP r132-r218（イベントNo5/No6/No7） |  |  |  |  | '1'/'2'/'3' は実装の内部規約であり、設計書は「新規／複製／修正」としか書いていない。 設計から実装へ渡すときの変換表として記録する（06-review.yaml D-MK-12）。 |
| delete | POST | /api/R60Maker/delete | メーカーマスタを論理削除する。 | R60MakerController.py:984-1102 | {"params": {"maker_cd": "str", "maker_nm": "str \| null", "maker_anm": "str \| null", "send_sts": "str \| null", "ksn_dat": "str（排他比較用）", "rev_no": "str", "stf_id": "str（緊急配信の起票者）"}} | {"error_code": "str", "error_id": "str \| null（R60E0025 / R60W0024 / R60W0006）", "msg": "実装では未設定。設計は完了時に R60I0002 を表示する（BP r318-r319）"} | ["購入品目別仕入先マスタ（区分 '1'）と原材料仕入単価マスタ（区分 '2'）の被参照チェックを行う。", "KSN_DAT の排他チェックを行い、不一致かつ更新区分='1'（オンライン）なら R60W0006。", "DEL_FLG='1' で更新する。SEND_STS は更新前が '9' なら維持、それ以外は '0'。", "画面初期表示時に緊急配信が選択されていた場合、緊急配信を起動する。"] | BP r265-r327（イベントNo11） |  |  |  |  |  |
| edit | POST | /api/R60Maker/edit | メーカーマスタを新規登録・複製登録・更新する。mode で分岐する。 | R60MakerController.py:1103-1337 | {"params": {"mode": "str（'1'=新規、'2'=複製、'3'=修正）", "maker_cd": "str", "maker_nm": "str \| null", "maker_anm": "str \| null", "send_sts": "str \| null", "del_flg": "str（修正時。'1'=削除選択）", "ksn_dat": "str（修正時の排他比較用）", "rev_no": "str", "stf_id": "str"}} | {"error_code": "str", "error_id": "str \| null（R60W0014 / R60E0025 / R60W0024 / R60W0006）", "msg": "実装では未設定。設計は完了時に R60I0001 を表示する（BP r399-r400）"} | ["mode='1'/'2'：キー重複チェック（R60W0014）→ INSERT → 緊急配信なら起動。", "mode='3'：削除選択時のみ被参照チェック（R60E0025 / R60W0024）→ 排他チェック（R60W0006）→ UPDATE。", "INSERT 時は DEL_FLG='0'、SEND_KBN='0'、ASD_STU_FLG='0'、REV_NO=開始値を固定で設定する。", "UPDATE 時は画面の DEL_FLG / SEND_STS を反映し、緊急配信なら起動する。"] | BP r329-r408（イベントNo12） |  |  |  |  |  |

## endpoint_to_event_mapping

| event_no | event | endpoint | params |
|---|---|---|---|
| 1 | 初期表示 | /init | {} |
| 2 | 表示ボタンクリック | /search | btn='1' |
| 3 | 仕掛表示ボタンクリック | /search | btn='0'（REG_STS='0' を追加） |
| 4 | 検索条件(非)表示 |  | フロントのみ（BP r130『共通処理参照』） |
| 5 | 複製ボタンクリック | /initEdit | mode='2' |
| 6 | 一覧データリンククリック | /initEdit | mode='3' |
| 7 | 新規ボタンクリック | /initEdit | mode='1' |
| 8 | ダウンロードボタンクリック | /download | 直前の検索条件・ソート順 |
| 9 | 戻るボタンクリック（一覧） |  | 検索条件入力状態へ戻る（BP r248-r256） |
| 10 | 業務終了ボタンクリック |  | 確認後、画面を閉じる（BP r258-r263） |
| 11 | 削除ボタンクリック | /delete | maker_cd, ksn_dat, rev_no, send_sts, stf_id |
| 12 | 登録ボタンクリック | /edit | mode='1'/'2'/'3' |
| 13 | 戻るボタンクリック（マスタ） |  | データ破棄チェック後、画面を閉じる（BP r410-r416） |

## notes

- API 呼び出し前にフロント側で単項目チェックと確認ダイアログを行う。バックエンドの error_id は項目間・DB 整合チェックが中心。
- オンライン利用可否チェックは全 6 端点の先頭で共通に行う（実装）。
- 設計のイベント No4 / No9 / No10 / No13 はサーバ処理を持たない。

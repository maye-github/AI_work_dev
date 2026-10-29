---
id: KNOW-LEGACY-R60-MODULE-R60PLC-API-VIEW
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-modules-r60plc-02-api
scope: project
project_id: P-R60-001
title: R60Plc — API 契約
doc_type: design-detail
conf_level: 30
updated_at: '2026-10-28'
---

# R60Plc — API 契約

> 正本は同ディレクトリの `02-api.yaml`。本ファイルは検索用の可読表現であり、
> 手で編集しない（`py -3 -m tools.kb_migrate --apply` で作り直す）。

| 項目 | 値 |
|---|---|
| id | KNOW-LEGACY-R60-MODULE-R60PLC-API |
| type | knowledge |
| status | draft |
| sensitivity | internal |
| owner | AI-SE |
| version | 0.1.0 |
| api_triggering_events | 13 |
| non_api_events | 11 |

## contract_conventions

| 項目 | 値 |
|---|---|
| transport | HTTP POST / JSON |
| base_path | /api/R60Plc |
| request_envelope | { params: {...} } |
| wire_case | camelCase |
| internal_case | snake_case |
| case_conversion | BaseCamelModel(alias_generator=to_camel, populate_by_name=True, serialize_by_alias=True, extra='ignore') |
| online_gate | 全 6 端点の先頭で r60util.chk_onl_flg()。NG は OnlineException |
| note | extra='ignore' は骨架規則（03-design-coding.md §2 の extra='forbid'）と異なる。 実装の事実として記録し、骨架規則は変更しない（D-PL-11）。 |

## endpoint_inventory

| 項目 | 値 |
|---|---|
| observed | 6 |
| service_methods | 6 |
| survey_score_note | reports/module-survey/scores/R60Plc.yaml の complexity.signals.endpoints は 11 と記録するが、 @router.post と Service のメソッドはいずれも 6 件である。24 イベントのうち API を呼ぶものは 13 件、呼ばないものが 11 件であり、11 は後者に一致する。 調査票の数え方は未確認。本カードは実測 6 件を採る（D-PL-02）。 |

### names

- init
- search
- download
- initEdit
- delete
- edit


## req_ids

## endpoints

| name | method | path | purpose | handler | request | response | message_ids | note | source_locator | behavior | sorting | risk_notes | mismatch |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| init | POST | /api/R60Plc/init | 一覧画面の初期表示。メッセージと 5 つの検索条件ドロップダウン、頁件数を返す。 | R60PlcController.py:1552-1803 | {"params": {}} | {"error_code": "str", "message_info": "dict[message_id, message_text]（20 件）", "cmp_list": "list[{value:CMP_CD, label:CMP_NM}]（会社マスタ×エリアマスタ、双方 DEL_FLG=0、CMP_CD 昇順）", "jig_list": "list[{value:'CMP_CD,JIG_CD', label:JIG_NM}]（事業場×エリア、双方 DEL_FLG=0、HYJ_SEQ NOT NULL、HYJ_SEQ・値昇順）", "area_list": "list[{value:'CMP_CD,JIG_CD,ARA_CD', label:ARA_NM}]（エリアマスタ DEL_FLG=0 かつ REG_STS=1、ARA_CD 昇順）", "plc_grp_list": "list[{value:'CMP,JIG,GRP', label:PLC_GRP_RNM}]（DEL_FLG=0・REG_STS=1、HYJ_SEQ 昇順）", "plc_typ_list": "list[{value:PLC_TYP_CD, label:PLC_TYP_NM}]（DEL_FLG=0・REG_STS=1、HYJ_SEQ 昇順）", "page_list": "list[{value:KOB_KMK_NM_1, label:CD_CHI_NM}]（情報ID 000000174、HYJ_SEQ・KEY_ID 昇順）", "default_page": "str \| null（情報ID 000000174、KOB_KMK_NM_10='D'）"} | ["R60W0128", "R60W0131", "R60W0121", "R60W0005", "R60A0008", "R60W0009", "R60W0006", "R60W0007", "R60I0001", "R60A0003", "R60W0010", "R60A0004", "R60W0014", "R60W0016", "R60W0015", "R60W0013", "R60W0024", "R60E0025", "R60I0002", "R60A0041"] | R60W0013 は本画面の設計シートにもフロント／バックエンドにも使用箇所が無い（D-PL-12）。 R60I0002 はフロントが表示しない（delete の応答としてバックエンドが返すが、画面は R60I0001 を出す）。 | BP r23-r45 |  |  |  |  |
| search | POST | /api/R60Plc/search | 仕掛表示／表示ボタンとページ移動・ソートで一覧を返す。 | R60PlcController.py:1804-1980 | {"params": {"cmp_cd": "str \| null（完全一致）", "jig_cd": "str \| null（'CMP_CD,JIG_CD'。実装は 2 番目を使う）", "ara_cd": "str \| null（'CMP,JIG,ARA'。実装は 3 番目を使う）", "plc_cd": "str \| null（前方一致。LIKE エスケープあり）", "plc_nm": "str \| null（中間一致）", "plc_grp_cd": "str \| null（'CMP,JIG,GRP'。3 番目）", "plc_typ_cd": "str \| null（完全一致）", "search_btn": "str（0=仕掛表示, 1=表示）", "del_flg_include": "str（0=削除を除く, 1=削除を含む）", "current_page": "int", "page_limit": "str", "sort_field": "str \| null（CMP_CD / JIG_CD / PLC_CD のみ許可）", "sort_order": "int \| null（1=昇順, -1=降順）"}} | {"error_code": "str", "error_id": "str \| null（R60W0010 / R60W0005）", "total": "int", "max_count": "str \| null（上限超過時）", "data": "list（31 表示項目＋cmp_cd/jig_cd）"} |  |  | BP r71-r127（イベント No5/No6） | ["検索条件は設計どおり。削除を含む＝未チェックの時だけ DEL_FLG=0 を加える。", "仕掛表示（search_btn='0'）の時だけ REG_STS=0 を加える。", "表示（search_btn='1'）の時は REG_STS を絞らない。設計は『確定のみ表示』と書くが、実装は未確定も返す（D-PL-07）。", "件数 0 → R60W0010、上限超過 → R60W0005。上限値は情報ID 000000024。"] | {"allowed_fields": ["CMP_CD", "JIG_CD", "PLC_CD"], "requested_sort": "ORDER BY DEL_FLG, {field} {ASC\|DESC}, ROWID", "default_sort": "ORDER BY DEL_FLG, CMP_CD, JIG_CD, PLC_CD, ROWID", "design_locator": "BP r107-r112（DEL_FLG・CMP_CD・JIG_CD・PLC_CD 昇順）", "note": "指定ソート時は副キーが落ちる（D-PL-10）"} |  |  |
| download | POST | /api/R60Plc/download | 直前の検索条件・ソート順で CSV を返す。 | R60PlcController.py:1981-2052 | {"params": "search と同じ（current_page / page_limit を除く）"} | {"content_type": "text/csv（添付ファイル）", "filename": "R60CsvUtil.get_csv_name(dbapi_conn, 'R60_PLC_M_TBL')"} |  |  | BP r193-r217 | ["CSV ヘッダは R60_GET_SELECT_COLUMN_FNC('R60_PLC_M_TBL','H')、データは同 'D'。", "設計のファイル名は情報ID 000000099 経由。実装は共通 CSV ユーティリティに委譲する。"] |  | ["WHERE 句を文字列連結で組み立てる（search は bind）。→ D-PL-09"] |  |
| initEdit | POST | /api/R60Plc/initEdit | マスタ項目モーダル（新規・複製・修正）の初期化。17 個のドロップダウンを返す。 | R60PlcController.py:2053-2602 | {"params": {"mode": "str（1=新規, 2=複製, 3=修正）", "cmp_cd": "str \| null", "jig_cd": "str \| null", "plc_cd": "str \| null"}} | {"error_code": "str", "init_data": "mode 2/3: 選択行の表示値＋コード値＋ksn_dat＋rev_no＋del_flg。 mode 1: 情報ID 295/296/297/299/300/301/302/303/420 の初期値のみ。", "*_list": "plc_zks_kbn_list(119), fifo_kbn_list(117), ato_zan_knr_flg_list(158), rry_knr_flg_list(159), kshak_knr_kbn_list(123), kshak_knte_kbn_list(124), kshak_tni_list(125), kaso_tnk_kbn_list(121), kaso_silo_kbn_list(120), huks_hmk_son_flg_list(127), uki_hmk_kkn_flg_list(126), bef_zik_kyoy_flg_list(118), gka_uki_flg_list(157), alc_zik_knr_flg_list(160), hjo_zry_tny_kno_flg_list(418), hyj_seq_kbn_list(419)"} |  | 設計はモード 1/2/3 の 3 画面を別々に書くが、実装は 1 つのモーダルと 1 つの initEdit で モードを切り替える。R60PlcCreate.vue / R60PlcCopy.vue は参照されていない残骸（D-PL-16）。 | BP r129-r191 |  |  |  |  |
| delete | POST | /api/R60Plc/delete | 論理削除。DEL_FLG=1 にする UPDATE。 | R60PlcController.py:2603-2757 | {"params": "業務キー 3 項目＋全更新項目＋ksn_stf_id / ksn_dat / rev_no"} | {"error_code": "str", "error_id": "R60W0006 / R60W0024 / R60E0025 / R60I0002"} |  |  | BP r260-r425 | ["排他：KSN_KBN='1' かつ KSN_DAT 不一致なら R60W0006。", "被参照：R60_CHECK_PLC_INFO_FNC が '1' なら R60W0024、null なら R60E0025。", "REG_STS を再判定し、DEL_FLG=1、SEND_STS=0、KSN_KBN=1、REV_NO+1 で UPDATE。", "成功時は error_id=R60I0002 を返す。"] |  |  | フロントは delete の成功応答を無視して R60I0001（登録しました。）を表示する（D-PL-07）。 |
| edit | POST | /api/R60Plc/edit | 新規・複製の INSERT、修正の UPDATE。 | R60PlcController.py:2758-3012 | {"params": {"mode": "str（1=新規, 2=複製, 3=修正）", "（以下 41 列に対応する値＋ksn_stf_id / ksn_dat / rev_no / del_flg）": "-"}} | {"error_code": "str", "error_id": "R60W0014 / R60W0006 / R60W0024 / R60E0025 / R60I0001"} |  |  | BP r316-r425 | ["mode 1/2：同一キー存在で R60W0014。INSERT は 41 列。SEND_KBN=0、REV_NO=開始値。", "mode 3：排他チェック。del_flg=1 で登録した場合は被参照チェック（削除と同じ）。", "mode 3：UPDATE は 33 列（項目移送表の更新 ○ と一致）。", "REG_STS は set_reg_sts() が 18 項目＋タンク時 6 項目で判定する。"] |  |  |  |

## event_to_endpoint_map

| event_no | name | endpoint | api | note |
|---|---|---|---|---|
| 1 | 初期表示 | init | True |  |
| 2 | 会社ドロップダウン変更 |  | False |  |
| 3 | 事業場ドロップダウン変更 |  | False |  |
| 4 | ロケーションコード検索 |  | False | R60PlcSup 画面 |
| 5 | 仕掛表示ボタン | search | True |  |
| 6 | 表示ボタン | search | True |  |
| 7 | 検索条件(非)表示 |  | False |  |
| 8 | ページ移動 | search | True |  |
| 9 | ソート：会社 | search | True |  |
| 10 | ソート：事業場 | search | True |  |
| 11 | ソート：ロケーションコード | search | True |  |
| 12 | 複製ボタン | initEdit | True |  |
| 13 | 一覧データリンク | initEdit | True |  |
| 14 | 戻る |  | False |  |
| 15 | 業務終了 |  | False |  |
| 16 | ダウンロード | download | True |  |
| 17 | 新規ボタン | initEdit | True |  |
| 18 | 会社変更（マスタ項目） |  | False |  |
| 19 | 事業場変更（マスタ項目） |  | False |  |
| 20 | ロケ属性変更 |  | False |  |
| 21 | ロケーション名称焦点喪失 |  | False |  |
| 22 | 戻る（マスタ項目） |  | False |  |
| 23 | 削除ボタン | delete | True |  |
| 24 | 登録ボタン | edit | True |  |

## open_points

- 表示（search_btn='1'）が REG_STS=1 で絞らない。設計の『確定のみ表示』と実装が食い違う。
- download のファイル名取得が設計（情報ID 000000099 指定）と実装（共通ユーティリティ）で異なる。
- delete の完了メッセージが設計 R60I0002、実装表示 R60I0001。

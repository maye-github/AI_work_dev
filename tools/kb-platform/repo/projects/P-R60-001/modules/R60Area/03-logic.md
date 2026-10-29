---
id: KNOW-LEGACY-R60-MODULE-R60AREA-LOGIC-VIEW
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-modules-r60area-03-logic
scope: project
project_id: P-R60-001
title: R60Area — 業務ロジック
doc_type: design-detail
conf_level: 30
updated_at: '2026-10-28'
---

# R60Area — 業務ロジック

> 正本は同ディレクトリの `03-logic.yaml`。本ファイルは検索用の可読表現であり、
> 手で編集しない（`py -3 -m tools.kb_migrate --apply` で作り直す）。

| 項目 | 値 |
|---|---|
| id | KNOW-LEGACY-R60-MODULE-R60AREA-LOGIC |
| type | knowledge |
| status | draft |
| sensitivity | internal |
| owner | AI-SE |
| version | 0.1.0 |

## req_ids

## common_preconditions

- セッション情報が存在すること（不在時はセッションエラー画面）
- オンライン利用可否フラグが有効であること（R60 onl_flg。NG はオンライン制御エラー画面）

## logic_cards

| logic_key | name | design_locator | implementation_locator | inputs | steps | outputs | notes | max_count_source | allowed_sort_fields | default_order | modes | rules | order | rule | fields | distinction | call_timing | targets | condition | action | call_sites |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AR-LOGIC-01 | 初期表示 | 14_業務処理説明 r23-r43（イベントNo1） | R60AreaController.py:1235-1428 | ["セッション（所属会社コード、組織コード、社員コード）"] | ["ユーザ情報を取得する（標準仕様）。", "権限情報を取得する（標準仕様）。", "画面タイトル背景色を設定する（標準仕様）。", "R60_GET_MESSAGE_FNC で使用メッセージを取得する。", "検索条件部の画面項目オブジェクトを生成する。"] | ["cmp_data", "jig_data", "page_list", "page_default", "message_info"] |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| AR-LOGIC-02 | 検索条件の生成 | 14_業務処理説明 r53-r75（イベントNo3/No4） | R60AreaController.py:1441-1473 | ["cmp_cd", "jig_cd", "ara_cd", "btn", "is_deleted"] | ["cmp_cd が非空なら CMP_CD = :CMP_CD を追加する。", "jig_cd が非空なら JIG_CD = :JIG_CD を追加する。'CMP_CD,JIG_CD' 形式のときは後半を使う。", "ara_cd が非空なら ARA_CD LIKE :ARA_CD ESCAPE '\\' を追加する（値は ara_cd + '%'）。", "btn='0'（仕掛表示）なら REG_STS = '0' を追加する。", "is_deleted='0' なら DEL_FLG = '0' を追加する。"] | ["where_clause", "bind_params"] | ["SQL は text() + bind パラメータ。値の文字列連結は行わない（search のみ）。"] |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| AR-LOGIC-03 | 件数取得と上限判定 | 14_業務処理説明 r69-r75 / 10_画面項目間・DB整合チェック r14-r15 | R60AreaController.py:1475-1498 |  | ["SELECT COUNT(CMP_CD) FROM R60_AREA_M_TBL WHERE {where} を実行する。", "0 件なら R60W0010 を返し、明細部を非表示にする。", "上限件数を超えたら R60W0005 を返し、上限値と HIT 件数を返す。"] | ["total_count", "error_id"] |  | コード値マスタ(明細) 情報ID='000000024' |  |  |  |  |  |  |  |  |  |  |  |  |  |
| AR-LOGIC-04 | ソート順 | 14_業務処理説明 r83-r89 / 単体テスト仕様 4-2-5・4-3-5 | R60AreaController.py:1516-1538 |  | ["sort_field が ALLOWED_SORT_FIELDS に一致する場合のみ、その列で ASC/DESC する。", "sort_order=1 を昇順、それ以外を降順とする。", "一致しない場合・未指定の場合は既定ソートへフォールバックする。", "いずれの場合も末尾に ROWID を付けて順序を一意化する。"] |  | ["设计書のソート順は「論理削除フラグ→会社コード→事業場表示順→事業場コード」。実装はこの順序に一致する。", "骨架规则 03 §5 の既定ソート例（JIG_HYJ_SEQ）とは列名が異なる。→ 06-review.yaml D-AR-06"] |  | ["CMP_CD", "JIG_CD", "ARA_CD"] | DEL_FLG ASC, CMP_CD ASC, TO_NUMBER(R60_Get_Jig_Information_FNC(CMP_CD, JIG_CD, '3')) ASC, JIG_CD ASC, ROWID |  |  |  |  |  |  |  |  |  |  |  |
| AR-LOGIC-05 | ページング | 14_業務処理説明 r91-r94（標準仕様参照） | R60AreaController.py:1499-1647 |  | ["page_limit は既定 10。current_page は 1 起算。", "総ページ数を ceil(total / page_limit) で求める。", "current_page が範囲外なら 1 または最終頁へ補正する。", "OFFSET {offset} ROWS FETCH FIRST {page_limit} ROWS ONLY で取得する。"] |  | ["骨架规则 00 §5 は ROWID 方式を原則とするが、実装は OFFSET/FETCH + 末尾 ROWID。→ 06-review.yaml D-AR-06"] |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| AR-LOGIC-06 | マスタ項目画面の初期化 | 14_業務処理説明 r106-r187（イベントNo6/No7/No11） | R60AreaController.py:1713-1991 |  | ["mode='1' のときコード値マスタ(明細) 情報ID 000000315〜000000320 から初期値を取得する。", "mode in ('1','2') のとき会社・事業場リストを生成する。", "受払場所・費用計上部署・自動払出承認フラグ・集中購買会社リストを生成する。", "mode='3' のとき対象行を取得して data に設定する。"] | ["ドロップダウンリスト", "初期値", "明細データ"] |  |  |  |  | {"1": "新規", "2": "複製", "3": "修正"} |  |  |  |  |  |  |  |  |  |  |
| AR-LOGIC-07 | ドロップダウン連動 | 14_業務処理説明 r218-r368 / 16_業務処理補足説明 | Front-end/src/components/R60AreaCreate.vue / R60AreaEdit.vue / R60AreaCopy.vue |  |  |  | ["「ロケーション選択時フラグ」は補足説明シートのケース 1〜4 で挙動が定義される。", "集中購買系の初期値はコード値マスタ(明細) 情報ID 000000316〜000000320。"] |  |  |  |  | ["会社変更 → 事業場・受払場所・各計上部署リストを再作成する。", "事業場変更 → 受払場所リストを再作成する。", "受払計上事業場変更 → 受払計上部署リストを再作成し、ロケーション選択時フラグを OFF にする。", "債務計上事業場変更 → 債務計上部署リストを再作成し、ロケーション選択時フラグを OFF にする。", "債権計上事業場変更 → 債権計上部署リストを再作成し、ロケーション選択時フラグを OFF にする。", "集中購買会社変更 → 集中購買事業場・各集中購買計上事業場・各集中購買計上部署リストを再作成する。"] |  |  |  |  |  |  |  |  |  |
| AR-LOGIC-08 | エリア名フォーカス喪失時のコピー | 14_業務処理説明 r258-r264（イベントNo14） | R60AreaCreate.vue / R60AreaEdit.vue / R60AreaCopy.vue |  | ["エリア略称が未設定なら、エリア名の先頭 16 バイトを設定する。", "支払案内書に表示する届先名が未設定なら、エリア名を設定する。"] |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| AR-LOGIC-09 | 登録・削除の入力チェック順序 | 14_業務処理説明 r370-r466（イベントNo25/No26） | R60AreaController.py:2324-2825 |  |  |  | ["手順 9（R60A0039 / R60A0040）は実装でコメントアウトされている。→ 06-review.yaml D-AR-02"] |  |  |  |  |  | ["1. 全項目変更なし → R60W0016（登録ボタンのみ）", "2. 新規・複製：会社・事業場・エリアコード必須 → R60W0009", "3. 新規・複製：エリアコード半角英数字 7 文字以内 → R60W0103", "4. 緊急配信チェック ON：13 項目必須 → R60W0012", "5. 緊急配信チェック OFF：13 項目必須 → R60W0015", "6. モード共通：エリア名 30Byte / エリア略称 16Byte → R60W0131", "7. モード共通：届先名 全角 25 文字 → R60W0118", "8. モード共通：ロケーション 半角英数大文字＋記号 8 文字 → R60W0128", "9. 計上事業場 ≠ 事業場 の確認 → R60A0039（登録）/ R60A0040（削除）", "10. 新規・複製：重複キー → R60W0014", "11. 修正：排他 → R60W0006", "12. 共通：ロケーション未登録 → R60W0033", "13. 削除：被参照 → R60W0024 / R60E0025", "14. 登録確認 → R60A0003 / 削除確認 → R60A0004"] |  |  |  |  |  |  |  |  |
| AR-LOGIC-10 | 登録ステータス判定 | 14_業務処理説明 r488-r505（手順12） | R60AreaController.py:2820-2843 set_reg_sts_area |  |  |  |  |  |  |  |  |  |  | 次の 16 項目すべてに値がある場合 REG_STS='1'（確定）、それ以外は '0'（未確定）。 | ["CMP_CD", "JIG_CD", "ARA_CD", "ARA_NM", "ARA_RNM", "UKH_PLC_CD", "UKH_KEIJ_JIG_CD", "UKH_KEIJ_BSY_CD", "SAIM_KEIJ_JIG_CD", "SAIM_KEIJ_BSY_CD", "SAIKN_KEIJ_JIG_CD", "SAIKN_KEIJ_BSY_CD", "JID_HAR_SYN_FLG", "SHR_ANSY_TDK_NM", "IDO_DFLT_PLC_CD_GZR", "IDO_DFLT_PLC_CD_HSH"] | ["緊急配信チェックの必須 13 項目は、上記からキー 3 項目（CMP_CD/JIG_CD/ARA_CD）を除いたもの。", "REG_STS は 16 項目、R60W0012 は 13 項目。混同しないこと。"] |  |  |  |  |  |
| AR-LOGIC-11 | 排他制御 | 10_画面項目間・DB整合チェック r34 | R60AreaController.py:2845-2873 haita_check_area |  |  |  | ["バッチ更新（KSN_KBN がオンライン以外）は不一致でも許可する。"] |  |  |  |  |  |  | R60_AREA_M_TBL から KSN_KBN と KSN_DAT を取得し、画面の ksn_dat と不一致、かつ KSN_KBN がオンライン更新の場合に R60W0006。 |  |  |  |  |  |  |  |
| AR-LOGIC-12 | 被参照チェック | 10_画面項目間・DB整合チェック r32-r33 | R60AreaController.py:2133-2153 / 2694-2705 |  |  |  |  |  |  |  |  |  |  | R60_Check_Area_Info_FNC(CMP_CD, JIG_CD, ARA_CD) を呼ぶ。戻り値 null → R60E0025、'1' → R60W0024。 |  |  | ["削除ボタン押下時（必ず）", "修正モードで DEL_FLG='1' にする場合（更新前）"] |  |  |  |  |
| AR-LOGIC-13 | ロケーション存在チェック | 10_画面項目間・DB整合チェック r30-r31 | R60AreaController.py:2875-2895 plc_exist_check |  |  |  |  |  |  |  |  |  |  | R60_PLC_M_TBL を CMP_CD・JIG_CD・PLC_CD で検索し、REG_STS='1' かつ DEL_FLG='0' の行が無ければ R60W0033。 |  |  |  | ["IDO_DFLT_PLC_CD_GZR", "IDO_DFLT_PLC_CD_HSH"] |  |  |  |
| AR-LOGIC-14 | 緊急配信 | 14_業務処理説明 r521-r525（手順18） | R60AreaController.py:2898-2912 emergency_send_area |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | SEND_STS='9' | R60_EMERGENCY_SEND_CTL_PKG を (テーブルID='R60_AREA_M_TBL', ログインユーザID, プログラムID='R60Area') で呼ぶ。 | ["新規・複製の登録後（R60AreaController.py:2607）", "修正の更新後（R60AreaController.py:2811）", "削除後（R60AreaController.py:2316）"] |
| AR-LOGIC-15 | 論理削除 | 14_業務処理説明 r516-r517（手順16） | R60AreaController.py:2033-2322 delete |  |  |  | ["削除後も検索条件「削除含む」で参照できる。"] |  |  |  |  |  |  | UPDATE で DEL_FLG='1'、SEND_STS、KSN_*、REV_NO+1 を設定する。物理削除は行わない。 |  |  |  |  |  |  |  |
| AR-LOGIC-16 | CSV ダウンロード | 14_業務処理説明 r191-r215（イベントNo16） | R60AreaController.py:1650-1711 download |  | ["R60_GET_CODE_CHI_MEISAI_FNC('000000099', 'R60_AREA_M_TBL', '1') でファイル名を取得する。", "R60_GET_SELECT_COLUMN_FNC('R60_AREA_M_TBL', 'H') でヘッダを取得する。", "R60_GET_SELECT_COLUMN_FNC('R60_AREA_M_TBL', 'D') でデータ項目を取得する。", "表示・仕掛表示で使用した検索条件とソート順でデータを取得する。", "R60CsvUtil で CSV を生成し、添付ファイルとして返す。"] |  | ["実装は検索条件を SQL 文字列へ直接連結している。→ 06-review.yaml D-AR-05"] |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

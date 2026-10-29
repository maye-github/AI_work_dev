---
id: KNOW-LEGACY-R60-MODULE-R60MAKER-LOGIC-VIEW
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-modules-r60maker-03-logic
scope: project
project_id: P-R60-001
title: R60Maker — 業務ロジック
doc_type: design-detail
conf_level: 30
updated_at: '2026-10-29'
---

# R60Maker — 業務ロジック

> 正本は同ディレクトリの `03-logic.yaml`。本ファイルは検索用の可読表現であり、
> 手で編集しない（`py -3 -m tools.kb_migrate --apply` で作り直す）。

| 項目 | 値 |
|---|---|
| id | KNOW-LEGACY-R60-MODULE-R60MAKER-LOGIC |
| type | knowledge |
| status | open |
| sensitivity | internal |
| owner | AI-SE |
| version | 0.1.0 |

## req_ids

## common_preconditions

- セッション情報が存在すること（不在時はセッションエラー画面）。BP r13-r16
- オンライン利用可否フラグが有効であること（NG はオンライン制御エラー画面）。BP r18-r20

## logic_cards

| logic_key | name | design_locator | implementation_locator | inputs | steps | outputs | notes | max_count_source |
|---|---|---|---|---|---|---|---|---|
| MK-LOGIC-01 | 初期表示 | BP r22-r48（イベントNo1） | R60MakerController.py:561-669 | ["セッション（所属会社コード、組織コード、社員コード）"] | ["呼び出し元から所属会社コード・組織コード・社員コードを引き継ぐ（BP r24-r27）。", "ユーザ情報を取得する（標準仕様）。", "権限情報を取得する（標準仕様。条件は本設計書に無い）。", "画面タイトル背景色を設定する（標準仕様）。", "R60_GET_MESSAGE_FNC で使用メッセージ 19 件を取得する。", "1頁件数リストを R60_CODE_MES_M_TBL（情報ID='000000488'）から作る。初期値は個別項目名10='D'。", "検索条件は空、削除含むはチェックオフで初期化する（BP r44-r48）。"] | ["page_list", "page_default", "message_info"] |  |  |
| MK-LOGIC-02 | 検索条件の生成（表示） | BP r52-r75（イベントNo2） | R60MakerController.py:688-717 | ["maker_cd", "maker_nm", "is_deleted"] | ["maker_cd が非空なら MAKER_CD LIKE :MAKER_CD を追加する（値は maker_cd + '%'）。", "maker_nm が非空なら MAKER_NM LIKE :MAKER_NM ESCAPE '\\' を追加する（値は '%' + エスケープ + '%'）。", "is_deleted='0' なら DEL_FLG = '0' を追加する。'1' なら条件に含めない。", "条件は AND で結合する。未指定項目は含めない（BP r59）。", "並び順は DEL_FLG 昇順＋MAKER_CD 昇順（BP r63）。"] | ["where_clause", "bind_params"] | ["search は bind パラメータ。値の文字列連結は行わない。"] |  |
| MK-LOGIC-03 | 検索条件の生成（仕掛表示） | BP r89-r119（イベントNo3） | R60MakerController.py:713-717 | ["maker_cd", "maker_nm", "is_deleted"] | ["MK-LOGIC-02 と同じ条件を作る。", "btn='0' のとき REG_STS = '0'（未確定）を追加する。", "btn='1'（表示）のとき REG_STS 条件を追加しない。"] | ["where_clause", "bind_params"] | ["btn の値は実装規約（'0'=仕掛表示、'1'=表示）。設計書はボタン名称で書いている。"] |  |
| MK-LOGIC-04 | 件数チェックと上限判定 | BP r65-r71 / r104-r110、画面項目間・DB整合チェック r14-r15 | R60MakerController.py:719-750 |  | ["検索条件（並び順を除く）で COUNT(ROWID) を実行する。", "0 件なら R60W0010 を返し、一覧を表示しない。", "上限件数を超えたら R60W0005 を返し、上限値と HIT 件数を返す。"] | ["total", "error_id", "max_count"] | ["設計書のメッセージ例は上限 3000 件だが、実装はコード値マスタから取得する（BP r68『共通仕様参照』）。"] | コード値マスタ(明細) 情報ID='000000024' |
| MK-LOGIC-05 | 一覧表示とボタン活性 | BP r78-r87（表示）/ r121-r126（仕掛表示） | Front-end/src/views/R60Maker.vue |  | ["検索結果を一覧に表示する。列はコード・日本語名・カナ名・削除。", "検索成功後、戻る・ダウンロード・新規を活性化する（BP r85-r87）。", "0 件表示時の活性制御は初期化と同じ（BP r83 注記）。"] | ["search_result_rows", "button_state"] | ["一覧の送信ステータス表示（No23）の位置づけは 01-fields.yaml を参照。"] |  |
| MK-LOGIC-06 | 複製モードの初期化 | BP r132-r166（イベントNo5） | R60MakerController.py:884-978（mode='2'） | ["選択行の maker_cd"] | ["元レコードを取得する。", "メーカーコード・日本語名・カナ名を引き継ぐ（BP r156-r158）。", "緊急配信はチェックオフ、削除は無（BP r159-r160）。", "戻る＝活性、削除＝非活性、登録＝活性（BP r164-r166）。"] | ["InitEditDetailData"] | ["実装は複製時に DB 原値の DEL_FLG / SEND_KBN / KSN_* を返すが、INSERT 時に DEL_FLG='0'・SEND_KBN='0' を固定設定するため登録結果は新規扱いになる。→ D-MK-06"] |  |
| MK-LOGIC-07 | 修正モードの初期化 | BP r168-r202（イベントNo6） | R60MakerController.py:884-978（mode='3'） | ["選択行の maker_cd"] | ["元レコードを取得する。", "コード・日本語名・カナ名・送信ステータス・論理削除フラグを画面に設定する（BP r192-r196）。", "削除ボタンは DEL_FLG='1' なら非活性（BP r201）。"] | ["InitEditDetailData"] |  |  |
| MK-LOGIC-08 | 新規モードの初期化 | BP r204-r218（イベントNo7） | R60MakerController.py:884-978（mode='1'） |  | ["コード・日本語名・カナ名は空、緊急配信はオフ、削除は無で表示する。", "戻る＝活性、削除＝非活性、登録＝活性。"] | ["InitEditDetailData"] |  |  |
| MK-LOGIC-09 | ダウンロード | BP r220-r246（イベントNo8） | R60MakerController.py:817-883 |  | ["CSV ファイル名を R60_GET_CODE_CHI_MEISAI_FNC('000000099', 'R60_MAKER_M_TBL', '1') で取得する。", "CSV ヘッダを R60_GET_SELECT_COLUMN_FNC(H)、データ項目を同(D) で取得する。", "直前の表示／仕掛表示で使った検索条件とソート順でデータを取得する。", "CSV を出力する。"] | ["csv_file"] | ["実装は検索条件を SQL 文字列へ直接連結している（search は bind）。→ D-MK-02"] |  |
| MK-LOGIC-10 | 削除 | BP r265-r327（イベントNo11） | R60MakerController.py:984-1097 / R60MakerEdit.vue:250-300 |  | ["緊急配信が選択されている場合、日本語名・カナ名の必須チェック（R60W0012）。未選択なら R60W0015。", "日本語名の形式チェック（R60W0131）、カナ名の形式チェック（R60W0113）。", "削除確認ダイアログ（R60A0004）。いいえなら中断。", "購入品目別仕入先マスタの被参照チェック（区分 '1'）。NULL は R60E0025、1 は R60W0024。", "原材料仕入単価マスタの被参照チェック（区分 '2'）。同じメッセージ。", "KSN_DAT の排他チェック。不一致かつ更新区分='1' なら R60W0006。", "DEL_FLG='1' で UPDATE する。REG_STS を再判定し、REV_NO を +1 する。", "画面初期表示時に緊急配信が選択されていた場合、緊急配信を起動する。", "完了メッセージ（R60I0002）を表示し、画面を閉じて一覧を再検索する。"] | ["delete_result"] | ["完了メッセージは実装のレスポンスには含まれず、フロント側で表示する（R60MakerEdit.vue:292）。"] |  |
| MK-LOGIC-11 | 登録・更新（新規／複製／修正） | BP r329-r408（イベントNo12） | R60MakerController.py:1103-1300 / R60MakerEdit.vue:370-560 |  | ["(新規・複製) メーカーコード必須チェック（R60W0009）→ 形式チェック（R60W0103）。", "緊急配信が選択されている場合、日本語名・カナ名の必須チェック（R60W0012）。", "(修正) 削除が選択されている場合、日本語名・カナ名の必須チェック（R60W0015）。", "日本語名の形式チェック（R60W0131）、カナ名の形式チェック（R60W0113）。", "(複製・修正) データ変更なしなら R60W0016。", "登録確認ダイアログ（R60A0003）。いいえなら中断。", "(新規・複製) キー重複チェック。存在すれば R60W0014。", "(修正・削除選択) 購入品目別仕入先（'1'）と原材料仕入単価（'2'）の被参照チェック。NULL は R60E0025、1 は R60W0024。", "(修正) KSN_DAT の排他チェック。不一致かつオンラインなら R60W0006。", "新規・複製は INSERT、修正は UPDATE。INSERT 時は DEL_FLG='0'、SEND_KBN='0'、REV_NO=開始値。", "緊急配信が選択されている場合、緊急配信を起動する。", "完了メッセージ（R60I0001）を表示し、画面を閉じて一覧を再検索する。"] | ["register_result"] | ["モード値は '1'=新規、'2'=複製、'3'=修正（実装規約）。", "完了メッセージは実装のレスポンスには含まれず、フロント側で表示する（R60MakerEdit.vue:354）。"] |  |
| MK-LOGIC-12 | 戻る（データ破棄確認） | BP r410-r416（イベントNo13） | Front-end/src/components/R60MakerEdit.vue |  | ["編集中（値変更あり）の場合、破棄確認（R60W0007）を表示する。", "いいえなら中断する。", "画面を閉じる。"] | ["close"] |  |  |
| MK-LOGIC-13 | 登録ステータス（REG_STS）の判定 | 項目移送表(DB) r19『共通仕様参照』（判定基準の本文は本設計書に無い） | R60MakerController.py:1311-1320 set_reg_sts |  | ["メーカーコード・日本語名・カナ名の 3 つがすべて非空なら REG_STS='1'（確定）。", "いずれかが空なら REG_STS='0'（未確定）。"] | ["reg_sts"] | ["設計書は判定基準を『共通仕様参照』としており、本設計書だけでは決まらない。実装値を記録する。→ D-MK-05"] |  |
| MK-LOGIC-14 | 緊急配信の起動 | BP r312-r316（削除）/ r393-r397（登録） | R60MakerController.py:1085-1093 / 1199-1207 / 1292-1300 |  | ["緊急配信チェックがオンの場合、R60_EMERGENCY_SEND_CTL_PKG を呼ぶ。", "パラメータは マスタファイル ID（'R60_MAKER_M_TBL'）、社員コード、アプリケーション ID（'R60Maker'）。", "削除時は『画面初期表示時の緊急配信』が対象である（BP r312）。"] | ["emergency_send_result"] | ["削除時の対象判定（初期表示時か現在値か）は設計記述が一意でない。実装は送信パラメータの send_sts で判定する。→ D-MK-08"] |  |

---
id: KNOW-LEGACY-R60-CHUNKS-R60MAKER
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-chunks-r60maker
scope: project
project_id: P-R60-001
title: R60Maker — 検索摘要（45 条）
doc_type: glossary
conf_level: 30
updated_at: '2026-10-29'
---

# R60Maker — 検索摘要（45 条）

> 各節は検索用に書かれた摘要であり、原文のスライスではない。
> 正本は `screens/` と `modules/` 側。

## R60Maker 画面概要・権限・使用頻度

`R60Maker:screen:overview` / `screen`
R60Maker はメーカーマスタメンテナンス画面。本画面はメーカー情報のメンテナンスを行う。前提条件は「あり」だが本文の記載がない。排他条件は「あり」で、画面項目間・DB整合チェックシート参照（KSN_DAT 比較）。利用対象者は利用権限保持者のみ。使用頻度は月次・随時。画面区分は参照・登録・更新・削除・DL。関連画面はセッションエラー、オンライン制御エラー、システムエラー。

## R60Maker / 検索画面の項目構成（33 項目）

`R60Maker:screen:search-items` / `screen`
検索画面は項目番号 1〜37、実項目 33 件。内訳はヘッダー5、検索条件7（メーカーコード・メーカー日本語名・削除含む・1頁件数・仕掛表示・表示・検索条件(非)表示）、ページャ5、行操作3（複製・送信・件数）、一覧4列（コード・日本語名・カナ名・削除）、下部ページャ5、ボタン4（戻る・業務終了・ダウンロード・新規）。メーカーコードは前方一致でワイルドカード入力不要、日本語名は中間一致。

## R60Maker / マスタ項目画面の項目構成（9 項目）

`R60Maker:screen:master-items` / `screen`
マスタ項目画面は項目番号 1〜12、実項目 9 件。操作モード、メーカーコード（新規・複製はテキストで必須、修正はラベル）、メーカー日本語名（30Byte）、メーカーカナ名（15 文字）、緊急配信チェック、削除チェック（新規・複製はラベル、修正のみチェック）、ボタン3（戻る・削除・登録）。削除ボタンは新規・複製で非活性、修正で活性、削除済みなら非活性。

## R60Maker / 廃止された入力画面シート（19 項目）

`R60Maker:screen:deprecated-input` / `screen`
設計書には『廃止_画面項目内容(入力)』シートが残っている。項目番号 19 件で、新規・修正・複製の 3 モード別に同じ 5 項目＋ボタン 3 を繰り返す構成。現行の入力画面仕様は『画面項目内容(マスタ項目)』（9 項目）が正であり、廃止シートを現行仕様として参照してはならない。

## R60Maker / イベント一覧（13 イベント）

`R60Maker:screen:events` / `screen`
イベントは 13 件。1 初期表示、2 表示ボタン、3 仕掛表示ボタン、4 検索条件(非)表示、5 複製ボタン、6 一覧データリンク、7 新規ボタン、8 ダウンロード、9 戻る（一覧）、10 業務終了、11 削除ボタン（マスタ）、12 登録ボタン（マスタ）、13 戻る（マスタ）。例外処理の記載があるのは No1 と No11 のみ。No4・No9・No10・No13 は標準仕様参照で本文がない。

## R60Maker / キー項目 MAKER_CD（メーカーコード）

`R60Maker:field:maker-cd` / `field`
MAKER_CD はメーカーコード、長さ 5、R60_MAKER_M_TBL の主キー。INSERT のみで UPDATE しない（項目移送表の更新欄が false）。新規・複製ではテキストボックスで必須、修正ではラベル表示。半角英数字 5 文字以内。検索では前方一致（値に % を付与）で使う。

## R60Maker / 項目 MAKER_NM（メーカー日本語名）

`R60Maker:field:maker-nm` / `field`
MAKER_NM はメーカー日本語名、長さ 30。INSERT・UPDATE・DELETE のすべてで移送する。全半角混在 30Byte 以内、禁止文字はカンマ・アポストロフィ・ダブルクォート・パイプ。検索では中間一致（LIKE の前後に % を付与し、ESCAPE でエスケープ）。緊急配信チェック ON のとき、または削除するときは必須。REG_STS の判定対象でもある。

## R60Maker / 項目 MAKER_ANM（メーカーカナ名）

`R60Maker:field:maker-anm` / `field`
MAKER_ANM はメーカーカナ名、長さ 15。INSERT・UPDATE・DELETE のすべてで移送する。半角文字・半角カタカナで 15 文字以内、禁止文字はカンマ。アポストロフィ・カンマ・円マーク・半角スペースは入力不可。緊急配信チェック ON のとき、または削除するときは必須。REG_STS の判定対象でもある。

## R60Maker / 項目 SEND_STS（送信ステータス／緊急配信）

`R60Maker:field:send-sts` / `field`
SEND_STS は送信ステータス、長さ 1。画面の緊急配信チェックに対応する。チェック ON で '9'（配信対象）、OFF で '0'。INSERT・UPDATE・DELETE で移送する。削除時は更新前が '9' なら維持し、それ以外は '0' にする。緊急配信 ON のときは名称 2 項目が必須になる。

## R60Maker / 項目 DEL_FLG（論理削除フラグ）

`R60Maker:field:del-flg` / `field`
DEL_FLG は論理削除フラグ、長さ 1。画面の削除チェックに対応する。チェック ON で '1'、OFF で '0'。INSERT・UPDATE・DELETE で移送する。新規・複製の INSERT では '0' 固定。削除ボタンでは '1' 固定。一覧の『削除』列はコード値明細マスタ 情報ID='000000063' で名称化する。

## R60Maker / 項目 REG_STS（登録ステータス）

`R60Maker:field:reg-sts` / `field`
REG_STS は登録ステータス、長さ 1。'1'＝確定、'0'＝未確定。仕掛表示ボタンは REG_STS='0' を検索条件に追加する。設計書の項目移送表は画面項目を『共通仕様参照』とだけ書き、判定基準の本文を持たない。実装の set_reg_sts は MAKER_CD・MAKER_NM・MAKER_ANM の 3 つがすべて非空なら '1'、それ以外は '0' と判定する。

## R60Maker / 監査項目 REG_* / KSN_* / REV_NO

`R60Maker:field:audit-columns` / `field`
登録系は REG_KBN・REG_STF_ID・REG_DAT・REG_PGM_ID で、INSERT のみ。更新系は KSN_KBN・KSN_STF_ID・KSN_DAT・KSN_PGM_ID で、INSERT・UPDATE・DELETE のすべてで更新する。REV_NO はリビジョン番号（長さ 5）で、更新・削除時に +1 する。排他制御は KSN_DAT の比較で行い、不一致かつオンライン更新区分なら R60W0006 を返す。

## R60Maker / R60_MAKER_M_TBL の 17 カラム

`R60Maker:field:table-columns` / `field`
R60_MAKER_M_TBL は 17 カラム。MAKER_CD / MAKER_NM / MAKER_ANM / ASD_STU_FLG / REG_STS / SEND_STS / SEND_KBN / DEL_FLG / REG_KBN / REG_STF_ID / REG_DAT / REG_PGM_ID / KSN_KBN / KSN_STF_ID / KSN_DAT / KSN_PGM_ID / REV_NO。INSERT 固定値は ASD_STU_FLG='0'、SEND_KBN='0'、DEL_FLG='0'。MAKER_CD は更新しない。主キーは MAKER_CD のみ。

## R60Maker / 被参照元マスタ（購入品目別仕入先・原材料仕入単価）

`R60Maker:field:referenced-masters` / `field`
R60Maker は被参照される側のマスタである。削除時と、修正で削除を選択したときに、購入品目別仕入先マスタ（区分 '1'）と原材料仕入単価マスタ（区分 '2'）から参照チェックを受ける。戻り値 NULL は R60E0025、'1'（参照あり）は R60W0024。本設計書には両マスタの移送表がなく、参照キーの実項目名は未確認。

## R60Maker / コード値明細マスタの情報 ID 一覧

`R60Maker:field:code-master-ids` / `field`
R60Maker が使うコード値明細マスタの情報 ID。1頁件数='000000488'（初期値は個別項目名10='D'）、送信ステータス表示='000000057'、論理削除表示='000000063'、検索上限件数='000000024'、CSV ファイル名='000000099'。

## R60Maker / API 共通規約（封筒・大小文字・extra）

`R60Maker:api:conventions` / `api`
R60Maker の API は HTTP POST / JSON。base_path は /api/R60Maker。要求は { params: {...} } の封筒形式。ワイヤは camelCase、内部は snake_case。BaseCamelModel は alias_generator=to_camel、populate_by_name=True、serialize_by_alias=True、extra='ignore'。extra='ignore' は骨架規則の extra='forbid' と異なる（実装の事実として記録）。全 6 端点の先頭で r60util.chk_onl_flg() を呼び、NG なら OnlineException。

## POST /api/R60Maker/init（一覧初期表示）

`R60Maker:api:init` / `api`
init は一覧画面の初期表示。ユーザ情報（セッション）と権限情報を取得し、R60_GET_MESSAGE_FNC で 19 件のメッセージを取得する。1頁件数リストは R60_CODE_MES_M_TBL を情報ID='000000488'・DEL_FLG='0' で絞り、HYJ_SEQ・KEY_ID 昇順で作る。初期値は個別項目名10='D' の行。応答は page_list、page_default、message_info。

## POST /api/R60Maker/search（表示／仕掛表示）

`R60Maker:api:search` / `api`
search はメーカーマスタをページングして返す。btn='1' は表示、btn='0' は仕掛表示で REG_STS='0' を追加する。maker_cd は前方一致（値に % を付与）、maker_nm は中間一致（前後に % を付与し ESCAPE で処理）。is_deleted='0' なら DEL_FLG='0' を追加する。条件は bind パラメータで組み立てる。0 件は R60W0010、上限超過は R60W0005（上限値と HIT 件数を返す）。応答は error_code / error_id / total / data / max_count。

## R60Maker / 検索のソートとページング

`R60Maker:api:search-sort-paging` / `api`
件数は COUNT(ROWID) で取得する。ページは ORDER BY {sort}, ROWID に OFFSET ... ROWS FETCH FIRST ... ROWS ONLY を付ける。許可ソート項目は MAKER_CD と MAKER_NM の 2 つだけ（ALLOWED_SORT_FIELDS）。要求ソートがあるときは ORDER BY DEL_FLG, {field} {ASC|DESC}, ROWID。未指定・不正時は ORDER BY DEL_FLG, MAKER_CD, ROWID にフォールバックする。設計書の既定順は DEL_FLG 昇順＋MAKER_CD 昇順。

## POST /api/R60Maker/download（CSV）

`R60Maker:api:download` / `api`
download は直前の表示／仕掛表示で使った検索条件とソート順で CSV を返す。ファイル名は R60_GET_CODE_CHI_MEISAI_FNC('000000099', 'R60_MAKER_M_TBL', '1') 相当（実装は R60CsvUtil.get_csv_name）。ヘッダとデータ項目は R60_GET_SELECT_COLUMN_FNC 相当（実装は r60get_select_column.execute）。検索条件の値を SQL 文字列へ直接連結している（search は bind）。セキュリティ上の差異として記録する。

## POST /api/R60Maker/initEdit（3 モード初期化）

`R60Maker:api:initEdit` / `api`
initEdit は mode で分岐する。mode='1' は新規（コード・名称は空、SEND_STS='0'、DEL_FLG='0'、REV_NO=開始値）、mode='2' は複製（元レコードのコード・日本語名・カナ名を引き継ぎ、緊急配信はオフ）、mode='3' は修正（元レコードの SEND_STS / DEL_FLG / KSN_* / REV_NO を引き継ぐ）。応答は error_code と data。モード値 '1'/'2'/'3' は設計書に無い実装規約である。

## POST /api/R60Maker/delete（論理削除）

`R60Maker:api:delete` / `api`
delete はメーカーマスタを論理削除する。購入品目別仕入先（区分 '1'）と原材料仕入単価（区分 '2'）の被参照を確認し、NULL は R60E0025、'1' は R60W0024 を返す。KSN_DAT の排他チェックで不一致かつ更新区分='1' なら R60W0006。DEL_FLG='1' で UPDATE し、REG_STS を再判定、REV_NO を +1 する。SEND_STS は更新前 '9' なら維持、それ以外は '0'。緊急配信が選択されていれば R60EmergencySendCtlBean を呼ぶ。応答は error_code と error_id のみで、完了メッセージはフロントが表示する。

## POST /api/R60Maker/edit（新規・複製・更新）

`R60Maker:api:edit` / `api`
edit は mode で分岐する。mode='1'（新規）と '2'（複製）はキー重複チェック（R60W0014）の後に INSERT する。INSERT 時は DEL_FLG='0'、SEND_KBN='0'、ASD_STU_FLG='0'、REV_NO=開始値を固定設定する。mode='3'（修正）は削除選択時だけ被参照チェック（R60E0025 / R60W0024）を行い、KSN_DAT の排他チェック（R60W0006）の後に UPDATE する。緊急配信が選択されていれば起動する。応答は error_code と error_id のみ。

## R60Maker / イベントとエンドポイントの対応

`R60Maker:api:event-mapping` / `api`
イベント対応。No1 初期表示→/init、No2 表示→/search(btn='1')、No3 仕掛表示→/search(btn='0')、No4 条件部トグル→フロントのみ、No5 複製→/initEdit(mode='2')、No6 一覧リンク→/initEdit(mode='3')、No7 新規→/initEdit(mode='1')、No8 ダウンロード→/download、No9 戻る（一覧）→フロントのみ、No10 業務終了→フロントのみ、No11 削除→/delete、No12 登録→/edit、No13 戻る（マスタ）→フロントのみ。

## R60Maker / 実装固有の値域（mode / btn / is_deleted / sort_order）

`R60Maker:api:mode-values` / `api`
設計書に現れない実装固有の値域。mode: '1'=新規、'2'=複製、'3'=修正。btn: '0'=仕掛表示（REG_STS='0' を追加）、'1'=表示。is_deleted: '0'=削除を含まない（DEL_FLG='0' を追加）、'1'=削除を含む。sort_order: 1=昇順、それ以外=降順。設計から実装へ渡すときの変換表として使う。

## R60Maker / 検索条件の組み立て

`R60Maker:logic:search-conditions` / `logic`
検索条件は AND で結合し、未指定項目は含めない。メーカーコードは前方一致、メーカー日本語名は中間一致。削除含むが OFF なら DEL_FLG='0'、ON なら条件を追加しない。仕掛表示では REG_STS='0' を追加し、表示では REG_STS 条件を追加しない。並び順は DEL_FLG 昇順＋MAKER_CD 昇順。

## R60Maker / 件数取得と上限判定

`R60Maker:logic:count-limit` / `logic`
検索条件（並び順を除く）で件数を取得する。0 件なら R60W0010 を表示して一覧を出さない。上限件数を超えたら R60W0005 を表示し、上限値と HIT 件数を返す。設計書のメッセージ例は上限 3000 件だが、実装はコード値明細マスタ 情報ID='000000024' から取得する。

## R60Maker / 複製モードの初期化

`R60Maker:logic:copy-mode` / `logic`
複製モードは選択行のデータを取得し、メーカーコード・日本語名・カナ名を引き継ぐ。緊急配信はチェックオフ、削除はブランク。戻る＝活性、削除＝非活性、登録＝活性。実装は元レコードの DEL_FLG と SEND_KBN も返すが、INSERT 時に DEL_FLG='0'・SEND_KBN='0' を固定するため、登録結果は新規扱いになる。

## R60Maker / 修正モードの初期化

`R60Maker:logic:edit-mode` / `logic`
修正モードは選択行のデータを取得し、コード・日本語名・カナ名・送信ステータス・論理削除フラグを画面に設定する。削除ボタンは DEL_FLG='1' なら非活性。緊急配信は SEND_STS='9' でチェックオン。修正ではメーカーコードはラベル表示で変更できない。

## R60Maker / 新規モードの初期化

`R60Maker:logic:new-mode` / `logic`
新規モードはコード・日本語名・カナ名を空、緊急配信をオフ、削除をブランクで表示する。戻る＝活性、削除＝非活性、登録＝活性。コードは必須で半角英数字 5 文字以内。

## R60Maker / 削除処理の順序

`R60Maker:logic:delete-sequence` / `logic`
削除の順序。1) 緊急配信 ON なら名称必須（R60W0012）、OFF なら名称必須（R60W0015）。2) 日本語名の形式（R60W0131）、カナ名の形式（R60W0113）。3) 削除確認（R60A0004）。4) 購入品目別仕入先の被参照（区分 '1'）で R60E0025 / R60W0024。5) 原材料仕入単価の被参照（区分 '2'）で同じメッセージ。6) 排他で R60W0006。7) DEL_FLG='1' で UPDATE、REG_STS 再判定、REV_NO +1。8) 緊急配信。9) R60I0002 を表示して画面を閉じる。

## R60Maker / 登録・更新処理の順序（3 モード）

`R60Maker:logic:register-sequence` / `logic`
新規・複製はメーカーコード必須（R60W0009）と形式（R60W0103）。緊急配信 ON なら名称必須（R60W0012）。修正で削除選択なら名称必須（R60W0015）。名称形式（R60W0131 / R60W0113）。複製・修正で変更なしなら R60W0016。登録確認（R60A0003）。新規・複製はキー重複（R60W0014）。修正で削除選択なら被参照（R60W0024 / R60E0025）。修正は排他（R60W0006）。INSERT または UPDATE の後に緊急配信、最後に R60I0001。

## R60Maker / REG_STS の判定規則（実装値）

`R60Maker:logic:reg-sts-rule` / `logic`
設計書は REG_STS の判定を『共通仕様参照』とだけ書き、本文を持たない。実装の set_reg_sts は MAKER_CD・MAKER_NM・MAKER_ANM の 3 つがすべて非空なら REG_STS='1'（確定）、いずれかが空なら '0'（未確定）と判定する。この規則は設計書からは導けないため、確定規則として扱わない。

## R60Maker / 緊急配信の起動

`R60Maker:logic:emergency-send` / `logic`
緊急配信チェックがオンのとき、R60_EMERGENCY_SEND_CTL_PKG を呼ぶ。パラメータはマスタファイル ID='R60_MAKER_M_TBL'、社員コード、アプリケーション ID='R60Maker'。削除時は『画面初期表示時に緊急配信が選択されていた場合』と書かれるが、画面状態か DB 値かは一意でない。実装はリクエストの send_sts で判定する。

## R60Maker / 戻る（データ破棄確認）

`R60Maker:logic:back-discard` / `logic`
マスタ画面で値変更があるまま戻るボタンを押すと、R60W0007『編集内容が未登録です。破棄して良いですか？』を表示する。いいえなら中断し、はいなら画面を閉じる。送信ステータスが変更前 '1:送信済み' の場合は判定から除外する。

## R60Maker / 単項目チェック 14 件

`R60Maker:error:single-item` / `error`
単項目チェックは 14 件。検索条件はメーカーコード（R60W0103、半角英数字 5 文字）とメーカー日本語名（R60W0131、30Byte・禁止文字）。マスタ項目はコード必須（R60W0009）と形式（R60W0103）、日本語名・カナ名の削除時必須（R60W0015）と緊急配信時必須（R60W0012）、日本語名形式（R60W0131）、カナ名形式（R60W0113）、戻る時の破棄確認（R60W0007）、変更なし（R60W0016）。

## R60Maker / 画面項目間・DB 整合チェック 9 件

`R60Maker:error:db-integrity` / `error`
項目間・DB 整合チェックは 9 件。0 件（R60W0010）、上限超過（R60W0005）、被参照チェックエラー（R60E0025）、更新日付比較差異（R60W0006）、メーカーコード重複（R60W0014）、購入品目別仕入先の参照あり（R60W0024）、原材料仕入単価の参照あり（R60W0024）。被参照チェックは削除時と登録時（修正で削除選択時）に行う。

## R60Maker / メッセージ一覧（19 件）

`R60Maker:error:messages` / `error`
使用メッセージは 19 件。内訳は W 13・A 3・I 2・E 1。確認は業務終了（R60A0008）、登録（R60A0003）、削除（R60A0004）。完了は登録（R60I0001）と削除（R60I0002）。異常は被参照チェックエラー（R60E0025）。警告は W0005 / W0006 / W0007 / W0009 / W0010 / W0012 / W0014 / W0015 / W0016 / W0024 / W0103 / W0113 / W0131。

## R60Maker / フロント側チェックとバックエンドの error_id の分担

`R60Maker:error:front-vs-back` / `error`
単項目チェックと確認・完了メッセージはフロント側で表示する。バックエンドが error_id で返すのは項目間・DB 整合チェックの 6 種のみ：R60W0005、R60W0006、R60W0010、R60W0014、R60W0024、R60E0025。したがって R60W0009 / W0012 / W0015 / W0016 / W0103 / W0113 / W0131 を API 応答から探しても見つからない。

## R60Maker / 単体テストの総数と内訳

`R60Maker:test:summary` / `test`
R60Maker の単体テストは 216 項目、FP 13、バグ 0。内訳は画面遷移 4、画面レイアウト 65（検索条件 17・検索結果 18・新規 10・複製 10・修正 10）、入力チェック 55（表示 5・仕掛表示 5・削除 11・登録 16・その他 2・必須 16）、イベント処理 69、特殊処理 23（権限検索結果 6・権限マスタ 10・例外 3・固有 4）。

## R60Maker / テスト観点の写像（同値分割・境界値・決定表）

`R60Maker:test:viewpoint` / `test`
旧仕様は正常／境界／異常の分類を持たない。写像は次のとおり。同値分割：単項目チェックの有効値・無効値・空値、権限マトリクス、モード×緊急配信×削除選択。境界値：コード 5 文字、日本語名 30Byte、カナ名 15 文字、検索上限、ページ先頭・最終頁。デシジョンテーブル：登録 8 パターン、削除 4 パターン、権限 6＋10 パターン。

## R60Maker / 登録 8 パターン・削除 4 パターンの決定表

`R60Maker:test:decision-tables` / `test`
登録は新規／複製／修正 × 削除選択 × 緊急配信の 8 パターンで、イベント処理 No12 の 8 件に対応する。削除は削除のみ／他項目変更有 × 緊急配信の 4 パターンで、イベント処理 No11 の 4 件に対応する。いずれも更新後にマスタの値が正しいこと、緊急配信 ON でパッケージが呼ばれることを確認する。

## R60Maker の主要な差異（D-MK-01〜13）

`R60Maker:review:deviations` / `review`
主要な差異。項目数は検索 33・マスタ 9 で骨架の 56 と不一致（D-MK-01）。download は SQL 文字列連結（D-MK-02）。delete/edit の応答に完了メッセージが無い（D-MK-03）。extra='ignore'（D-MK-04）。REG_STS の判定が設計書に無い（D-MK-05）。複製初期化が元の DEL_FLG / SEND_KBN を返す（D-MK-06）。廃止シートが残る（D-MK-07）。削除時緊急配信の対象が曖昧（D-MK-08）。前提条件・排他条件の本文が無い（D-MK-09）。Create/Copy が未使用（D-MK-10）。AB 404 は未測定（D-MK-11）。mode 値が設計に無い（D-MK-12）。標準仕様参照のイベントに本文が無い（D-MK-13）。

## R60Maker / A/B レポートの 404 の読み替え

`R60Maker:review:ab-404` / `review`
R60Maker の A/B レポートは全端点 404。これは『実装が無い』ではなく『測定環境に公開されていなかった』である。根拠は app/main.py:48 で import、:132 で include_router され、R60MakerController.py:23 の prefix='/R60Maker' と端点パスが AB の要求と一致するため。404 は未公開、500 は実装の失敗、null は未測定として読み替える。

## R60MakerCreate.vue / R60MakerCopy.vue は参照されていない

`R60Maker:review:unused-components` / `review`
R60Maker.vue は R60MakerEdit.vue だけを import する。R60MakerCreate.vue は入力項目に v-model が無く、メッセージ ID も持たない。R60MakerCopy.vue は edit_data.key_001..003 を参照し、削除チェックはコメントアウトされている。3 モード分のチェックとダイアログは R60MakerEdit.vue に集約されている。Create/Copy を現行実装として学習しない。

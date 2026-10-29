---
id: KNOW-LEGACY-R60-CHUNKS-R60AREA
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-chunks-r60area
scope: project
project_id: P-R60-001
title: R60Area — 検索摘要（57 条）
doc_type: glossary
conf_level: 30
updated_at: '2026-10-29'
---

# R60Area — 検索摘要（57 条）

> 各節は検索用に書かれた摘要であり、原文のスライスではない。
> 正本は `screens/` と `modules/` 側。

## R60Area 画面概要・権限・使用頻度

`R60Area:screen:overview` / `screen`
R60Area はエリアマスタメンテナンス画面。本画面はエリア情報のメンテナンスを行う。前提条件はなし。排他条件はあり（画面項目間・DB整合チェックシート参照）。利用対象者は利用権限保持者のみ。使用頻度は日次・随時。画面区分は参照・登録・更新・削除・DL。関連画面はロケーション検索（入力支援）、共通メニュー、セッションエラー、オンライン制御エラー、システムエラー。

## R60Area / 検索画面の項目構成（76 項目）

`R60Area:screen:search-list` / `screen`
検索画面は項目番号 1〜76 の 76 項目。内訳はヘッダー5、検索条件8（会社・事業場・エリアコード・削除含む・1頁件数・仕掛表示・表示・検索条件非表示）、ページャ6、行操作2（複製・送信）、一覧42列（No25〜66）、下部ページャ5、ボタン4（戻る・業務終了・ダウンロード・新規）。エリアコードは前方一致で、ワイルドカード入力は不要。

## R60Area / マスタ項目画面の項目構成（45 項目）

`R60Area:screen:master-panel` / `screen`
マスタ項目画面は項目番号 1〜45 の 45 項目。キー3（会社・事業場・エリアコード）、属性はエリア名・略称・受払場所・受払／債務／債権の計上事業場と計上部署・自動払出承認フラグ・届先名・移動デフォルトロケーション（原材料／半製品）・集中購買系、状態は緊急配信チェックと削除チェック、ボタン3（戻る・削除・登録）。実装では R60AreaCreate.vue／R60AreaEdit.vue／R60AreaCopy.vue の 3 コンポーネントに分かれる。

## R60Area / キー項目 CMP_CD（会社コード）

`R60Area:field:key-cmp-cd` / `field`
CMP_CD は会社コード。R60_AREA_M_TBL の主キーの 1 つ。更新は行わない（項目移送表の更新欄が空）。検索画面ではドロップダウンで選択し完全一致。マスタ画面では新規・複製時のみドロップダウン、修正時はラベル表示。会社を変更すると関連する事業場・受払場所・各計上部署リストを再作成する。

## R60Area / キー項目 JIG_CD（事業場コード）と複合キー文字列

`R60Area:field:key-jig-cd` / `field`
JIG_CD は事業場コード。R60_AREA_M_TBL の主キーの 1 つで、更新しない。検索リクエストでは jig_cd が 'CMP_CD,JIG_CD' 形式の複合キー文字列で渡され、実装は split(',') の後半を検索条件に使う。この形式は設計書に明文がなく実装上の暗黙規約である。値にカンマが含まれると壊れる。

## R60Area / キー項目 ARA_CD（エリアコード）の入力規則

`R60Area:field:key-ara-cd` / `field`
ARA_CD はエリアコード。R60_AREA_M_TBL の主キーの 1 つで更新しない。半角英数字 7 文字以内。違反時は R60W0103「##1は半角英数字##2文字以内で入力して下さい。」（##1=エリアコード、##2=7）。新規・複製では必須（R60W0009）。検索時は前方一致で、入力値に '%' を付けて LIKE 検索する。

## R60Area / エリア名・エリア略称の桁数とコピー動作

`R60Area:field:ara-nm-rnm` / `field`
ARA_NM（エリア名）は 30Byte、ARA_RNM（エリア略称）は 16Byte。超過時は R60W0131「##1は半角##2文字以内で入力して下さい。（全角使用可）」。エリア名のフォーカス喪失時、エリア略称が未設定ならエリア名の先頭 16Byte をコピーする。あわせて、支払案内書に表示する届先名が未設定ならエリア名をコピーする。

## R60Area / UKH_PLC_CD（受払場所）の選択元

`R60Area:field:ukh-plc-cd` / `field`
UKH_PLC_CD は受払場所コード。受払場所マスタから、REG_STS='1' かつ DEL_FLG='0' の行をドロップダウンに表示する。事業場を変更すると受払場所リストを再作成する。緊急配信チェック ON のときは必須 13 項目の 1 つ。REG_STS 判定の 16 項目にも含まれる。

## R60Area / 計上事業場・計上部署（受払／債務／債権）の 6 項目

`R60Area:field:keij-jig-bsy` / `field`
計上事業場・計上部署は受払・債務・債権の 3 系統で 6 項目。事業場側は UKH_KEIJ_JIG_CD／SAIM_KEIJ_JIG_CD／SAIKN_KEIJ_JIG_CD、部署側は UKH_KEIJ_BSY_CD／SAIM_KEIJ_BSY_CD／SAIKN_KEIJ_BSY_CD。設計書の項目名は『受払計上場所』『債務計上場所』『債権計上場所』と書くが、実カラムは事業場コードと部署コードであり『場所』ではない。各計上事業場を変更すると対応する部署リストを再作成し、ロケーション選択時フラグを OFF にする。

## R60Area / JID_HAR_SYN_FLG（自動払出承認フラグ）

`R60Area:field:jid-har-syn-flg` / `field`
JID_HAR_SYN_FLG は自動払出承認フラグ。コード値明細の情報ID 000000115 からドロップダウンを生成する。緊急配信チェック ON のときは必須 13 項目の 1 つ。REG_STS 判定の 16 項目にも含まれる。

## R60Area / SHR_ANSY_TDK_NM（支払案内書に表示する届先名）

`R60Area:field:shr-ansy-tdk-nm` / `field`
SHR_ANSY_TDK_NM は支払案内書に表示する届先名。全角 25 文字以内。超過時は R60W0118「##1は全角##2文字以内で入力して下さい。」（##1=支払案内書に表示する届先名、##2=25）。未設定ならエリア名をコピーする。緊急配信時の必須 13 項目、REG_STS 判定の 16 項目に含まれる。

## R60Area / 移動デフォルトロケーション（原材料／半製品）

`R60Area:field:ido-dflt-plc` / `field`
移動デフォルトロケーションは IDO_DFLT_PLC_CD_GZR（原材料）と IDO_DFLT_PLC_CD_HSH（半製品）の 2 項目。半角英数大文字と記号 '_','-','(',')' のみ、8 文字以内。違反時は R60W0128。ロケーションマスタに REG_STS='1' かつ DEL_FLG='0' で存在しない場合は R60W0033（背景色赤・フォーカスセット）。名称は R60_Get_Plc_Infomation_FNC で取得し、検索アイコンからロケーション検索画面を開く。

## R60Area / 集中購買系の項目群と入力必須コメント

`R60Area:field:sych-kbi-group` / `field`
集中購買系は会社・事業場・受払計上事業場・受払計上部署・債務計上事業場・債務計上部署・債権計上事業場・債権計上部署。各項目にはコメント『集中購買品目を扱うエリアの場合、入力必須』が付く（8 箇所）。初期値はコード値明細の情報ID 000000315〜000000320 から取得する。集中購買会社を変更すると集中購買系の各リストを再作成する。

## POST /api/R60Area/init（初期表示）

`R60Area:api:init` / `api`
初期表示の端点。ユーザ情報・権限情報・画面タイトル背景色を標準仕様で取得し、R60_GET_MESSAGE_FNC で使用メッセージを取得、検索条件部の画面項目オブジェクトを生成する。応答は会社リスト・事業場リスト・頁件数リスト・既定頁件数・メッセージ情報。冒頭でセッション存在チェックとオンライン利用可否チェックを行う。実装は R60AreaController.py の /init（1235-1428 行）。

## POST /api/R60Area/search（検索）

`R60Area:api:search` / `api`
検索の端点。要求は cmp_cd・jig_cd・ara_cd・btn・is_deleted・current_page・page_limit・sort_field・sort_order を params 封筒で受ける。btn='0' は仕掛表示で REG_STS='0' を条件に追加し、btn='1' は表示で REG_STS を条件に足さない。応答は total・data[]・error_id。実装は 1429-1649 行。A/B レポートでは search が 500 で崩壊しており、完成した参照実装として扱わない。

## POST /api/R60Area/download（CSV 出力）

`R60Area:api:download` / `api`
ダウンロードの端点。ファイル名は R60_GET_CODE_CHI_MEISAI_FNC('000000099','R60_AREA_M_TBL','1')、ヘッダは R60_GET_SELECT_COLUMN_FNC('R60_AREA_M_TBL','H')、データ項目は同 'D' で取得する。表示・仕掛表示と同じ検索条件とソート順でデータを取得し、R60CsvUtil で CSV を生成して添付で返す。実装は 1650-1711 行で、検索条件を SQL 文字列へ直接連結している（SQL インジェクションの余地）。

## POST /api/R60Area/initEdit（マスタ画面初期化）

`R60Area:api:init-edit` / `api`
マスタ項目画面の初期化端点。mode='1' は新規、'2' は複製、'3' は修正。新規・複製では会社・事業場リスト、受払場所、費用計上部署、自動払出承認フラグ、集中購買会社リストを生成し、コード値明細 000000315〜000000320 から初期値を取る。修正では対象行を取得して data に設定する。実装は 1713-1991 行。

## POST /api/R60Area/getPlcNm（ロケーション名取得）

`R60Area:api:get-plc-nm` / `api`
ロケーション名取得の端点。会社・事業場・ロケーションコードをキーに R60_Get_Plc_Infomation_FNC 相当で名称を引き、data に文字列で返す。マスタ画面で移動デフォルトロケーションのコードを入力・選択したときに名称欄を更新するために使う。設計書の画面項目内容には名称取得関数の記載があるが、専用端点としては明記されていない。

## POST /api/R60Area/delete（論理削除）

`R60Area:api:delete` / `api`
削除の端点。単項目チェック→項目間チェック→被参照チェック（R60_Check_Area_Info_FNC）→排他チェック→ロケーション存在チェック→REG_STS 判定→DEL_FLG='1' の UPDATE→緊急配信→commit の順。応答は error_code と error_id。物理削除は行わない。実装は 2033-2322 行。

## POST /api/R60Area/edit（登録・更新・論理削除）

`R60Area:api:edit` / `api`
登録・更新の端点。新規・複製は重複キーチェック→ロケーション存在チェック→REG_STS 判定→INSERT→緊急配信→commit。修正は排他チェック→ロケーション存在チェック→REG_STS 判定→削除チェック時のみ被参照チェック→UPDATE→緊急配信→commit。データが変更されていなければ R60W0016 で中断する。実装は 2324-2818 行。

## R60Area / 検索条件（WHERE 句）の生成规则

`R60Area:logic:search-where` / `logic`
検索条件は次の順で組み立てる。cmp_cd が非空なら CMP_CD = :CMP_CD。jig_cd が非空なら JIG_CD = :JIG_CD（'CMP_CD,JIG_CD' 形式なら後半を使用）。ara_cd が非空なら ARA_CD LIKE :ARA_CD ESCAPE '\'（値は ara_cd+'%'）。btn='0' なら REG_STS = '0'。is_deleted='0' なら DEL_FLG = '0'。search は text() と bind パラメータを使い、値を文字列連結しない。

## R60Area / 件数取得・0 件・上限超過の判定

`R60Area:logic:search-count-limit` / `logic`
SELECT COUNT(CMP_CD) FROM R60_AREA_M_TBL WHERE {where} で総件数を取得する。0 件なら R60W0010『対象データが存在しませんでした。』を返し明細部を非表示にする。上限件数（コード値明細 情報ID 000000024）を超えたら R60W0005『検索結果件数が上限値を超えました。（上限値=##1件、HIT件数=##2件）検索条件を再設定して下さい。』を返す。

## R60Area / 検索のソート順と許可ソート列

`R60Area:logic:search-sort` / `logic`
既定のソート順は DEL_FLG 昇順→CMP_CD 昇順→事業場表示順 昇順（R60_Get_Jig_Information_FNC の戻り値）→JIG_CD 昇順。ユーザがソートできる列は会社（CMP_CD）・事業場（JIG_CD）・エリアコード（ARA_CD）の 3 つだけで、実装の ALLOWED_SORT_FIELDS と一致する。白名单外・未指定は既定ソートへフォールバックし、末尾に ROWID を付けて順序を一意化する。

## R60Area / ページング方式（OFFSET/FETCH + ROWID）

`R60Area:logic:search-paging` / `logic`
page_limit は既定 10、current_page は 1 起算。総ページ数は ceil(total/page_limit)。範囲外の頁は 1 または最終頁へ補正する。取得 SQL は ORDER BY {sort}, ROWID OFFSET {offset} ROWS FETCH FIRST {page_limit} ROWS ONLY。骨架規則は ROWID 方式を原則とするが、本実装は OFFSET/FETCH を使い、末尾に ROWID を足して順序を安定させている。

## R60Area / マスタ画面のモード別初期化

`R60Area:logic:master-init` / `logic`
新規（mode='1'）は全項目ブランクから開始し、会社・事業場リストと集中購買会社の初期値をコード値明細 000000315〜000000320 から取る。複製（mode='2'）は選択行の値を複製し、キー 3 項目はユーザが選び直す。修正（mode='3'）は対象行を取得し、キー 3 項目をラベル表示にして編集不可とする。削除済みデータは削除チェックが ON の状態で開く。

## R60Area / ドロップダウン連動の規則

`R60Area:logic:dropdown-linkage` / `logic`
会社変更→事業場・受払場所・各計上部署リストを再作成。事業場変更→受払場所リストを再作成。受払／債務／債権の各計上事業場変更→対応する部署リストを再作成し、ロケーション選択時フラグを OFF にする。集中購買会社変更→集中購買事業場・集中購買の各計上事業場・各計上部署リストを再作成。集中購買の各計上事業場変更→対応する集中購買計上部署リストを再作成。

## R60Area / ロケーション選択時フラグの挙動

`R60Area:logic:location-flag` / `logic`
ロケーション選択時フラグは、複製・新規を開いたとき OFF。ロケーション検索画面から戻ったとき ON。各計上事業場を変更したとき OFF。会社変更時、フラグが OFF のときだけ受払／債務／債権の計上事業場リストを再作成し、ON のときは再作成しない。これは選択済みロケーションを保持するためである。

## R60Area / 登録・削除の入力チェック順序（14 段）

`R60Area:logic:edit-validation-order` / `logic`
登録・削除のチェック順は固定。1 全項目変更なし→R60W0016。2 新規・複製のキー必須→R60W0009。3 エリアコード半角英数字 7 文字→R60W0103。4 緊急配信 ON の必須 13 項目→R60W0012。5 緊急配信 OFF の必須 13 項目→R60W0015。6 エリア名 30Byte・略称 16Byte→R60W0131。7 届先名 全角 25 文字→R60W0118。8 ロケーション 8 文字→R60W0128。9 計上事業場≠事業場の確認→R60A0039／R60A0040。10 重複キー→R60W0014。11 排他→R60W0006。12 ロケーション未登録→R60W0033。13 被参照→R60W0024／R60E0025。14 登録／削除確認→R60A0003／R60A0004。

## R60Area / REG_STS（登録ステータス）判定 16 項目

`R60Area:logic:reg-sts` / `logic`
次の 16 項目すべてに値がある場合 REG_STS='1'（確定）、それ以外は '0'（未確定）。CMP_CD、JIG_CD、ARA_CD、ARA_NM、ARA_RNM、UKH_PLC_CD、UKH_KEIJ_JIG_CD、UKH_KEIJ_BSY_CD、SAIM_KEIJ_JIG_CD、SAIM_KEIJ_BSY_CD、SAIKN_KEIJ_JIG_CD、SAIKN_KEIJ_BSY_CD、JID_HAR_SYN_FLG、SHR_ANSY_TDK_NM、IDO_DFLT_PLC_CD_GZR、IDO_DFLT_PLC_CD_HSH。緊急配信の必須 13 項目は、この 16 項目からキー 3 項目を除いたものである。

## R60Area / 排他チェック（KSN_DAT / KSN_KBN）

`R60Area:logic:exclusive` / `logic`
R60_AREA_M_TBL から KSN_KBN と KSN_DAT を取得し、画面が保持する ksn_dat と不一致、かつ KSN_KBN がオンライン更新の場合に R60W0006『他の端末からデータが既に更新されています。』を返して処理を中断する。バッチ更新（KSN_KBN がオンライン以外）は不一致でも許可する。実装は 2845-2873 行の haita_check_area。

## R60Area / 被参照チェック（R60_Check_Area_Info_FNC）

`R60Area:logic:referential` / `logic`
R60_Check_Area_Info_FNC(CMP_CD, JIG_CD, ARA_CD) を呼ぶ。戻り値が null なら R60E0025『削除可否チェックファンクションでエラーが発生しました。』、'1' なら R60W0024『このデータは他のマスタで参照されているため削除できません。』を返す。呼ぶ時機は、削除ボタン押下時（必ず）と、修正モードで DEL_FLG='1' にする場合（更新前）。

## R60Area / ロケーション存在チェック

`R60Area:logic:location-exist` / `logic`
R60_PLC_M_TBL を CMP_CD・JIG_CD・PLC_CD で検索し、REG_STS='1' かつ DEL_FLG='0' の行が無ければ R60W0033『指定された##1＝の組合せは##2に存在しません。』（##1=会社・事業場・移動デフォルトロケーション、##2=ロケーションマスタ）を返し、背景色を赤にしてフォーカスをセットする。対象は原材料と半製品の 2 項目。

## R60Area / 緊急配信の呼び出し条件

`R60Area:logic:emergency-send` / `logic`
緊急配信チェック ON のとき SEND_STS='9' を設定し、R60_EMERGENCY_SEND_CTL_PKG を（テーブルID='R60_AREA_M_TBL'、ログインユーザID、プログラムID='R60Area'）で呼ぶ。呼び出し箇所は新規・複製の登録後、修正の更新後、削除後の 3 つ。設計書の手順は『登録・更新・削除→commit→緊急配信』の順に読めるが、実装は緊急配信を呼んでから commit しており、トランザクション境界は要確認である。

## R60Area / 論理削除（DEL_FLG）

`R60Area:logic:logical-delete` / `logic`
削除は物理削除ではなく UPDATE で DEL_FLG='1' を設定する。あわせて SEND_STS、KSN_KBN／KSN_STF_ID／KSN_DAT／KSN_PGM_ID、REV_NO+1 を更新する。削除後も検索条件『削除含む』を ON にすれば参照できる。キー 3 項目は更新しない。

## R60Area / R60W0012／R60W0015 の必須 13 項目

`R60Area:error:required-13` / `error`
緊急配信チェック ON で必須 13 項目のいずれかが未入力なら R60W0012『緊急配信をするには、必須項目を指定する必要があります。』。削除時、または緊急配信 OFF で登録するときに必須 13 項目のいずれかが未入力なら R60W0015『データを削除する際には、必須項目を入力しておく必要があります。』。13 項目は ARA_NM、ARA_RNM、UKH_PLC_CD、UKH_KEIJ_JIG_CD、UKH_KEIJ_BSY_CD、SAIM_KEIJ_JIG_CD、SAIM_KEIJ_BSY_CD、SAIKN_KEIJ_JIG_CD、SAIKN_KEIJ_BSY_CD、JID_HAR_SYN_FLG、SHR_ANSY_TDK_NM、IDO_DFLT_PLC_CD_GZR、IDO_DFLT_PLC_CD_HSH。

## R60Area / R60W0005／R60W0010（件数関連）

`R60Area:error:count-messages` / `error`
検索結果 0 件は R60W0010『対象データが存在しませんでした。』で明細部を非表示にする。上限超過は R60W0005『検索結果件数が上限値を超えました。（上限値=##1件、HIT件数=##2件）検索条件を再設定して下さい。』で明細部を非表示にする。いずれも検索条件は残す。実装は 1485-1498 行付近。

## R60Area / R60W0014（重複キー）

`R60Area:error:duplicate-key` / `error`
新規・複製で同一キー（CMP_CD, JIG_CD, ARA_CD）が既に存在する場合、R60W0014『既に同一データが存在します。』を返し、会社・事業場・エリアコードの背景色を赤にする。修正ではキーを変更できないため重複チェックは行わない。実装は 2440-2451 行付近。

## R60Area / R60A0039／R60A0040 は実装されていない

`R60Area:error:a0039-a0040` / `error`
R60A0039 は登録時、R60A0040 は削除時に、各計上事業場（受払・債務・債権・集中購買系）が事業場と異なる場合の確認メッセージ『##1が##2と異なっていますが登録しますか？／削除しますか？』。設計書は確認ダイアログを要求しているが、実装では R60AreaController.py:2453-2489（登録）と 2155-2191（削除）がすべてコメントアウトされており、確認なしで処理が進む。設計書を正とし、実装は未了である。

## R60Area / R60W0006／R60E0025（排他・チェック異常）

`R60Area:error:exclusive-and-check-fnc` / `error`
R60W0006『他の端末からデータが既に更新されています。』は KSN_DAT 不一致かつ KSN_KBN がオンライン更新のとき。アラート表示で処理中断。R60E0025『削除可否チェックファンクションでエラーが発生しました。』は R60_Check_Area_Info_FNC の戻り値が null のとき。アラート表示で処理中断。

## R60Area のメッセージ 23 件の内訳

`R60Area:error:message-inventory` / `error`
R60Area で使うメッセージは 23 件。内訳は W（警告）15 件、A（確認）5 件、I（情報）2 件、E（異常）1 件。A は R60A0003 登録確認、R60A0004 削除確認、R60A0008 業務終了確認、R60A0039 登録時の計上事業場相違確認、R60A0040 削除時の同確認。E は R60E0025。R60A0039 と R60A0040 は未実装。

## R60Area / テスト観点：検索（表示／仕掛表示）

`R60Area:test:search` / `test`
表示ボタン（4-2-1..9）と仕掛表示ボタン（4-3-1..9）は各 9 パターン。観点は、検索条件（会社・事業場・エリアコード前方一致・削除含む）の反映、現新比較、ソート順、0 件時の挙動（検索条件保持・戻る／ダウンロード／新規は非活性・業務終了は活性）、上限超過時の同挙動。仕掛表示は REG_STS='0' を条件に含む点だけが異なる。

## R60Area / テスト観点：登録・削除のデシジョンテーブル

`R60Area:test:decision-tables` / `test`
削除（4-29-1..4）は『削除のみ／他項目も変更』×『緊急配信 ON/OFF』の 4 パターン。登録（4-30-1..8）は『新規／複製／修正』×『削除チェック ON/OFF』×『緊急配信 ON/OFF』の 8 パターン。確認点は、R60_AREA_M_TBL が正しく更新されること、緊急配信 ON で R60_EMERGENCY_SEND_CTL_PKG が呼ばれること、更新後データが画面に表示されること、現新比較（4-30-8 を除く）。

## R60Area / テスト観点：権限マトリクス

`R60Area:test:permission-matrix` / `test`
検索条件・結果画面表示時は 12 パターン（5-1-1）。権限区分 Y/N、自工場更新権限、他工場更新権限の組合せで、表示・仕掛表示の可否と新規・複製ボタンの活性が決まる。マスタ画面表示時は 10 パターン（5-1-2）。新規・複製・修正の操作可否と、削除・登録ボタンの活性が決まる。

## R60Area / 単体テスト 560 項目の内訳

`R60Area:test:totals` / `test`
R60Area の単体テストは総項目 560、実施 560、バグ 0。内訳は画面遷移 5、画面レイアウト 203（検索条件 18・検索結果 56・新規 43・修正 43・複製 43）、入力チェック 97（表示 3・削除 44・登録 48・その他 2）、イベント処理 229、特殊処理 26（権限 12+10・例外 4）。検算式は 5+203+97+229+26=560。

## R60Area / D-AR-01：項目数 76／45 と骨架の 56 の不一致

`R60Area:review:item-count` / `review`
設計書の画面項目は検索 76 件、マスタ 45 件。骨架の I-201..I-256 は 56 件で、どちらとも一致しない。56 は骨架構築時に置いた仮の枠であり設計書から導いた数ではない。R60Area で I-ID を起こす場合は、検索とマスタを別採番し、設計書の項目番号を source_locator に持つ。

## R60Area / D-AR-05：ダウンロードの SQL 文字列連結

`R60Area:review:download-sql` / `review`
R60AreaController.py:1666-1682 の download は cmp_cd と jig_cd を f-string／+ で WHERE 句へ埋め込む。同じファイルの search は bind パラメータを使う。入力値によって SQL インジェクションが成立し得る。対策は download も bind パラメータ化するか、CSV ユーティリティ側でパラメータを受ける形へ変えること。設計を変える場合は CR を起票する。

## R60Area / D-AR-08：A/B レポートは未完了

`R60Area:review:ab-report` / `review`
A/B レポートでは、search と check が 500 でサーバー崩壊（同一入力で旧 SQL は正常）、detail と new に 8 列の差異、modify と download は SKIP、head と init は構造差（旧＝複数 SELECT、新＝1 JSON）で値は一致。R60Area の新実装を完成した参照実装として扱わない。学習の正は設計書と単体テスト仕様である。

## R60Area / D-AR-04：イベント番号の衝突

`R60Area:review:event-numbering` / `review`
12_イベント一覧 では No10=ダウンロード、No16=債務計上事業場ドロップダウン変更、No25=削除、No26=登録。14_業務処理説明 には『イベントNo16：ダウンロードボタンクリック』と書く箇所があり、番号が衝突する。イベント番号を検索キーにすると別の処理に当たるため、RAG ではイベント名称＋処理内容を主キーにする。

## R60Area / 規約：ソート項目の白名单方式

`R60Area:convention:sort-whitelist` / `convention`
一覧のソートは、リクエストの sort_field をそのまま SQL に連結せず、許可列の白名单と照合する。R60Area の許可列は CMP_CD（会社）・JIG_CD（事業場）・ARA_CD（エリアコード）の 3 つ。白名单外・未指定は既定ソートへフォールバックし、末尾に ROWID を付けて順序を一意化する。白名单方式は.sql 識別子を bind できないため、識別子の安全性を白名单で担保する。

## R60Area / 規約：複合キー文字列 'CMP_CD,JIG_CD'

`R60Area:convention:composite-key` / `convention`
R60Area のフロントは、事業場ドロップダウンの値を 'CMP_CD,JIG_CD' 形式の 1 文字列で保持する。バックエンドは jig_cd.split(',')[1] を事業場コードとして使う箇所と、split(',')[0] を部署コードとして使う箇所がある。この形式は設計書に明文がなく実装上の暗黙規約であり、値にカンマが含まれると壊れる。API 契約カードに明記する。

## R60Area / CSV ダウンロードの手順

`R60Area:logic:download-csv` / `logic`
1 R60_GET_CODE_CHI_MEISAI_FNC('000000099','R60_AREA_M_TBL','1') でファイル名を取得。2 R60_GET_SELECT_COLUMN_FNC('R60_AREA_M_TBL','H') でヘッダを取得。3 同 'D' でデータ項目を取得。4 表示・仕掛表示と同じ検索条件とソート順でデータを取得。5 R60CsvUtil で CSV を生成し添付ファイルとして返す。列の並びは設計書の項目移送表と抽出項目定義に従う。

## R60Area / CSV 出力の検索条件は画面の状態を引き継ぐ

`R60Area:logic:download-condition` / `logic`
ダウンロードは独立した検索を行わず、直前の表示／仕掛表示で使った検索条件とソート順を引き継ぐ。したがって、仕掛表示の後にダウンロードすると REG_STS='0' のデータだけが出力される。削除含むの状態も引き継ぐ。画面の状態を渡し忘れると、表示中の一覧と CSV の中身が食い違う。

## R60Area / DEL_FLG（削除フラグ）と検索条件『削除含む』

`R60Area:field:del-flg` / `field`
DEL_FLG は論理削除フラグ。'1' が削除済み、'0' が有効。検索条件『削除含む』が OFF のときは DEL_FLG='0' を条件に追加する。ON のときは条件に足さず、削除済みも含めて検索する。既定ソートでは DEL_FLG 昇順を先頭に置くため、削除済みは一覧の後ろに並ぶ。物理削除は行わない。

## R60Area / KSN_DAT（更新日時）と排他制御

`R60Area:field:ksn-dat` / `field`
KSN_DAT は更新日時で、REV_NO とともに排他制御に使う。修正・削除時に、画面が保持する ksn_dat と DB の KSN_DAT を比較し、不一致かつ KSN_KBN がオンライン更新なら R60W0006 で中断する。バッチ更新は不一致でも許可する。更新時は KSN_DAT と REV_NO を新しい値に進める。

## R60Area / SEND_STS（緊急配信ステータス）

`R60Area:field:send-sts` / `field`
SEND_STS は緊急配信ステータス。画面の緊急配信チェック ON で '9'、OFF で '0' を設定する。'9' のとき登録・更新・削除の後に R60_EMERGENCY_SEND_CTL_PKG を呼ぶ。一覧の『送信』列は R60_Get_Code_Chi_Meisai_FNC('000000057', SEND_STS, '1') で名称表示する。

## R60Area の人間実装の対応表

`R60Area:screen:implementation-map` / `screen`
初期表示 1235-1428、検索 1429-1649、ダウンロード 1650-1711、マスタ画面 1713-1991、ロケーション名 1992-2032、削除 2033-2322、登録・更新 2324-2818。補助関数は REG_STS 判定 2820-2843、排他 2845-2873、ロケーション存在 2875-2895、緊急配信 2898-2912。フロントは R60Area.vue（一覧）と R60AreaCreate.vue／R60AreaEdit.vue／R60AreaCopy.vue（マスタ）。

## R60Area / 規約：BaseCamelModel の extra は実装では ignore

`R60Area:convention:extra-ignore` / `convention`
R60AreaController.py:33-39 の BaseCamelModel は alias_generator=to_camel、populate_by_name=True、serialize_by_alias=True、extra='ignore'。骨架規則（03-design-coding.md §2）は extra='forbid' を固定としている。実装では定義外の入力が 422 にならず静かに無視される。実装値を記録し、規則を変えるかは人の裁定事項とする。

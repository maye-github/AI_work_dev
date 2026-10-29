---
id: KNOW-LEGACY-R60-MODULE-R60MAKER-ERRORS-VIEW
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-modules-r60maker-04-errors
scope: project
project_id: P-R60-001
title: R60Maker — エラー一覧
doc_type: design-detail
conf_level: 30
updated_at: '2026-10-29'
---

# R60Maker — エラー一覧

> 正本は同ディレクトリの `04-errors.yaml`。本ファイルは検索用の可読表現であり、
> 手で編集しない（`py -3 -m tools.kb_migrate --apply` で作り直す）。

| 項目 | 値 |
|---|---|
| id | KNOW-LEGACY-R60-MODULE-R60MAKER-ERRORS |
| type | knowledge |
| status | open |
| sensitivity | internal |
| owner | AI-SE |
| version | 0.1.0 |

## message_id_convention

| 項目 | 値 |
|---|---|
| W | 警告（処理中断。背景色赤・フォーカスセット・アラート・ダイアログのいずれか） |
| A | 確認（Yes/No。No なら処理中断） |
| I | 情報（処理完了の通知） |
| E | 異常（ファンクション等の想定外エラー） |

## counts

| 項目 | 値 |
|---|---|
| total_message_ids | 19 |
| note | 単項目チェックと確認・完了メッセージはフロント側で表示する。 バックエンドが error_id で返すのは、項目間・DB 整合チェックの 6 種のみである。 |

### by_type

| 項目 | 値 |
|---|---|
| W | 13 |
| A | 3 |
| I | 2 |
| E | 1 |

### backend_returned

- R60W0005
- R60W0006
- R60W0010
- R60W0014
- R60W0024
- R60E0025

### frontend_only

- R60W0007
- R60W0009
- R60W0012
- R60W0015
- R60W0016
- R60W0103
- R60W0113
- R60W0131
- R60A0003
- R60A0004
- R60A0008
- R60I0001
- R60I0002


## req_ids

## messages

| message_id | type | trigger | text | params | action | design_locator | implementation_locator | note | required_fields |
|---|---|---|---|---|---|---|---|---|---|
| R60W0005 | W | 検索 HIT 件数が上限件数を超過 | 検索結果件数が上限値を超えました。（上限値=##1件、HIT件数=##2件）検索条件を再設定して下さい。 | {"##1": "上限件数（設計書の例は 3000）", "##2": "上限+1 以上の自然数"} | アラート表示 / 明細部を非表示 | 11_画面項目間・DB整合チェック r15 | R60MakerController.py:743 / Front-end/src/views/R60Maker.vue:380-382 | 設計書の ##1 は 3000 固定の例。実装はコード値マスタ(明細) 情報ID='000000024' から取得する （BP r68『共通仕様参照』）。 |  |
| R60W0006 | W | 削除・修正時に KSN_DAT が一致しない（他端末更新、かつオンライン更新区分） | 他の端末からデータが既に更新されています。 |  | アラート表示。処理中断 | 11_画面項目間・DB整合チェック r18 | R60MakerController.py:1038（削除）/ 1246（修正） |  |  |
| R60W0007 | W | マスタ項目画面で値変更ありのまま戻るボタン押下 | 編集内容が未登録です。破棄して良いですか？ |  | ダイアログ表示 | 10_画面単項目チェック r25 | Front-end/src/components/R60MakerEdit.vue:548 | 送信ステータスが変更前 '1:送信済み' の場合は判定から除外する（設計書 r25 注記）。 |  |
| R60W0009 | W | 新規・複製でメーカーコードが未入力 | 必須項目が未入力です。 |  | 背景色を赤 / フォーカス当たる | 10_画面単項目チェック r17 | Front-end/src/components/R60MakerEdit.vue:374-376 |  |  |
| R60W0010 | W | 検索結果が 0 件 | 対象データが存在しませんでした。 |  | アラート表示 / 明細部を非表示 | 11_画面項目間・DB整合チェック r14 | R60MakerController.py:734 / Front-end/src/views/R60Maker.vue:389-391 |  |  |
| R60W0012 | W | 緊急配信チェック ON でメーカー日本語名またはカナ名が未入力 | 緊急配信をするには、必須項目を指定する必要があります。 |  | 背景色を赤 / フォーカス当たる | 10_画面単項目チェック r20 / r23 | Front-end/src/components/R60MakerEdit.vue:392-411（削除）/ 471-490（登録） |  | ["MAKER_NM", "MAKER_ANM"] |
| R60W0014 | W | 新規・複製で同一キー（MAKER_CD）が存在 | 既に同一データが存在します。 |  | アラート表示 / メーカーコードの背景色を赤 | 11_画面項目間・DB整合チェック r19 | R60MakerController.py:1142 |  |  |
| R60W0015 | W | 削除時、または削除選択付き登録時でメーカー日本語名またはカナ名が未入力 | データを削除する際には、必須項目を入力しておく必要があります。 |  | 背景色を赤 / フォーカス当たる | 10_画面単項目チェック r19 / r22 | Front-end/src/components/R60MakerEdit.vue:418-437（削除）/ 495-514（登録） |  | ["MAKER_NM", "MAKER_ANM"] |
| R60W0016 | W | 複製・修正で登録ボタン押下時に全項目に変更なし | データが変更されていないため、登録を行いません。 |  | ダイアログ表示 | 10_画面単項目チェック r26 | Front-end/src/components/R60MakerEdit.vue:464 | 送信ステータスが変更前 '1:送信済み' の場合は判定から除外する（設計書 r26 注記）。 |  |
| R60W0024 | W | 削除対象が購入品目別仕入先マスタまたは原材料仕入単価マスタから参照されている | このデータは他のマスタで参照されているため削除できません。 |  | アラート表示 | 11_画面項目間・DB整合チェック r20-r21 | R60MakerController.py:1020 / 1033（削除）、1228 / 1241（修正で削除選択） |  |  |
| R60W0103 | W | メーカーコードが半角英数字以外、または 5 文字超過 | ##1は半角英数字##2文字以内で入力して下さい。 | {"##1": "メーカーコード", "##2": 5} | 背景色を赤 / フォーカス当たる | 10_画面単項目チェック r14（検索）/ r18（マスタ） | Front-end/src/views/R60Maker.vue:336（検索）/ R60MakerEdit.vue:381-383（マスタ） |  |  |
| R60W0113 | W | メーカーカナ名が半角文字・半角カタカナ以外、禁止文字（,）を含む、または 15 文字超過 | ##1は半角、かつ##2文字以内で入力して下さい。（但し、アポストロフィ、カンマ、円マーク、半角スペースは入力不可） | {"##1": "メーカーカナ名", "##2": 15} | 背景色を赤 / フォーカス当たる | 10_画面単項目チェック r24 | Front-end/src/components/R60MakerEdit.vue:453-456（削除）/ 530-533（登録） |  |  |
| R60W0131 | W | メーカー日本語名が全半角混在 30Byte 超過、または禁止文字 [, ' " \| ] を含む | ##1は半角##2文字以内で入力して下さい。（全角使用可） | {"##1": "メーカー日本語名", "##2": 30} | 背景色を赤 / フォーカス当たる | 10_画面単項目チェック r15（検索）/ r21（マスタ） | Front-end/src/views/R60Maker.vue:349（検索）/ R60MakerEdit.vue:443-446（削除）/ 520-523（登録） |  |  |
| R60A0003 | A | 登録ボタン押下（単項目・項目間チェック通過後） | 登録しますか？ |  | 確認ダイアログ。No なら処理中断 | 12_その他メッセージ r19 | Front-end/src/components/R60MakerEdit.vue:316 |  |  |
| R60A0004 | A | 削除ボタン押下（単項目・項目間チェック通過後） | 削除しますか？ |  | 確認ダイアログ。No なら処理中断 | 12_その他メッセージ r17 | Front-end/src/components/R60MakerEdit.vue:252 |  |  |
| R60A0008 | A | 業務終了ボタン押下 | 業務終了しますか？ |  | 確認ダイアログ | 12_その他メッセージ r14 | Front-end/src/views/R60Maker.vue:571-573 |  |  |
| R60I0001 | I | 登録・更新処理完了後 | 登録しました。 |  | 情報ダイアログ | 12_その他メッセージ r16 | Front-end/src/components/R60MakerEdit.vue:354 |  |  |
| R60I0002 | I | 削除処理完了後 | 削除しました。 |  | 情報ダイアログ | 12_その他メッセージ r18 | Front-end/src/components/R60MakerEdit.vue:292 |  |  |
| R60E0025 | E | 被参照チェックファンクションが想定外エラー（戻り値 null） | 削除可否チェックファンクションでエラーが発生しました。 |  | アラート表示。処理中断 | 11_画面項目間・DB整合チェック r17 | R60MakerController.py:1018 / 1031（削除）、1226 / 1239（修正で削除選択） |  |  |

## exception_cases

| name | trigger | behavior | design_locator | implementation_locator | note |
|---|---|---|---|---|---|
| SessionException | セッション情報が存在しない | セッションエラー画面へ遷移 | 14_業務処理説明 r13-r16 |  |  |
| OnlineException | オンライン利用可否フラグが NG | オンライン制御エラー画面へ遷移 | 14_業務処理説明 r18-r20 | 全 6 端点の先頭で r60util.chk_onl_flg() |  |
| システム例外 | SQLException / DB エラー / 想定外 Exception | ロールバックし、システムエラー画面へ遷移 | 13_イベント一覧 例外処理列（r14 / r25） |  | 例外処理列が明記されているのはイベント No1 と No11 のみ。No12 は空欄だが同じ扱いと読める。 |

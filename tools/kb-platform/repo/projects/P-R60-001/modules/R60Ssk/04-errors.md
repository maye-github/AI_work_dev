---
id: KNOW-LEGACY-R60-MODULE-R60SSK-ERRORS-VIEW
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-modules-r60ssk-04-errors
scope: project
project_id: P-R60-001
title: R60Ssk — エラー一覧
doc_type: design-detail
conf_level: 30
updated_at: '2026-10-29'
---

# R60Ssk — エラー一覧

> 正本は同ディレクトリの `04-errors.yaml`。本ファイルは検索用の可読表現であり、
> 手で編集しない（`py -3 -m tools.kb_migrate --apply` で作り直す）。

| 項目 | 値 |
|---|---|
| id | KNOW-LEGACY-R60-MODULE-R60SSK-ERRORS |
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

## retrieved_but_unused

| 項目 | 値 |
|---|---|
| note | init が R60_GET_MESSAGE_FNC で 16 件取得するが、本画面の設計シートにも フロント／バックエンドの実装にも使用箇所が無いメッセージがある（D-SS-07）。 |
| caution | 文言は本設計書に無いため、本カードには書かない（推測で補わない）。 |

### message_ids

- R60W0118
- R60W0113
- R60I0002
- R60A0004

### implementation_evidence

- R60SskController.py:401-417（取得）
- grep 'R60W0118\|R60W0113\|R60I0002\|R60A0004' Front-end/src で 0 件


## counts

| 項目 | 値 |
|---|---|
| design_defined | 11 |
| used_by_implementation | 12 |
| retrieved_but_unused | 4 |
| note | 単項目チェックと確認・完了メッセージはフロント側で表示する。 バックエンドが error_id で返すのは項目間・DB 整合チェックの 3 種のみである。 |

### by_type

| 項目 | 値 |
|---|---|
| W | 8 |
| A | 2 |
| I | 1 |
| E | 0 |

### backend_returned

- R60W0005
- R60W0006
- R60W0010

### frontend_only

- R60W0007
- R60W0009
- R60W0016
- R60W0106
- R60W0131
- R60W2002
- R60A0003
- R60A0008
- R60I0001


## req_ids

## messages

| message_id | type | trigger | text | params | action | design_locator | implementation_locator | note | inconsistency |
|---|---|---|---|---|---|---|---|---|---|
| R60W0005 | W | 表示ボタン押下時、HIT 件数が上限件数を超過 | 検索結果件数が上限値を超えました。（上限値=##1件、HIT件数=##2件）検索条件を再設定して下さい。 | {"##1": "上限件数（設計の例は 3000）", "##2": "上限+1 以上の自然数"} | アラート表示 / 明細部を非表示 | 10_画面項目間・DB整合チェック r15 | R60SskController.py:570-575 / Front-end/src/views/R60Ssk.vue:737-739 | 上限値は設計では 3000 固定の例。実装はコード値マスタ(明細) 情報ID='000000024' から取得する （BP r83-r84『標準仕様参照』）。 |  |
| R60W0006 | W | 登録時に KSN_DAT が不一致（他端末更新、かつ KSN_KBN='1'） | 他の端末からデータが既に更新されています。 |  | アラート表示。処理中断 | 10_画面項目間・DB整合チェック r17 | R60SskController.py:816-823 / Front-end/src/components/R60SskEdit.vue:406-412 | 設計は『バッチの場合は OK』。実装は KSN_KBN='1'（オンライン）の時だけ不一致をエラーにする。 |  |
| R60W0007 | W | マスタ項目画面で変更ありのまま戻るボタン押下 | 編集内容が未登録です。破棄して良いですか？ |  | 確認ダイアログ。OK なら閉じる | 本設計書の『その他メッセージ』に記載なし（D-SS-13） | Front-end/src/components/R60SskEdit.vue:325 | 実装は init で取得したメッセージを表示する。共通仕様側の定義と読めるが、 本設計書だけでは文言・条件を裏付けられない。 |  |
| R60W0009 | W | 表示ボタン押下時に会社が未選択 | 必須項目が未入力です。 |  | 背景色を赤 / フォーカス当たる | 09_画面単項目チェック r14 | Front-end/src/views/R60Ssk.vue:675 |  |  |
| R60W0010 | W | 検索結果が 0 件 | 対象データが存在しませんでした。 |  | アラート表示 / 明細部を非表示 | 10_画面項目間・DB整合チェック r14 | R60SskController.py:566-567 / Front-end/src/views/R60Ssk.vue:746-748 |  |  |
| R60W0016 | W | 登録ボタン押下時に全項目に変更なし | データが変更されていないため、登録を行いません。 |  | ダイアログ表示 | 09_画面単項目チェック r18 | Front-end/src/components/R60SskEdit.vue:354 |  |  |
| R60W0106 | W | 組織ユニットが半角英数字以外、または 8 文字超過 | ##1は半角数字##2文字で入力して下さい。 | {"##1": "組織ユニット", "##2": 8} | 背景色を赤 / 対象項目が選択状態 | 09_画面単項目チェック r15 | Front-end/src/views/R60Ssk.vue:681-684 |  | チェック内容は『半角英数字以外』をエラーとするが、メッセージ文言は『半角数字』である。 英字を許可するのか数字だけか、設計が矛盾している（D-SS-14）。 |
| R60W0131 | W | 正式名称が半角英数字以外、または 40byte 超過 | ##1は半角##2文字以内で入力して下さい。（全角使用可） | {"##1": "正式名称", "##2": "４０（設計の表記は全角）"} | 背景色を赤 | 09_画面単項目チェック r16 | Front-end/src/views/R60Ssk.vue:700-703 |  |  |
| R60W2002 | W | 経理用会社と経理用事業場の片方にのみ値がある | ##1はセットで入力して下さい。 | {"##1": "「経理用会社」、「経理用事業場」"} | 背景色を赤 / フォーカス当たる | 09_画面単項目チェック r19-r20 | Front-end/src/components/R60SskEdit.vue:366-383 | 設計では No7（経理用会社）と No8（経理用事業場）の 2 行に同じメッセージが付く。 |  |
| R60A0003 | A | 登録ボタン押下（単項目・項目間チェック通過後） | 登録しますか？ |  | 確認ダイアログ。No なら処理中断 | 11_その他メッセージ r16 | Front-end/src/components/R60SskEdit.vue:394 |  |  |
| R60A0008 | A | 業務終了ボタン押下 | 業務終了しますか？ |  | 確認ダイアログ | 11_その他メッセージ r14 | Front-end/src/views/R60Ssk.vue:792-798 |  |  |
| R60I0001 | I | 登録（更新）処理完了後 | 登録しました。 |  | 情報ダイアログ | 11_その他メッセージ r17 | Front-end/src/components/R60SskEdit.vue:423 |  |  |

## exception_cases

| name | trigger | behavior | design_locator | implementation_locator | note |
|---|---|---|---|---|---|
| SessionException | セッション情報が存在しない | セッション情報エラー画面へ遷移 | BP r14-r16 |  |  |
| OnlineException | オンライン利用可否フラグが NG | オンライン制御エラー画面へ遷移 | BP r18-r20 | 全 5 端点の先頭で r60util.chk_onl_flg() |  |
| システム例外 | SQLException / DB エラー / 想定外 Exception | ロールバックし、システムエラー画面へ遷移 | 12_イベント一覧 r14（イベントNo1）/ r28（イベントNo14） |  | 例外処理列が明記されているのはイベント No1 と No14 のみ。登録（No16）は空欄だが、 同様の扱いと読むほかない（D-SS-15）。 |

---
id: KNOW-LEGACY-R60-MODULE-R60MAKER-REVIEW-VIEW
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-modules-r60maker-06-review
scope: project
project_id: P-R60-001
title: R60Maker — レビュー指摘と処置
doc_type: design-detail
conf_level: 30
updated_at: '2026-10-29'
---

# R60Maker — レビュー指摘と処置

> 正本は同ディレクトリの `06-review.yaml`。本ファイルは検索用の可読表現であり、
> 手で編集しない（`py -3 -m tools.kb_migrate --apply` で作り直す）。

| 項目 | 値 |
|---|---|
| id | KNOW-LEGACY-R60-MODULE-R60MAKER-REVIEW |
| type | knowledge |
| status | open |
| sensitivity | internal |
| owner | AI-SE |
| version | 0.1.0 |

## ab_comparison

| 項目 | 値 |
|---|---|
| status | not_measured |
| evidence | A/B レポートの 8 端点はすべて 404。ただし router は main.py:48,132 で登録済み。 |
| implication | 実装一致は未測定。設計書と単体テスト仕様を正として学習し、実装は差分の観測対象とする。 |

## teaching_value

### strengths

- 単一画面のマスタメンテとして、検索・新規・複製・修正・削除・CSV の全操作が揃う。
- 3 モード（新規／複製／修正）と削除選択の組合せが、デシジョンテーブルの教材になる。
- 被参照チェック（2 マスタ）・排他・重複・緊急配信が 1 画面に集約されている。
- 設計（12 枚のシート）と単体テスト（216 件）が揃い、設計→テストの写像を学べる。

### cautions

- Create/Copy が未使用の可能性があり、実装の読み方を誤ると学習効果が逆転する（D-MK-10）。
- REG_STS と緊急配信の判定は設計だけでは閉じない（D-MK-05 / D-MK-08）。
- AB 未測定のため、実装を正解として提示しない（D-MK-11）。


## req_ids

## deviations

| id | title | type | evidence | impact | cause | action | machine_detectable | layer | detection_hint |
|---|---|---|---|---|---|---|---|---|---|
| D-MK-01 | 画面項目数が骨架の I-ID 枠（56）と一致しない | design_vs_skeleton | ["画面項目内容(検索)：項目番号 33 件（r15-r51）", "画面項目内容(マスタ項目)：項目番号 9 件（r16-r27）", "骨架の I-201..I-256 は 56 件"] | I-ID を 1 対 1 で対応付けると、検索 33 件・マスタ 9 件のどちらとも合わない。 | 56 は骨架構築時に置いた仮の枠であり、設計書から導いた数ではない。 | R60Maker では I-ID を画面項目数として使わない。I-ID を起こす場合は、設計書の項目番号を source_locator に持つ。 | False | knowledge |  |
| D-MK-02 | ダウンロード処理が検索条件を SQL 文字列へ直接連結している | security | ["R60MakerController.py:817-883 の download は maker_cd / maker_nm を WHERE 句へ文字列連結する。", "同じファイルの search（670-816）は bind パラメータを使っている。"] | 入力値によっては SQL インジェクションが成立し得る。search と download で安全度が異なる。 | 共通 CSV ユーティリティが WHERE 文字列を受け取る設計であり、呼び出し側が値を連結している。 | 実装課題として記録する。download も bind パラメータ化する。設計（D/L）を変える場合は CR を起票する。 | True | gate | WHERE 句の組み立てで f-string / + を使っている箇所を grep する。 |
| D-MK-03 | 削除・登録のレスポンスに完了メッセージが含まれない | design_vs_implementation | ["設計は削除完了時に R60I0002、登録完了時に R60I0001 を表示する（BP r318-r319 / r399-r400）。", "実装の delete は {\"error_code\":\"0\",\"error_id\":\"\"} のみ、edit も同様で msg を返さない（R60MakerController.py:1090-1097 / 1295-1300）。", "フロント側が messageInfo から R60I0002 / R60I0001 を引いて表示する（R60MakerEdit.vue:292 / 354）。"] | 機能上の欠落はないが、API 契約としては設計のメッセージが応答に現れない。 | メッセージ表示をフロントの責務に寄せた実装判断。 | API 契約カード（02-api.yaml）に『実装では未設定、フロントが表示』と明記する。 | True | knowledge | 設計のメッセージ ID と API レスポンス項目を突合する。 |
| D-MK-04 | BaseCamelModel の extra が 'ignore'（骨架規則は 'forbid'） | design_vs_skeleton | ["R60MakerController.py:34-40 は extra=\"ignore\"。", "03-design-coding.md §2 は extra='forbid' を固定としている。"] | 定義外の入力が 422 にならず、静かに無視される。項目追加・改定の検知が弱い。 | 既存案件の実装が骨架規則より先に存在し、骨架規則が実装に合わせられていない。 | R60Maker の知識カードには実装値を記録する。骨架規則を変えるかは人（ユーザー）の裁定事項であり、本カードでは変更しない。 | True | rules | grep 'extra=' で 'ignore' と 'forbid' の混在を検出できる。 |
| D-MK-05 | REG_STS の判定基準が設計書に無く、実装だけが規則を持つ | design_gap | ["項目移送表(DB) r19 は登録ステータス（REG_STS）の画面項目を『共通仕様参照』とだけ書く。", "R60MakerController.py:1311-1320 の set_reg_sts は『コード・日本語名・カナ名の 3 つが非空なら 1』と判定する。"] | 設計書だけを読むと REG_STS を再現できない。仕掛表示（REG_STS='0'）の対象範囲も決まらない。 | 共通仕様が別文書にあり、本設計書へ転記されていない。 | 実装値を記録しつつ、共通仕様の所在を確認するまで『確定規則ではない』と扱う。 | False | knowledge |  |
| D-MK-06 | 複製モードの初期化が元レコードの DEL_FLG / SEND_KBN を返す | design_vs_implementation | ["設計は複製時に『緊急配信はチェックオフ、削除は無』とする（BP r159-r160）。", "実装の initEdit（mode='2'）は元レコードの DEL_FLG と SEND_KBN をそのまま返す（R60MakerController.py:884-978）。", "ただし edit（mode='2'）の INSERT は DEL_FLG='0'、SEND_KBN='0' を固定設定する。"] | 複製画面に元データの削除状態・送信区分が一瞬見える可能性がある。登録結果は設計どおり新規扱い。 | 初期化レスポンスと INSERT で別々の値を組み立てている。 | 画面表示の実害を確認する。API 契約には『複製時の初期化は元値を含む』と注記する。 | True | knowledge | initEdit の mode='2' 分岐が返す項目と、設計の『チェックオフ／削除は無』を比較する。 |
| D-MK-07 | 『廃止_画面項目内容(入力)』シートが設計書に残っている | design_hygiene | ["設計書に『廃止_画面項目内容(入力)』シートがある（項目番号 19 件）。", "現行の入力画面仕様は『画面項目内容(マスタ項目)』（9 件）。"] | どちらを読むかで項目数・必須条件が変わる。RAG が両方を拾うと誤答する。 | シート廃止時に削除せず、名前に『廃止_』を付けて残した。 | RAG の chunk では廃止シートを corpus_scope='holdout' または除外にし、search 対象にしない。 | True | knowledge | シート名の接頭辞『廃止_』を検出する。 |
| D-MK-08 | 削除時の緊急配信対象が『画面初期表示時』と現在値のどちらか一意でない | design_clarity | ["BP r312『画面初期表示時に緊急配信が選択されていた場合、緊急配信を起動する』。", "BP r316 は削除時の送信ステータスを『更新前が 9 なら維持、それ以外は 0』とする。", "実装はリクエストの send_sts を判定に使う（R60MakerController.py:1085-1093）。"] | 画面表示後にチェックを変えた場合、設計の逐語と実装で対象が変わり得る。 | 『初期表示時』という表現が、画面状態を指すのか DB 値を指すのか曖昧。 | 設計へ確認事項として返す。実装値は send_sts による判定として記録する。 | False | knowledge |  |
| D-MK-09 | 概要シートの前提条件・排他条件が『あり』だけで本文が無い | design_gap | ["01_概要 r27-r28：前提条件は『なし／あり』の選択だけ。", "01_概要 r31-r33：排他条件は『なし／あり』の選択と『画面項目間・DB整合チェックシート参照』のみ。"] | 前提条件の本文が無いため、セッション・オンライン制御以外の前提を設計から復元できない。 | 標準様式の欄を埋めたが、本文の転記がされていない。 | 排他条件は 11_画面項目間・DB整合チェック r18（KSN_DAT 比較）を正とする。前提条件は BP r13-r20 を正とする。 | False | knowledge |  |
| D-MK-10 | R60MakerCreate.vue / R60MakerCopy.vue が画面から参照されていない | implementation_structure | ["R60Maker.vue:172 は R60MakerEdit.vue だけを import する。", "R60MakerCreate.vue の入力項目に v-model が無く、メッセージ ID も持たない。", "R60MakerCopy.vue は edit_data.key_001..003 を参照し、削除チェックはコメントアウトされている。", "3 モード分のチェックとダイアログは R60MakerEdit.vue に集約されている。"] | Create/Copy を『現行実装』として読むと、存在しない画面構成を学習する。 | モード統合時に旧コンポーネントを残した可能性が高い（未確認）。 | RAG では Create/Copy を holdout または低重みにし、Edit.vue を現行の真源とする。削除の可否は人が判断する。 | True | knowledge | view の import 一覧と components ディレクトリを突合する。 |
| D-MK-11 | A/B レポートの全端点 404 は『実装欠落』ではない | measurement | ["app/main.py:48,132 で R60MakerController を import し include_router している。", "R60MakerController.py:23 は prefix='/R60Maker'、端点パスは /init・/search・/download・initEdit・/delete・/edit。", "A/B レポートは 8 端点すべて 404。"] | 404 を実装欠落と読むと、実在する実装を『無い』と誤判定する。 | 測定環境でルータが公開されていなかった（未測定）。 | impl_alignment は null（未測定）とする。AB を再実測するまで実装一致を語らない。 | True | knowledge | 404 のときは main.py の include_router と router prefix を必ず確認する。 |
| D-MK-12 | モード値 '1'/'2'/'3' が設計書に書かれていない | design_vs_implementation | ["設計は『新規／複製／修正』という名称でしか書かない。", "実装は mode='1'（新規）、'2'（複製）、'3'（修正）で分岐する（R60MakerController.py:884 以降）。"] | 設計から API を起こすとき、mode の値域を設計だけでは決められない。 | 実装時の内部規約が設計へ反映されていない。 | 02-api.yaml に変換表として記録する。設計へ反映するかは人（ユーザー）の裁定事項。 | True | knowledge | mode の比較値と設計のモード名称を突合する。 |
| D-MK-13 | 標準仕様参照のイベント（No4/No9/No10/No13）に本文が無い | design_gap | ["13_イベント一覧 r17：No4『検索条件部を縮小/拡大表示する』のみ。", "13_イベント一覧 r22-r23, r27：No9/No10/No13 は『標準仕様参照』。", "BP も No4 は『共通処理参照』、No9/No10/No13 は標準仕様の記述に留まる。"] | 戻る・業務終了・条件部トグルの詳細（確認メッセージの有無、遷移先）を本設計書から復元できない。 | 共通仕様が別文書にあり、本設計書へ転記されていない。 | RAG ではこれらを『標準仕様』として弱い根拠に留め、共通仕様の所在を確認するまで断定しない。 | False | knowledge |  |

## review_questions

| question | status | owner | note |
|---|---|---|---|
| download の SQL 連結は許容されているか。 | open | 人（ユーザー） | セキュリティ方針に関わるため、骨架側で勝手に直さない。 |
| extra='ignore' を骨架規則（forbid）へ合わせるのか、規則を実装へ合わせるのか。 | open | 人（ユーザー） | migration 案件固有の実装と greenfield の既定規則が衝突している。 |
| REG_STS の共通仕様はどこにあるか。3 項目非空で '1' という実装規則は正か。 | open | 人（ユーザー） | 仕掛表示の対象範囲に直結する。 |
| 削除時の緊急配信は『画面初期表示時の値』と『現在のチェック状態』のどちらで判定するか。 | open | 人（ユーザー） | 設計の逐語と実装が食い違う可能性がある。 |
| R60MakerCreate.vue / R60MakerCopy.vue は廃止予定か、将来使うのか。 | open | 人（ユーザー） | RAG の teaching/holdout の振り分けに影響する。 |

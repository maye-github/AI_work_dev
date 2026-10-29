---
id: KNOW-LEGACY-R60-MODULE-R60SSK-TESTS-VIEW
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-modules-r60ssk-05-tests
scope: project
project_id: P-R60-001
title: R60Ssk — 単体テスト観点
doc_type: design-detail
conf_level: 30
updated_at: '2026-10-28'
---

# R60Ssk — 単体テスト観点

> 正本は同ディレクトリの `05-tests.yaml`。本ファイルは検索用の可読表現であり、
> 手で編集しない（`py -3 -m tools.kb_migrate --apply` で作り直す）。

| 項目 | 値 |
|---|---|
| id | KNOW-LEGACY-R60-MODULE-R60SSK-TESTS |
| type | knowledge |
| status | draft |
| sensitivity | internal |
| owner | AI-SE |
| version | 0.1.0 |
| traceability_note | 旧テスト仕様の大項目・中項目番号は骨架の TC-xxx ではない。 RAG では「設計 → テスト観点」の検索に使うが、ids.yml への発号は行わない。 TC-xxx を起こす場合は、本ファイルの viewpoint_mapping を観点の出所として design_ids / req_ids を別途付与する（红线⑤）。 |

## summary

| 項目 | 値 |
|---|---|
| program_id | R60Ssk |
| program_name | 部署マスタメンテナンス |
| fp | 13 |
| total_test_items | 146 |
| bugs | 0 |

## test_item_counts

| 項目 | 値 |
|---|---|
| screen_transition | 4 |
| total_check | 4 + 48 + 15 + 69 + 10 = 146 |

### screen_layout

| 項目 | 値 |
|---|---|
| search_condition | 17 |
| search_result | 20 |
| master_modify | 11 |
| subtotal | 48 |

### input_check

| 項目 | 値 |
|---|---|
| display | 7 |
| register | 6 |
| back | 1 |
| business_end | 1 |
| subtotal | 15 |

### event

| 項目 | 値 |
|---|---|
| initial_display | 18 |
| company_change | 4 |
| unit_search_icon | 1 |
| display_button | 12 |
| condition_toggle | 1 |
| back_button | 3 |
| business_end | 1 |
| download | 6 |
| result_link | 9 |
| page_move | 5 |
| sort | 6 |
| accounting_company_change | 2 |
| register_button | 1 |
| subtotal | 69 |

### special

| 項目 | 値 |
|---|---|
| permission_search_result | 0 |
| permission_master | 6 |
| permission_value_change | 0 |
| exception | 4 |
| module_specific | 0 |
| subtotal | 10 |


## viewpoint_mapping

| 項目 | 値 |
|---|---|
| note | 旧単体テスト仕様は「正常/境界/異常」の分類を持たない。 骨架の 正常3/境界2/異常3 へ写像するときは、下記の読み替えを使う。 |

### equivalence_partition

- 検索条件：会社あり／なし、組織ユニットあり／なし、正式名称あり／なし
- 組織ユニットの文字種：半角英数字・半角数字・全角・記号
- 経理用会社／経理用事業場：両方あり・両方なし・片方のみ
- 権限区分：Y / それ以外

### boundary_value

- 組織ユニット 8 文字（8 OK / 9 NG）
- 正式名称 40byte（40 OK / 41 NG）
- 検索上限件数（上限ちょうど OK / 上限+1 NG）
- ページ：先頭頁・最終頁・総頁超過

### decision_table

- 登録：変更なし／経理用会社のみ／経理用事業場のみ／両方あり × 排他一致／不一致
- 登録ステータス：会社・組織ユニット・事業場組織ユニット・正式名称の未設定組合せ
- ボタン活性：検索 0 件／1 件以上 × 戻る・ダウンロード・新規
- 経理用会社変更：ブランク／選択済 × 選択行の経理事業場あり／なし


## teaching_value

### strengths

- 146 件のテスト項目が 5 分類（遷移・レイアウト・入力・イベント・特殊）で整理され、分類ごとの件数が追える。
- 検索条件・結果・マスタ修正の 3 画面構成で、画面遷移テストの最小形を学べる。
- 『登録』が更新のみであることを、テスト項目（削除・新規が無い）からも確認できる。

### cautions

- 個別ケース本文が未抽出のため、件数以上の網羅性は語れない。
- 登録イベントのテスト項目が 1 件と少なく、件数だけでは設計のチェック項目を覆っているか判断できない。


## req_ids

## observations

- 設計のイベントは 16 件、テストの中項目は 13 件である。テストはソート 3 種類を『一覧項目ソートアイコンクリック』1 項目にまとめ、戻る系を統合している。
- 登録ボタンクリック（マスタ項目）のテスト項目数は 1。参照先は『4.登録機能』シートで、概要の件数だけでは網羅度を判断できない。
- 権限のテストは『マスタ画面表示時』6 件のみ。検索条件・結果画面と画面項目値変更時は 0 件。
- 例外は 4 件。設計の例外処理列はイベント No1 / No14 にしか無い。

## key_test_cards

| area | test_items | checks | viewpoint | design_locator |
|---|---|---|---|---|
| 画面遷移 | 4 | ["組織ユニット検索ボタンで一覧型入力支援(組織ユニット)が起動する。", "入力支援の OK／キャンセルで本画面に戻る。", "一覧データリンクでマスタ項目画面(修正)が起動し、登録・戻るで本画面に戻る。", "業務終了ボタンで本画面が閉じる。"] | 同値分割 | 12_イベント一覧 r14-r30 |
| 画面レイアウト | 48 | ["検索条件画面 17 件・検索結果画面 20 件・マスタ項目画面(修正) 11 件。", "項目の表示/非表示、初期値、活性/非活性を確認する。"] | 同値分割 |  |
| 入力チェック（表示） | 7 | ["会社必須（R60W0009）。", "組織ユニットの文字種・8 文字（R60W0106）。", "正式名称の文字種・40byte（R60W0131）。"] | 同値分割 + 境界値 |  |
| 入力チェック（登録） | 6 | ["変更なし（R60W0016）。", "経理用会社・経理用事業場のセット（R60W2002）。", "排他（R60W0006）。"] | 同値分割 + デシジョンテーブル |  |
| イベント（検索） | 18 + 4 + 12 + 5 + 6 + 1 = 46 | ["初期表示で会社・1 頁件数・メッセージが設定される。", "会社変更で組織ユニットの入力可否と検索アイコンの活性が変わる。", "表示で条件・ソート・ページング・ボタン活性が正しい。", "ページ移動とソートで一覧が更新される。"] | 同値分割 + 境界値 + デシジョンテーブル |  |
| イベント（マスタ項目） | 9 + 2 + 1 = 12 | ["一覧リンクで修正モードが起動し、選択行が表示される。", "経理用会社変更で経理用事業場リストが再作成される。", "登録で UPDATE され、完了メッセージが表示される。"] | デシジョンテーブル |  |
| 特殊処理 | 10 | ["マスタ画面表示時の権限 6 件。", "例外 4 件（セッション・オンライン・システム）。"] | デシジョンテーブル |  |

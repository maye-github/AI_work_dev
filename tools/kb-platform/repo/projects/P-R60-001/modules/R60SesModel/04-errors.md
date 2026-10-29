---
id: KNOW-LEGACY-R60-MODULE-R60SESMODEL-ERRORS-VIEW
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-modules-r60sesmodel-04-errors
scope: project
project_id: P-R60-001
title: R60SesModel — エラー一覧
doc_type: design-detail
conf_level: 30
updated_at: '2026-10-29'
---

# R60SesModel — エラー一覧

> 正本は同ディレクトリの `04-errors.yaml`。本ファイルは検索用の可読表現であり、
> 手で編集しない（`py -3 -m tools.kb_migrate --apply` で作り直す）。

| 項目 | 値 |
|---|---|
| id | KNOW-LEGACY-R60-MODULE-R60SESMODEL-ERRORS |
| type | knowledge |
| status | open |
| sensitivity | internal |
| owner | AI-SE |
| version | 0.1.0 |

## message_inventory

| 項目 | 値 |
|---|---|
| mismatch | 設計 8＋33、実装 fetch 36・参照 37。完全一致しない。 『その他メッセージ』だけを見て実装を照合すると、チェック系文言の欠落を見落とす（D-SM-03）。 |

### design_other_messages

| 項目 | 値 |
|---|---|
| rows | 13 |
| note | ヘッダ・明細で同じ ID を繰り返すため、行数 13 に対し ID は 8。 |

#### distinct_ids

- R60A0008
- R60A0021
- R60I0022
- R60I0001
- R60I0002
- R60A0003
- R60A0004
- R60W0007


### design_check_sheets

| 項目 | 値 |
|---|---|
| distinct_ids | 33 |
| note | 単項目 29 件・項目間 36 件のチェックが参照するメッセージを数えると 33 ID。 『その他メッセージ』8 ID と合わせても、チェック系の文言はそちらに集約されていない。 |

### implementation_fetch

| 項目 | 値 |
|---|---|
| count | 36 |
| from | R60SesModelController.py get_message_info:4639-4723 |

### implementation_reference

| 項目 | 値 |
|---|---|
| count | 37 |
| extra | R60W0001（dataInit:2305） |
| gap | R60W0001 は fetch されない（D-SM-10）。 |


## message_types

| 項目 | 値 |
|---|---|
| I | 情報（完了） |
| A | 確認（Yes/No） |
| W | 警告（処理中断または注意） |
| E | エラー（共通部品・DB 異常） |

## error_flow

### search

- 0 件 → R60W0010（error_code='1'）
- 上限超過 → R60W0005（total・max_count 付き）

### init_edit

- 対象なし → header_data を空で返す（エラーにしない）

### edit_new

- W0009 / W0016 / W0103 / W0131 / W0012 / W0015 → W0011 → W0032 → W2019(flg=2) → W0014 → W2051

### edit_modify

- W0006 → W0011 → W2019(flg=3) → E0025 / W0018 → W2007 → W2051 → W0017 / W0020

### delete

- W0010 → W0006 → W2019(flg=2) → W2007 → W2051 → W0017(flg=1)

### edit_child_new

- W0019 → W0011 → W2050 → W2019 → W0014

### edit_child_modify

- W0018 / E0025 → W0011 → W0006 → W2019

### delete_child

- W0011 → W0006 → W2019(flg=3)

### data_init

- sim_kbn='0' → R60W0001（ただし message_info に無い）


## error_flg_semantics

| 項目 | 値 |
|---|---|
| R60W0011 | 1=アイテム, 2=半製品, 3=購入品目 |
| R60W0017 | 1=親子, 2=生産/工場 |
| R60W2019 | 1=枯渇, 2=イベント(登録時), 3=イベント(削除/修正時) |
| note | 同じ警告 ID でも画面が文言を差し替えるため、error_flg が必須。 |

## design_vs_implementation

### matched

- W0006 / W0011 / W0014 / W2019 / W2007 / W2051 / W0017 の発火位置は設計の処理順と一致。
- error_flg の意味も応答モデルの説明と一致。

### divergent

- 更新系は message_id を返さず、フロントが R60I0001 / R60I0002 を固定表示する（D-SM-23）。
- dataInit は R60I0022 を返さない（画面が自前で表示）。
- R60W0001 を fetch しない（D-SM-10）。

### design_defects

- W0005 の文言が上限値 3000/3001 を直書きしている。上限は情報ID 000000024 で変わる。
- 単項目 No8 半製品名称は本文 30byte・メッセージ引数 40 で食い違う（D-SM-18）。


## req_ids

## messages

| id | type | role | design_sheet | impl | fetched | note | error_flg |
|---|---|---|---|---|---|---|---|
| R60W0001 | W | 通常環境でのデータ初期化拒否 | なし | dataInit:2305 | False |  |  |
| R60W0005 | W | 検索上限超過 | 18_項目間 | search:2051 | True | 文言に 3000/3001 を直書き |  |
| R60W0006 | W | 排他エラー（更新日時不一致） | 18_項目間 | 各更新・削除 | True |  |  |
| R60W0007 | W | 画面を閉じる時の破棄確認 | 17_単項目 | 各モーダル close | True |  |  |
| R60W0009 | W | 必須項目 | 17_単項目 | inputCheck | True |  |  |
| R60W0010 | W | 検索結果 0 件 | 18_項目間 | search:2049 / delete:3362 | True |  |  |
| R60W0011 | W | 親コード・子コードが存在しない | 18_項目間 | 各更新・削除 | True |  |  |
| R60W0012 | W | 緊急配信時の必須項目 | 17_単項目 | inputCheck（ヘッダ） | True |  |  |
| R60W0014 | W | 重複キー | 18_項目間 | edit / editChild | True |  |  |
| R60W0015 | W | 削除チェック時の必須項目 | 17_単項目 | inputCheck | True |  |  |
| R60W0016 | W | 変更がない | 17_単項目 | inputCheck | True |  |  |
| R60W0017 | W | 関連データの必須（親子・生産工場） | 18_項目間 | edit / delete | True |  | 1=親子, 2=生産工場 |
| R60W0018 | W | 復活時に未復活の関連がある | 18_項目間 | edit / editChild | True |  | 1-3 で対象を切替 |
| R60W0019 | W | 親が削除済み | 18_項目間 | editChild | True |  |  |
| R60W0020 | W | 緊急配信に関する必須（明細） | 18_項目間 | edit（明細確認） | True |  |  |
| R60W0031 | W | 子コードの先頭が親番と不一致 | 17_単項目 | 編集画面 inputCheck | True |  |  |
| R60W0032 | W | 複製元に子コードが無い | 18_項目間 | edit（複製） | True |  |  |
| R60W0101 | W | 未確認（画面側の使用箇所が薄い） | 未確認 | fetch のみ | True |  |  |
| R60W0102 | W | 未確認（コード桁系と推測） | 未確認 | fetch のみ | True |  |  |
| R60W0103 | W | 生産モデルコードの桁不正 | 17_単項目 | searchChk / inputCheck | True |  |  |
| R60W0108 | W | 購入品目コードは 6 桁 | 17_単項目 | searchChk | True |  |  |
| R60W0118 | W | アイテム名称は全角 20 桁 | 17_単項目 | searchChk | True |  |  |
| R60W0121 | W | 所要量・基準値の数値範囲 | 17_単項目 | inputCheck | True |  |  |
| R60W0131 | W | 名称の桁不正 | 17_単項目 | searchChk / inputCheck | True |  |  |
| R60W2007 | W | 緊急配信対象に有効な明細が無い | 18_項目間 | edit / delete | True |  |  |
| R60W2019 | W | イベントマスタ参照エラー | 18_項目間 | 各更新・削除・自動採番枯渇 | True |  | 1=枯渇, 2=イベント(登録), 3=イベント(削除/修正) |
| R60W2050 | W | 飲料社工場ユーザーが非素材の購入品目を選択 | 18_項目間 | editChild / delete | True |  |  |
| R60W2051 | W | 子マスタが未確定（REG_STS='0'） | 18_項目間 | edit / delete | True |  |  |
| R60E0023 | E | 未確認（共通部品異常系と推測） | 未確認 | fetch のみ | True |  |  |
| R60E0025 | E | 共通チェック関数が null を返した | 18_項目間 | edit / editChild | True |  |  |
| R60A0003 | A | 登録・更新の確認 | 19_その他 | 登録前確認 | True |  |  |
| R60A0004 | A | 削除の確認 | 19_その他 | 削除前確認 | True |  |  |
| R60A0008 | A | 確認（用途未確認） | 19_その他 | fetch のみ | True |  |  |
| R60A0021 | A | 確認（用途未確認） | 19_その他 | fetch のみ | True |  |  |
| R60I0001 | I | 登録・更新完了 | 19_その他 | フロントが固定表示 | True |  |  |
| R60I0002 | I | 削除完了 | 19_その他 | フロントが固定表示 | True |  |  |
| R60I0022 | I | データ初期化完了 | 19_その他 | dataInit は返さずフロントが表示 | True |  |  |

## open_questions

- R60W0101 / R60W0102 / R60E0023 / R60A0008 / R60A0021 の正式な用途。
- R60W0001 を init の message_info に含めない理由。
- 更新系 API が message_id を返さないのは設計か実装の簡略化か。
- W0005 の文言 3000/3001 と情報ID 000000024 の現在値の関係。

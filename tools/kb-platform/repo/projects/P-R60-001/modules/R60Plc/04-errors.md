---
id: KNOW-LEGACY-R60-MODULE-R60PLC-ERRORS-VIEW
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-modules-r60plc-04-errors
scope: project
project_id: P-R60-001
title: R60Plc — エラー一覧
doc_type: design-detail
conf_level: 30
updated_at: '2026-10-29'
---

# R60Plc — エラー一覧

> 正本は同ディレクトリの `04-errors.yaml`。本ファイルは検索用の可読表現であり、
> 手で編集しない（`py -3 -m tools.kb_migrate --apply` で作り直す）。

| 項目 | 値 |
|---|---|
| id | KNOW-LEGACY-R60-MODULE-R60PLC-ERRORS |
| type | knowledge |
| status | open |
| sensitivity | internal |
| owner | AI-SE |
| version | 0.1.0 |

## message_inventory

| 項目 | 値 |
|---|---|
| fetched_at_init | 20 |
| used_in_design | 19 |

### unused

- R60W0013

### returned_by_backend_but_not_shown

- R60I0002


## message_types

| 項目 | 値 |
|---|---|
| R60W | 警告・入力チェック（処理を止める） |
| R60A | 確認ダイアログ（OK/キャンセル） |
| R60I | 完了通知 |
| R60E | システムエラー |

## design_vs_implementation

### matched

- 入力チェック・検索・DB整合のメッセージ割当
- 確認ダイアログのタイミング

### mismatched

- R60I0002 が画面に到達しない
- R60W0013 が未使用のまま取得されている


## req_ids

## messages

| id | type | category | trigger | timing | design_locator | implemented | note | function | deviation |
|---|---|---|---|---|---|---|---|---|---|
| R60W0128 | warning | 単項目 | ロケーションコードの形式不正（半角英数大文字と _ - ( ) 以外、または 8 桁超） | 項目から焦点が外れた時・登録時 | 09_画面単項目チェック | True |  |  |  |
| R60W0131 | warning | 単項目 | ロケーション名称が 24 桁超、または略称が 16 桁超 | 焦点喪失時・登録時 | 09_画面単項目チェック | True |  |  |  |
| R60W0121 | warning | 単項目 | 最大容量・最大深さ・開始検定深さ等の数値範囲外 | 焦点喪失時・登録時 | 09_画面単項目チェック | True |  |  |  |
| R60W0009 | warning | 単項目 | 新規・複製時に必須項目が未入力 | 登録時 | 09_画面単項目チェック | True |  |  |  |
| R60W0015 | warning | 単項目 | 削除チェック時に削除に必要な項目が未入力 | 登録時 | 09_画面単項目チェック | True |  |  |  |
| R60W0016 | warning | 単項目 | 前回読込時から変更が無い | 登録時 | 09_画面単項目チェック | True |  |  |  |
| R60W0010 | warning | 検索 | 検索結果が 0 件 | 仕掛表示・表示・ページ移動・ソート | 10_画面項目間・DB整合チェック | True |  |  |  |
| R60W0005 | warning | 検索 | 件数が上限を超過 | 検索時 | 10_画面項目間・DB整合チェック | True | 上限値は情報ID 000000024。超過時は一覧を描画しない。 |  |  |
| R60W0014 | warning | DB整合 | 同一業務キー（CMP_CD+JIG_CD+PLC_CD）が既存 | 新規・複製の登録時 | 10_画面項目間・DB整合チェック | True | DEL_FLG を見ないため、削除済みキーでも重複になる。 |  |  |
| R60W0006 | warning | DB整合 | 排他エラー（KSN_DAT 不一致） | 修正・削除の登録時 | 10_画面項目間・DB整合チェック | True |  |  |  |
| R60W0024 | warning | DB整合 | 他情報から参照されているため削除不可 | 削除時・削除チェック付き登録時 | 10_画面項目間・DB整合チェック | True |  | R60_CHECK_PLC_INFO_FNC |  |
| R60E0025 | error | DB整合 | 被参照チェック関数が null を返す | 削除時・削除チェック付き登録時 | 10_画面項目間・DB整合チェック | True |  |  |  |
| R60W0007 | warning | 確認 | 変更を破棄してよいか | 戻る・閉じる・モーダルを閉じる時 | 09_画面単項目チェック | True |  |  |  |
| R60A0004 | confirm | 確認 | 削除してよいか | 削除ボタン | 11_その他メッセージ | True |  |  |  |
| R60A0003 | confirm | 確認 | 登録してよいか | 登録ボタン | 11_その他メッセージ | True |  |  |  |
| R60A0008 | confirm | 確認 | 必須項目の確認 | 登録時 | 11_その他メッセージ | True |  |  |  |
| R60A0041 | confirm | 確認 | 必須項目確認（OK で登録続行） | 登録時 | 10_画面項目間・DB整合チェック | True | 確認ダイアログのため、キャンセルで処理を中止する。 |  |  |
| R60I0001 | info | 完了 | 登録・削除の完了 | edit 成功時、および delete 成功時（フロント固定表示） | 11_その他メッセージ | True |  |  | 削除でも R60I0001 を表示する（設計は R60I0002）。 |
| R60I0002 | info | 完了 | 削除の完了 | delete 成功時（バックエンドが返す） | 11_その他メッセージ | partial |  |  | 取得・返却はあるが、フロントは表示しない。 |
| R60W0013 | warning | 未使用 | 設計シートに記述が無い | なし |  | False | init の message_info に含めて取得しているが、設計 3 シートおよび フロント・バックエンドのいずれにも使用箇所が無い。 |  |  |

## error_flow

| stage | messages | on_error |
|---|---|---|
| 単項目チェック | ["R60W0128", "R60W0131", "R60W0121", "R60W0009", "R60W0015", "R60W0016"] | 項目にフォーカスを戻し、処理を中止する。 |
| 検索 | ["R60W0010", "R60W0005"] | 一覧を描画しない。 |
| 登録前チェック | ["R60W0014", "R60W0006", "R60W0024", "R60E0025", "R60A0041"] | 処理を中止する。A0041 はキャンセルで中止、OK で続行。 |
| 完了 | ["R60I0001", "R60I0002"] | なし（通知のみ）。 |

## open_questions

- R60I0002 を表示するのが正しいか、登録と同じ R60I0001 が正しいか。
- R60W0013 はどの操作を想定したメッセージか（設計から読み取れない）。

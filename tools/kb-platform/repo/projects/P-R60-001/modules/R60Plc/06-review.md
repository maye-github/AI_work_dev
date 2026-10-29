---
id: KNOW-LEGACY-R60-MODULE-R60PLC-REVIEW-VIEW
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-modules-r60plc-06-review
scope: project
project_id: P-R60-001
title: R60Plc — レビュー指摘と処置
doc_type: design-detail
conf_level: 30
updated_at: '2026-10-29'
---

# R60Plc — レビュー指摘と処置

> 正本は同ディレクトリの `06-review.yaml`。本ファイルは検索用の可読表現であり、
> 手で編集しない（`py -3 -m tools.kb_migrate --apply` で作り直す）。

| 項目 | 値 |
|---|---|
| id | KNOW-LEGACY-R60-MODULE-R60PLC-REVIEW |
| type | knowledge |
| status | open |
| sensitivity | internal |
| owner | AI-SE |
| version | 0.1.0 |

## scope

| 項目 | 値 |
|---|---|
| design_sheets | 01, 06, 08, 09, 10, 11, 12, 13, 14, 15 |
| frontend | R60PlcService.ts / R60Plc.vue / R60PlcEdit.vue / R60PlcCreate.vue / R60PlcCopy.vue |
| backend | R60PlcController.py |
| tests | 00_単体ﾃｽﾄ仕様兼結果.txt / 01_1.画面遷移.txt |
| ab_report | doc/03_AI/AB_Reports/reports/R60Plc/summary.md |

## finding_summary

| 項目 | 値 |
|---|---|
| total | 16 |
| design_internal | 5 |
| design_vs_implementation | 6 |
| implementation_only | 3 |
| survey_or_ab | 2 |

### severity

#### high

- D-PL-07
- D-PL-08
- D-PL-09

#### medium

- D-PL-06
- D-PL-10
- D-PL-11
- D-PL-12
- D-PL-15
- D-PL-16

#### low

- D-PL-01
- D-PL-02
- D-PL-03
- D-PL-04
- D-PL-05
- D-PL-13
- D-PL-14



## teaching_notes

### reusable_patterns

- 検索一覧＋マスタ項目モーダルの 3 モード（新規・複製・修正）
- 複合キーをカンマ連結したドロップダウン value
- 件数 0 / 上限超過を検索結果として扱う
- 排他 → 被参照 → 更新の順序
- 論理削除（DEL_FLG=1）と 33 列 UPDATE
- REG_STS を必須項目の充足で判定する（18＋条件付き 6）

### anti_patterns

- 設計の『表示＝確定のみ』と実装の不一致（D-PL-07）
- 応答メッセージを無視して固定文言を出す（D-PL-08）
- search と download で SQL の組み立て方式が違う（D-PL-09）
- Enabled という名前で disabled を制御する（D-PL-15）
- 死んだコンポーネントを残す（D-PL-16）


## req_ids

## deviations

| id | title | category | severity | finding | evidence | impact | treatment |
|---|---|---|---|---|---|---|---|
| D-PL-01 | 画面項目数の数え方（見出し行の混入） | survey | low | 検索シートの No は最大 69、マスタ項目シートは最大 40 だが、 いずれも節見出し行（検索 4 行、マスタ 3 行）を含む。実際の項目は 65＋37＝102。 | ["06_画面項目内容(検索): No1-69、節行 [1,7,21,65]", "08_画面項目内容(マスタ項目): No1-40、節行 [1,3,37]"] | 項目数を No の最大値で数えると 109 になり、102 より 7 多い。 | 本カードは実項目 102 を採る。 |
| D-PL-02 | 調査票の『endpoints 11』は端点ではなく API 呼出イベント数 | survey | low | reports/module-survey/scores/R60Plc.yaml は endpoints=11 と記録するが、 @router.post は 6 件、Service メソッドも 6 件。24 イベントのうち API を呼ぶものは 13 件、呼ばないものが 11 件であり、11 は後者に一致する。 | ["R60PlcController.py: 6 端点", "R60PlcService.ts: 6 メソッド", "event_to_endpoint_map: api_triggering_events=13 / non_api_events=11"] | 複雑度スコアの端点シグナルが約 2 倍に見える。 | 本カードは実測 6 を採る。 |
| D-PL-03 | 業務処理説明のイベント番号が見出しと本文でずれる | design_internal | low | 13_業務処理説明 の見出しは No12（複製）・No13（一覧リンク）・No17（新規）だが、 本文中では同じ処理を No11・No12・No16 と書く箇所がある。 | ["13_業務処理説明: 見出しと本文の番号差", "12_イベント一覧: 複製=No12、一覧リンク=No13、新規=No17"] | イベント番号で設計を参照すると 1 件ずれる。 | 12_イベント一覧 を正とする。 |
| D-PL-04 | 業務処理説明の処理番号が重複 | design_internal | low | 13_業務処理説明 に (5) と (10) が 2 回ずつ現れ、処理順序を番号で追えない。 | ["13_業務処理説明: (5)・(10) の重複"] | 処理順の参照が曖昧になる。 | 番号ではなく処理名で参照する。 |
| D-PL-05 | マスタ項目シートのコピー＆ペースト誤り 3 件 | design_internal | low | ["No8 エリアの初期値が『一覧で選択されたデータの事業場』（エリアではない）。", "No24 開始検定深さの初期値が『一覧で選択されたデータの最大深さ』（開始検定深さではない）。", "No34 削除のエンティティが『エリアマスタ／論理削除フラグ』（ロケーションマスタではない）。"] | ["08_画面項目内容(マスタ項目): No8 / No24 / No34"] | 初期値と削除対象を取り違えると、別テーブルを更新する設計になる。 | 実装（R60PlcEdit.vue / R60PlcController.py）を事実として併記し、設計の誤りを記録する。 |
| D-PL-06 | タンク判定の表記が『2』と『02』で揺れる | design_internal | medium | 13_業務処理説明 と 08_画面項目内容(マスタ項目) で、ロケーション属性区分の タンク判定を『2』と書く箇所と『02』と書く箇所がある。実装は '02' で判定する。 | ["13_業務処理説明: 『2:タンク』表記", "R60PlcController.py set_reg_sts: plc_zks_kbn == '02'"] | 実装が '2' で判定するとタンク条件が外れ、6 項目の必須チェックが効かない。 | 実装 '02' を事実とし、設計の統一を未確定事項に残す。 |
| D-PL-07 | 表示ボタンが REG_STS=1 で絞らない | design_vs_implementation | high | 設計 13_業務処理説明 は『表示は登録ステータス＝確定のデータを表示』と書くが、 実装は search_btn='0'（仕掛表示）の時だけ REG_STS=0 を加え、 search_btn='1'（表示）では REG_STS を条件に加えない。 | ["13_業務処理説明: 表示の絞り込み記述", "R60PlcController.py search: search_btn == '0' の分岐のみ", "R60Plc.vue runSearch('0') / runSearch('1')"] | 表示ボタンで未確定データが一覧に現れる。設計の意図と業務の見え方が変わる。 | 設計と実装のどちらが正かは未確定。RAG では両方を併記する。 |
| D-PL-08 | 削除完了メッセージが設計と実装で異なる | design_vs_implementation | high | バックエンド delete は成功時に R60I0002（削除しました。）を返すが、 フロントは応答メッセージを表示せず、常に R60I0001（登録しました。）を表示する。 | ["R60PlcController.py delete: error_id=R60I0002", "R60PlcEdit.vue deleteDialog: R60I0001 を固定表示", "11_その他メッセージ: R60I0002=削除完了"] | 削除したのに『登録しました』と出る。利用者に誤解を与える。 | 設計 R60I0002 が正。実装の不具合候補として記録する。 |
| D-PL-09 | ダウンロードの WHERE 句を文字列連結で組み立てる | implementation_only | high | search は bind 変数で条件を組むが、download は同じ条件を文字列連結で SQL に埋め込む。 入力値は画面由来だが、search と方式が異なり、SQL 断片の混入面が広い。 | ["R60PlcController.py download: WHERE 文字列連結", "R60PlcController.py search: bind 変数"] | 設計の白名单・bind 原則（03-design-coding.md §5）から外れる。 | 骨架の製造細則では bind 必須。移行案件では既存実装の事実として記録。 |
| D-PL-10 | 指定ソート時に副キーが落ちる | design_vs_implementation | medium | 設計は『DEL_FLG・CMP_CD・JIG_CD・PLC_CD 昇順』を既定とし、 指定ソートでも副キーを保つと読める。実装は指定時に ORDER BY DEL_FLG, {指定列} {ASC\|DESC}, ROWID となり、他のキーが落ちる。 | ["13_業務処理説明 r107-r112", "R60PlcController.py ALLOWED_SORT_FIELDS / order by 組み立て"] | 同値行の並びが設計と変わる。ページング時の順序安定性は ROWID で担保。 | 実装を事実として記録。設計の副キー意図は未確定。 |
| D-PL-11 | Pydantic モデルが extra='ignore' | implementation_only | medium | SearchParams / InitEditParams 等は BaseCamelModel を継承するが、 extra='ignore' を指定する。骨架規則の extra='forbid'（03-design-coding.md §2）と異なる。 | ["R60PlcController.py: class SearchParams ... extra='ignore'", ".claude/rules/03-design-coding.md §2"] | 定義外の入力が 422 にならず静黙無視される。項目追加・改定の検知が弱い。 | 移行案件の既存事実として記録。骨架の既定は forbid のまま変更しない。 |
| D-PL-12 | 未使用メッセージ R60W0013 と、表示されない R60I0002 | implementation_only | medium | init は 20 件のメッセージを取得するが、R60W0013 は設計 3 シートにも フロント・バックエンドにも使用箇所が無い。R60I0002 は delete が返すが画面に出ない。 | ["R60PlcController.py init: message_info 20 件", "R60PlcEdit.vue: R60I0002 の表示分岐なし"] | メッセージ定義と画面挙動が一対一でない。 | D-PL-08 と併せて記録。 |
| D-PL-13 | A/B レポートは head のみ測定 | ab_report | low | doc/03_AI/AB_Reports/reports/R60Plc/summary.md は ✅ 0 件・🔷 1 件（head）・⏭️ 2 件（modify / download は SKIP）。 差分比較は画面ヘッダの構造一致までで、修正・ダウンロードは未測定。 | ["doc/03_AI/AB_Reports/reports/R60Plc/summary.md"] | 実装一致の証拠は検索画面の構造のみ。登録・削除・DL は未検証。 | RAG では『A/B 未測定』を明示し、実装一致と断定しない。 |
| D-PL-14 | DB カラム数 41 と調査票 42 の不一致 | survey | low | 15_項目移送表(DB) の実列は No1-41 の 41 列。調査票は 42 カラムと記録する。 | ["15_項目移送表(DB): No1-41", "reports/module-survey/scores/R60Plc.yaml: columns=42"] | カラム数で実装を照合すると 1 列余る。 | 本カードは 41 を採る。 |
| D-PL-15 | ボタン活性フラグの名前と意味が反転 | implementation_only | medium | R60PlcEdit.vue のフラグは deleteBtnEnabled / registBtnEnabled という名前だが、 テンプレートでは disabled 属性へバインドされている。true が『非活性』を意味する。 | ["R60PlcEdit.vue: :disabled=\"...Enabled\"", "deleteBtnEnabled=true が新規・複製・削除済みで設定される"] | 名前から活性と読むと挙動を逆に理解する。レビュー時の誤読源。 | 実装の事実として記録。骨架の製造では名前と意味を一致させる。 |
| D-PL-16 | 参照されていないコンポーネント R60PlcCreate.vue / R60PlcCopy.vue | implementation_only | medium | 新規用 R60PlcCreate.vue（917 行）と複製用 R60PlcCopy.vue（960 行）が存在するが、 どちらも import されていない。画面は R60PlcEdit.vue（1819 行）1 本で 3 モードを担う。 | ["R60Plc.vue:166 は R60PlcEdit のみ import", "R60PlcCreate.vue / R60PlcCopy.vue: 参照なし"] | 死んだコードが 1,877 行。修正時にどれを直すか誤る危険がある。 | 実装の事実として記録。移行時は Edit 1 本を正とする。 |

## design_internal_inconsistencies

- 13_業務処理説明 のイベント番号（D-PL-03）
- 13_業務処理説明 の処理番号重複（D-PL-04）
- 08_画面項目内容(マスタ項目) の初期値・エンティティ誤り（D-PL-05）
- タンク判定の 2 / 02 表記ゆれ（D-PL-06）
- 14_廃止_画面項目内容(入力) に R60Maker の項目が残存（19 件）

## open_questions

- D-PL-07 は設計と実装のどちらが正か。
- D-PL-10 の副キーは設計意図か、実装の簡略化か。
- R60W0013 の想定用途。
- タンク属性の正式値（2 / 02）。

---
id: KNOW-LEGACY-R60-MODULE-R60SESMODEL-REVIEW-VIEW
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-modules-r60sesmodel-06-review
scope: project
project_id: P-R60-001
title: R60SesModel — レビュー指摘と処置
doc_type: design-detail
conf_level: 30
updated_at: '2026-10-28'
---

# R60SesModel — レビュー指摘と処置

> 正本は同ディレクトリの `06-review.yaml`。本ファイルは検索用の可読表現であり、
> 手で編集しない（`py -3 -m tools.kb_migrate --apply` で作り直す）。

| 項目 | 値 |
|---|---|
| id | KNOW-LEGACY-R60-MODULE-R60SESMODEL-REVIEW |
| type | knowledge |
| status | draft |
| sensitivity | internal |
| owner | AI-SE |
| version | 0.1.0 |

## scope

| 項目 | 値 |
|---|---|
| design_sheets | 01, 06, 10, 12, 16, 17, 18, 19, 20, 21, 22-33 |
| frontend | R60SesModelService.ts / R60SesModel.vue / R60SesModelEdit.vue / R60SesModelMesEdit.vue |
| backend | R60SesModelController.py |
| tests | 00_単体ﾃｽﾄ仕様兼結果.txt / 01_1.画面遷移.txt |
| ab_report | なし（impl_alignment=null） |

## finding_summary

| 項目 | 値 |
|---|---|
| total | 24 |

### by_category

#### survey

- D-SM-01
- D-SM-14
- D-SM-15

#### design_internal

- D-SM-02
- D-SM-11
- D-SM-12
- D-SM-13
- D-SM-16
- D-SM-17
- D-SM-18
- D-SM-22

#### design_vs_implementation

- D-SM-03
- D-SM-06
- D-SM-07
- D-SM-08
- D-SM-21
- D-SM-23

#### implementation_only

- D-SM-04
- D-SM-05
- D-SM-09
- D-SM-10
- D-SM-19
- D-SM-20
- D-SM-24


### severity

#### high

- D-SM-05
- D-SM-14

#### medium

- D-SM-01
- D-SM-02
- D-SM-03
- D-SM-04
- D-SM-07
- D-SM-10
- D-SM-12
- D-SM-16
- D-SM-17
- D-SM-18
- D-SM-20
- D-SM-21
- D-SM-23
- D-SM-24

#### low

- D-SM-06
- D-SM-08
- D-SM-09
- D-SM-11
- D-SM-13
- D-SM-15
- D-SM-19
- D-SM-22



## teaching_notes

### reusable_patterns

- 主従 4 画面（検索一覧 → 明細一覧 → ヘッダモーダル → 明細モーダル）
- 1 モーダルで新規・複製・修正の 3 モードを切り替える
- 自動採番とダミーマスタ登録を 1 関数にまとめる（4A0000〜4Z9999、英字繰上げ）
- CONNECT BY で生産モデルの親子を再帰解決し、巨大 IN を避ける
- 1 テーブルにつき操作パターン別の移送表（登録・更新・削除）を分ける
- REG_STS を必須項目の充足で判定する（ヘッダ 4 項目、明細は必須 5 項目）
- 排他 → イベント参照 → 被参照 → 更新 → 外部連携の順序を固定する
- 表示は REG_STS を絞らず、仕掛表示だけ未確定を出す（R60Plc の逆張りの正例）

### anti_patterns

- テストの小計行を項目数に含める（D-SM-02）
- コード値をエスケープせず SQL に埋め込む（D-SM-05）
- 死んだ Service メソッド・死んだ Pydantic モデルを残す（D-SM-09 / D-SM-20）
- 返すメッセージ ID を取得しない（D-SM-10）
- 顧客会社コードを BP と実装に直書きする（D-SM-12）
- BP に設計者の疑問メモを残す（D-SM-11）
- API が完了メッセージを返さず、画面が固定文言を持つ（D-SM-23）
- Enabled という名前で disabled を制御する（D-SM-24）

### positive_contrast

- R60Plc の D-PL-07（表示が REG_STS=1 で絞らない設計／実装不一致）に対し、 R60SesModel は設計どおり『表示は絞らない・仕掛表示だけ REG_STS=0』である。 同種の画面でも設計と実装が一致する例として教材に使える。


## req_ids

## deviations

| id | title | category | severity | finding | evidence | impact | treatment |
|---|---|---|---|---|---|---|---|
| D-SM-01 | 調査票の endpoints=16 は実測 12 | survey | medium | reports/module-survey/scores/R60SesModel.yaml は complexity.signals.endpoints を 16 と 記録するが、同ファイル自身が【推測】と注記している。実測は @router.post 12 件、 Service メソッド 12 件。 | ["R60SesModelController.py: 12 の @router.post", "R60SesModelService.ts: 12 メソッド", "reports/module-survey/scores/R60SesModel.yaml: endpoints: 16（【推測】）"] | 複雑度スコアの端点シグナルが 33% 過大。 | 本カードは実測 12 を採る。 |
| D-SM-02 | 単体テスト 760 項目は小計行の二重計上 | design_internal | medium | 仕様兼結果のヘッダは 760 項目だが、節の小計行を含む。 実項目は 679。760 = 679 + 53 + 21 + 7。 B5 小計 53 は配下の子 48 と一致しない（差 5）。 | ["00_単体ﾃｽﾄ仕様兼結果.txt: AN 列合計", "カテゴリ別: 38 + 149 + 160 + 371 + 42 = 760 / 実項目 679"] | テスト規模を 81 件（約 12%）過大に見積もる。小計の誤差 5 の原因も不明。 | 本カードは 760（生セル）と 679（実項目）を併記する。 |
| D-SM-03 | メッセージ台帳が 3 箇所に分散し件数が一致しない | design_vs_implementation | medium | 『その他メッセージ』は 8 ID、単項目・項目間チェックが参照するのは 33 ID、 実装は 36 ID を取得し 37 ID を参照する。どの台帳も全量を持たない。 | ["19_その他メッセージ: 8 distinct", "17/18 チェック: 33 distinct", "R60SesModelController.py get_message_info: 36 ID", "参照 37 ID（R60W0001 を含む）"] | メッセージだけを台帳で照合すると、チェック系文言の欠落を見落とす。 | 本カードは 04-errors に全 37 ID を列挙する。 |
| D-SM-04 | Pydantic モデルが extra='ignore' | implementation_only | medium | BaseCamelModel は extra='ignore' を指定する。骨架規則の extra='forbid' と異なる。 | ["R60SesModelController.py:63-69", ".claude/rules/03-design-coding.md §2"] | 定義外の入力が 422 にならず静黙無視される。 | 移行案件の既存事実として記録。骨架の既定は forbid のまま変更しない。 |
| D-SM-05 | SQL の文字列連結とコード値の未エスケープ | implementation_only | high | search の件数 SQL は ses_mdl_cd をシングルクォートで囲まずに連結する。 get_ses_mdl_cd_condition は kon_hmk_cd / hsh_cd を未エスケープで LIKE に埋め込む。 download は WHERE 全体を f-string で組み立てる。 | ["R60SesModelController.py:1946-1948（count_sb へ生値）", "R60SesModelController.py:5189, 5195（KO_CD LIKE '値%'）", "R60SesModelController.py:2172-2286（download の WHERE 連結）"] | SQL 断片の混入面が広い。骨架の bind 原則から外れる。 | 骨架の製造細則では bind 必須。移行案件では既存実装の事実として記録する。 |
| D-SM-06 | search と download で DEL_FLG 条件の書き方が異なる | design_vs_implementation | low | search は is_deleted != '1' で DEL_FLG='0' を加え、 download は is_deleted == '0' の時だけ加える。 現行の入力値（0/1）では同値だが、想定外の値で挙動が分かれる。 | ["R60SesModelController.py:1981", "R60SesModelController.py:2229"] | 画面から 2 以外の値が来ると、検索と DL の対象がずれる。 | 本カードは事実として併記。 |
| D-SM-07 | 指定ソート時に副キー SES_MDL_CD が落ちる | design_vs_implementation | medium | 既定は ORDER BY DEL_FLG, SES_MDL_CD, ROWID。指定ソート時は ORDER BY DEL_FLG, {列} {ASC\|DESC}, ROWID となり、SES_MDL_CD の副キーが落ちる。 | ["R60SesModelController.py:2063-2078", "21_業務処理説明: 並び順の記述"] | 同値行の並びが設計と変わる。ROWID で順序は安定する。 | 実装を事実として記録。設計の副キー意図は未確定。 |
| D-SM-08 | ページングが OFFSET/FETCH | design_vs_implementation | low | 骨架の規則は Oracle 検索一覧のページングを原則 ROWID 方式とするが、 実装は OFFSET {n} ROWS FETCH FIRST {m} ROWS ONLY を使う。 | ["R60SesModelController.py:2111", ".claude/rules/00-project-global.md §5"] | 深いページで性能が落ち得る。 | 移行案件の既存事実。骨架の既定は変更しない。 |
| D-SM-09 | Service の dataInit が未使用 | implementation_only | low | R60SesModelService.ts は dataInit を持つが、画面のデータ初期化は subDataInit('R60SesModel/dataInit', ...) を直接呼ぶ。Service メソッドは死んでいる。 | ["R60SesModelService.ts:40-44", "R60SesModel.vue:1767-1772"] | 修正時にどちらを直すか誤り得る。 | 実装の事実として記録。 |
| D-SM-10 | R60W0001 を取得せずに返す | implementation_only | medium | dataInit は sim_kbn='0' で R60W0001 を返すが、init の message_info（36 件）に R60W0001 が含まれない。画面が文言を引けない可能性がある。 | ["R60SesModelController.py:2305", "R60SesModelController.py get_message_info: 36 件に W0001 なし"] | 通常環境で初期化を押すと、メッセージ解決に失敗し得る。 | 不具合候補として記録。 |
| D-SM-11 | 業務処理説明に設計者自身の疑問メモが残る | design_internal | low | BP r1720 に『※このパターンは存在しない？』という自己疑問の注記が残っている。 分岐の網羅性が確定していない。 | ["21_業務処理説明 r1720"] | その分岐の仕様が未確定のまま実装されている可能性。 | 未確定事項として記録。 |
| D-SM-12 | 顧客固有の会社コードが BP に直書き | design_internal | medium | BP の条件に '0093'（飲料社）・'0452'（カルピス社）・'0001'（ビール社工場）・ 'P030' が直書きされている。実装も定数として持つ。 | ["21_業務処理説明 r350, r602-604, r975, r1184, r1836", "R60SesModelController.py:50-51"] | 会社追加・変更のたびにコード修正が要る。greenfield では設定化を検討する。 | 移行案件の事実として記録。骨架へ持ち込まない。 |
| D-SM-13 | 項目移送表 12 枚に対して実テーブルは 6 つ | design_internal | low | DB1〜DB12 のうち、同一テーブルが登録・更新・削除の別シートに分かれている。 更新列はシートごとに読み分ける必要がある。 | ["22-33_項目移送表(DB)1-12", "SES_MODEL=DB1/7, SES_MODEL_MES=DB2/8/11/12, HAN_SEIHIN=DB4/10, KJO=DB6/9"] | 1 テーブル 1 シートと誤解すると更新列を取り違える。 | 01-fields に 12→6 の対応表を置く。 |
| D-SM-14 | A/B レポートが無い | ab_report | high | 調査票の impl_alignment は null。R60SesModel には A/B 比較レポートが無く、 実装が設計どおりかは単体テストの『不具合 0』以外に証拠が無い。 | ["reports/module-survey/scores/R60SesModel.yaml: impl_alignment: null", "doc/03_AI/AB_Reports/reports/R60SesModel/ 不存在"] | 設計と実装の一致を独立に検証できない。 | RAG では『A/B 未測定』を明示し、実装一致と断定しない。 |
| D-SM-15 | 調査票の項目数・イベント数は No の最大値 | survey | low | 調査票は『33 項目 / 39 項目 / 31 イベント』と記録するが、これはシートの No 最大値。 節見出し行と欠番を除くと、単項目チェック 29、項目間チェック 36、イベント 28。 | ["17_画面単項目チェック: No1-33、節行 [1,10,23,32]", "18_画面項目間: No1-39、節行 [1,4,25]", "20_イベント一覧: No1-31、節行 [1,20,26]"] | 件数で設計を照合すると 4〜7 件ずれる。 | 本カードは実件数を採る。 |
| D-SM-16 | 明細マスタ項目 No13 展開区分の初期値欄が誤り | design_internal | medium | 『展開区分』の初期値が『リンクを押下した同行の調達対象外フラグ』になっている。 コピー＆ペースト誤りで、展開区分自身の値が正。 | ["16_画面項目内容(マスタ項目_明細): No13"] | 初期値をそのまま実装すると、展開区分に調達対象外フラグを入れる。 | 設計の誤りとして記録。実装は展開区分を独立に扱う。 |
| D-SM-17 | 検索 No10 アイテム名称の種別が『ボタン』 | design_internal | medium | アイテム名称はテキストボックスだが、種別欄が『ボタン』になっている。 | ["06_画面項目内容(検索): No10"] | 種別で項目を分類すると、入力項目を取りこぼす。 | テキストボックスが正。実装もテキストボックス。 |
| D-SM-18 | 単項目 No8 半製品名称の桁が本文 30 とメッセージ引数 40 で食い違う | design_internal | medium | チェック本文は『30byte』だが、メッセージの ##2 は 40。 項目定義（半製品名称 40）と合わせると 40 が正と読める。 | ["17_画面単項目チェック: No8", "06_画面項目内容(検索): No18 半製品名称"] | 30 で実装すると、40 桁の名称を登録できない。 | 40 を正と推定し、未確定事項に残す。 |
| D-SM-19 | DB5 / DB6 の削除で監査列を更新しない | implementation_only | low | R60_HSH_SES_MODEL_REF_M_TBL と R60_KJO_SES_MODEL_M_TBL の削除は SEND_STS / DEL_FLG / KSN_DAT / KSN_PGM_ID の 4 列のみ。 他の削除系が更新する KSN_KBN / KSN_STF_ID / REV_NO を更新しない。 | ["26_項目移送表(DB)5", "27_項目移送表(DB)6"] | 監査証跡と楽観ロック値が残らない。意図か漏れか不明。 | 未確定事項として記録。 |
| D-SM-20 | 端点の無い Pydantic モデル定義が 2 組残る | implementation_only | medium | GetItem*（1001-1115 行）と GetKoCdNm*（1675-1732 行）は定義だけがあり、 @router.post が無い。getKonHmk と役割が重複する。 | ["R60SesModelController.py:1001-1115", "R60SesModelController.py:1675-1732"] | 死んだ契約定義が API 一覧を膨らませる。 | 実装の事実として記録。移行時は getKonHmk を正とする。 |
| D-SM-21 | InitEditHeaderData に mode が無く、渡した値が捨てられる | design_vs_implementation | medium | init_edit は mode=3 の分岐で InitEditHeaderData(mode='修正', ...) を組み立てるが、 モデルに mode フィールドが無いため extra='ignore' で応答から落ちる。 画面は親から受け取った mode を表示に使う。 | ["R60SesModelController.py:2455-2475", "R60SesModelController.py:571-655（InitEditHeaderData）"] | API 単体では操作モードが分からない。レスポンス定義と実装意図が食い違う。 | 実装の事実として記録。 |
| D-SM-22 | 検索 No12/16 のエンティティ桁 7 と表示桁 6 | design_internal | low | 購入品目コード・半製品コードはエンティティ桁 7、表示桁 6。 枝番が 6 桁であることと整合するが、桁欄の意味が混在している。 | ["06_画面項目内容(検索): No12, No16"] | 桁チェックをどちらで実装するか迷う。 | 実装（W0108 は購入品目 6 桁）に合わせ、表示桁を採る。 |
| D-SM-23 | 更新系 API が message_id を返さない | design_vs_implementation | medium | EditResponse / DeleteResponse / EditChildResponse / DeleteChildResponse は message_id を持つが、実装の成功応答は error_code / error_id / ses_mdl_cd のみ。 画面が R60I0001 / R60I0002 を固定表示する。 | ["R60SesModelController.py:2822, 3310, 3737, 4379, 4569", "R60SesModelEdit.vue:900-902"] | 設計のメッセージ契約と実装が一対一でない。文言変更時に両方を直す必要がある。 | 実装の事実として記録。 |
| D-SM-24 | Enabled という名前のフラグが disabled を制御する | implementation_only | medium | deleteBtnEnabled / registBtnEnabled は disabled 属性へバインドされる。 true が『非活性』を意味する。 | ["R60SesModelEdit.vue:484-486", "R60SesModelMesEdit.vue:483-486"] | 名前から活性と読むと挙動を逆に理解する。R60Plc の D-PL-15 と同型。 | 実装の事実として記録。骨架の製造では名前と意味を一致させる。 |

## design_internal_inconsistencies

- 単体テストの小計二重計上と B5 の差 5（D-SM-02）
- メッセージ台帳の分散（D-SM-03）
- BP の自己疑問メモ（D-SM-11）
- 会社コードの直書き（D-SM-12）
- 移送表 12 枚／テーブル 6 つ（D-SM-13）
- 展開区分の初期値コピペ誤り（D-SM-16）
- アイテム名称の種別誤り（D-SM-17）
- 半製品名称の 30/40（D-SM-18）
- コード桁 7/6（D-SM-22）

## open_questions

- D-SM-02 の B5 小計 53 と配下 48 の差 5 の原因。
- D-SM-06 の 2 が来た場合の正しい扱い。
- D-SM-07 の副キーは設計意図か実装の簡略化か。
- D-SM-18 の半製品名称は 30 か 40 か。
- D-SM-19 の監査列を更新しない理由。
- D-SM-21 の mode を API で返すべきか。

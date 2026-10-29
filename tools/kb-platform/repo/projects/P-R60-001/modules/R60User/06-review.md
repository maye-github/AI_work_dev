---
id: KNOW-LEGACY-R60-MODULE-R60USER-REVIEW-VIEW
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-modules-r60user-06-review
scope: project
project_id: P-R60-001
title: R60User — レビュー指摘と処置
doc_type: design-detail
conf_level: 30
updated_at: '2026-10-29'
---

# R60User — レビュー指摘と処置

> 正本は同ディレクトリの `06-review.yaml`。本ファイルは検索用の可読表現であり、
> 手で編集しない（`py -3 -m tools.kb_migrate --apply` で作り直す）。

| 項目 | 値 |
|---|---|
| id | KNOW-LEGACY-R60-MODULE-R60USER-REVIEW |
| type | knowledge |
| status | open |
| sensitivity | internal |
| owner | AI-SE |
| version | 0.1.0 |

## scope

| 項目 | 値 |
|---|---|
| design_sheets | 01, 06, 08, 09, 10, 11, 12, 13, 14 |
| frontend | R60UserService.ts / R60User.vue / R60UserEdit.vue / R60UserCreate.vue |
| backend | R60UserController.py |
| tests | 00_単体ﾃｽﾄ仕様兼結果.txt / 01_1.画面遷移.txt |
| ab_report | doc/03_AI/AB_Reports/reports/R60User/summary.md |

## finding_summary

| 項目 | 値 |
|---|---|
| total | 16 |
| survey_or_ab | 1 |
| design_internal | 3 |
| design_vs_implementation | 3 |
| implementation_only | 9 |

### severity

#### high

- D-US-11

#### medium

- D-US-01
- D-US-02
- D-US-03
- D-US-06
- D-US-12
- D-US-13

#### low

- D-US-04
- D-US-05
- D-US-07
- D-US-08
- D-US-09
- D-US-10
- D-US-14
- D-US-15
- D-US-16



## teaching_notes

### reusable_patterns

- 1 画面 CRUD に権限軸（権限区分・自工更新・他工更新）を足す設計
- 修正専用マスタ：IDM／3G 受信済みデータを編集する（新規を作らない）
- 7 つのドロップダウンを情報 ID で解決する
- 緊急配信チェック＝SEND_STS='9'、オン時は 5 項目必須
- REG_STS を 5 項目の充足で判定する
- 排他 → 更新 → 緊急配信 → commit の順序
- 0 件時に一覧部を v-if で非表示にする（R60Area の反面教師に対する正例）

### anti_patterns

- 未知の更新エラーを成功表示する（D-US-11）
- 画面にしか検証が無い更新 API（D-US-06）
- 押しても何も起きないボタンと死んだ Create コンポーネント（D-US-01）
- 初期値の取り違え（所属会社 vs S 会社、D-US-02）
- LIKE 値の未エスケープ（D-US-13）
- 活性フラグの名前と意味の反転（registBtnEnabled=true が非活性）

### positive_contrast

- 0 件時に DataTable ごと非表示（設計の『明細部を非表示』に一致）
- REG_STS の判定が設計（移送表 No16）と一致
- 緊急配信の引数が設計（r340-r344）と一致


## req_ids

## deviations

| id | title | category | severity | finding | evidence | impact | treatment |
|---|---|---|---|---|---|---|---|
| D-US-01 | 操作モードは修正のみ。新規・ダウンロードは空実装、Create コンポーネントは未参照 | implementation_only | medium | 検索画面には「ダウンロード」「新規」ボタンがあり、初期値は非活性と設計されるが、 実装の doDownload / doCreate は空関数である。削除ボタンも常時非活性（ストア既定 true）。 新規用 R60UserCreate.vue（323 行）はどこからも import されていない。 | ["R60User.vue:916-919: doDownload / doCreate が空実装", "R60User.vue:136: 新規ボタンの onClick は doCreate", "R60User.vue:147: import は R60UserEdit のみ", "stores/index.ts:83-85: deleteBtnEnabled=true / registBtnEnabled=true が既定", "08_画面項目内容(マスタ項目): 新規・複製操作時の列が空"] | 設計はボタンを定義するが、機能イベントが無い。押しても何も起きないボタンが残る。 死んだコード 323 行。教材としては『修正専用マスタ』の実例になる。 | 実装の事実として記録。設計のボタン定義と実装の機能欠落を混同しない。 移行時は修正のみを正とし、新規・複製が必要なら別モジュールとして設計する。 |
| D-US-02 | 検索の会社初期値が S 会社（scmp_cd）で、所属会社（cmp_cd）ではない | design_vs_implementation | medium | 設計（06 検索シート No8）は「初期値：ログインユーザーの所属会社を選択状態にする」。 実装は userInfo.scmp_cd を初期値にする。ストアでは cmp_cd が所属会社、 scmp_cd は mngInfo.loginSCmpCd（S 会社）である。 | ["R60User.vue:201: cmpCd.value = userInfo.scmp_cd", "stores/index.ts:58-67: cmp_cd=userInfo.cmpCd / scmp_cd=loginSCmpCd", "06_画面項目内容(検索): No8 初期値=ログインユーザーの所属会社"] | 所属会社と S 会社が異なるユーザーでは、初期表示の検索結果が設計と変わる。 検索漏れ（または余計な行）として現れる。 | 設計を正とし、移行時は cmp_cd を使う。D-US-02 として人要裁定。 |
| D-US-03 | 組織ユニット名称のエンティティ記載が 2 シートで食い違う | design_internal | medium | 検索シート No11 はエンティティを『部署マスタ.組織ユニット』、No30 は『ユーザマスタ.社員コード』 と書く。一方、表示仕様と業務処理説明は R60_Get_User_Information_FNC(社員コード, '6') → 部署マスタ.正式名称 と書く。 | ["06_画面項目内容(検索): No11 エンティティ=部署マスタ.組織ユニット", "06_画面項目内容(検索): No30 エンティティ=ユーザマスタ.社員コード", "06_画面項目内容(検索): No30 表示仕様=R60_Get_User_Information_FNC(社員コード,'6') → 部署マスタ.正式名称", "13_業務処理説明 r77-r88: 部署マスタから正式名称を取得"] | エンティティ列だけを読むと、名称ではなくコードを表示する設計に見える。 実装は getSskUnitNm で R60_SSK_M_TBL.SEI_NM を返し、表示仕様側に一致する。 | 表示仕様と業務処理説明を正とする。実装の SEI_NM との対応は【推測】。 |
| D-US-04 | 経理用事業場の複合キーと S_JIG_CD（4 桁）の分解規則が設計に無い | design_internal | low | マスタ項目シート No13 はリストキーを「会社コード + ',' + 事業場コード」と定義する。 移送表の S_JIG_CD は 4 桁で、複合値のどちらを保存するかが書かれていない。 | ["08_画面項目内容(マスタ項目): No13 リストキー項目=会社コード + ',' + 事業場コード", "14_項目移送表(DB): No10 S_JIG_CD 桁数=4", "R60UserController.py:1354-1355: カンマ分割の 2 番目を S_JIG_CD に保存"] | 設計だけを読むと保存値が決まらない。実装はサーバー側で分割して解決している。 | 実装を事実として併記する。設計へは『2 番目を保存』と明記すべき。 |
| D-US-05 | 自工／他工判別が設計の OR 条件を単純化 | design_vs_implementation | low | 設計は「経理用会社／事業場と一致」または「S 会社／S 事業場と一致」なら自工とする。 実装は、経理用が入力されていれば経理用とだけ比較し、無ければ S と比較する。 両方が入力されていて異なる場合、設計の OR 条件と結果が変わりうる。 | ["13_業務処理説明 r228-r242: 自工判別 14-1 / 14-2", "R60UserEdit.vue:844-869: subDistKojo2", "R60UserEdit.vue:457-475: 権限区分 Y のとき引数を切り替えて呼ぶ"] | 特定の会社・事業場の組合せで、登録ボタンの活性が設計と逆になる可能性がある。 | 設計を正とし、移行時は OR 条件を実装する。 |
| D-US-06 | 更新端点が画面チェックを再検証しない | implementation_only | medium | 単項目チェック・項目間チェック・緊急配信時の必須選択は、すべてフロントエンドで行う。 /edit は排他チェックと REG_STS 判定だけを行い、R60W0012 / R60W2002 / R60W0016 を再検証しない。 | ["R60UserEdit.vue:698-772: inputCheck", "R60UserEdit.vue:607-625: R60W2002", "R60UserController.py:1340-1438: edit は排他と set_reg_sts のみ"] | API を直接呼ぶと、緊急配信オンのまま必須項目が空の行を保存できる。 画面経由の操作では設計どおりに止まる。 | R60 既存実装の事実として記録。greenfield では端点側にも最低限の検証を置く。 |
| D-US-07 | 対象行が無い場合も排他エラー（R60W0006）を返す | implementation_only | low | 排他チェックは result_check が None の場合も R60W0006 を返す。 設計は KSN_DAT の不一致だけを排他エラーと定義する。 | ["R60UserController.py:1377-1380", "10_画面項目間・DB整合チェック: No6 排他=KSN_DAT 不一致"] | 他端末で削除された場合と、同時更新された場合が同じメッセージになる。 | 実装の事実として記録。設計は排他の定義のみを定める。 |
| D-US-08 | KSN_KBN を REG_KBN_ONLINE 定数で比較（命名不整合） | implementation_only | low | 排他チェックは KSN_KBN（更新区分）を R60Const.REG_KBN_ONLINE と比較する。 定数名は登録区分（REG_KBN）を指す。値は共に '1' と推測され、動作は設計どおり。 | ["R60UserController.py:1378", "13_業務処理説明 r331-r333: 更新区分が '1'（オンライン）"] | 値が同じため現状は動くが、定数の意味を取り違えると将来の変更で壊れる。 | 実装の事実として記録。移行時は KSN_KBN 用の定数を使う。 |
| D-US-09 | R60W1003 を取得するが設計・使用箇所が無い | implementation_only | low | init は 15 個のメッセージ ID を取得する。設計の 3 シート（09/10/11）に現れるのは 14 ID。 R60W1003 は設計に無く、画面にも使用箇所が無い。 | ["R60UserController.py:737-775: R60W1003 を含む 15 ID", "09_画面単項目チェック / 10_画面項目間 / 11_その他メッセージ: 合計 14 ID", "R60User.vue / R60UserEdit.vue: R60W1003 の参照なし"] | 未使用メッセージの取得。R60W0103 の誤記の可能性もある。 | 未使用として記録。用途は人要確認。 |
| D-US-10 | R60W0005 の文言が上限値を 3000/3001 と直書き（実装は実値） | design_internal | low | 項目間チェックシートはメッセージ引数を ##1=3000、##2=3001 以上の自然数と固定値で書く。 上限は情報 ID 000000024 で変わるため、設計の固定値は陳腐化する。 実装は ##1 に max_count、##2 に total を差し込む。 | ["10_画面項目間・DB整合チェック: No3 ##1=3000、##2=3001 以上", "R60User.vue:824-830: data.maxCount / data.total を差込", "R60UserController.py:917-918: 上限は情報 ID 000000024"] | 設計どおりに実装すると、上限値変更時に文言が嘘になる。 | 実装の方式（実値差込）を正とする。改善例として教材化できる。 |
| D-US-11 | 未知の更新エラーを成功扱いする | implementation_only | high | registDialog は errorCode='1' のとき R60W0006 だけを処理し、それ以外は TODO のまま if を抜ける。その後、R60I0001（登録しました。）を表示し、モーダルを閉じて再検索する。 | ["R60UserEdit.vue:657-683: errorId=R60W0006 以外は TODO で通過", "R60UserEdit.vue:673-683: 成功メッセージと closeEditDialog"] | サーバー側の想定外エラー（DB 例外・オンライン制御エラー等）でも、画面は成功と表示する。 利用者は更新されたと誤認する。更新系で最も危険な差分。 | 設計はエラー時の中断を定める。実装は未完成。 greenfield では error_code を網羅し、未知コードはエラー表示で止める。 |
| D-US-12 | 登録ボタンの活性が経理用会社の変更後に再判定されない | design_vs_implementation | medium | 設計のボタン制御は、自工／他工判別の結果に基づく。判別は経理用会社／事業場に依存する。 実装はモーダル初期化時に 1 回だけ判定し、イベント 13（経理用会社変更）では 事業場リストを作り直すだけで、登録ボタンの活性を再判定しない。 | ["R60UserEdit.vue:457-475: 初期化時のみ subBtnRegistDisabled2 を呼ぶ", "R60UserEdit.vue:511-546: イベント 13 は sJigData の再生成のみ", "13_業務処理説明 r244-r267: 自工／他工に応じたボタン制御"] | 経理用会社を変えると、実際の自工／他工とボタン活性が食い違う可能性がある。 | 設計を正とし、変更イベントで再判定する。 |
| D-US-13 | LIKE 値の % / _ をエスケープしない | implementation_only | medium | 社員コード・組織ユニット・発令日は前方一致で `LIKE :X ESCAPE '\'` を使うが、 入力値に含まれる % と _ をエスケープしていない。設計は「ワイルドカード文字入力不要」であり、 入力された記号は文字として扱うべきである。 | ["R60UserController.py:928-935: f\"{value}%\" をそのまま渡す", "06_画面項目内容(検索): No12/13 前方一致あいまい検索（ワイルドカード入力不要）"] | `%` を入力すると全件検索、`_` を入力すると任意 1 文字一致になり、検索条件が広がる。 件数上限を超えて一覧が出ない、といった症状になる。 | 実装の事実として記録。移行時は値の % _ \ をエスケープする。 |
| D-US-14 | ページングが OFFSET/FETCH | implementation_only | low | 一覧取得は OFFSET … ROWS FETCH FIRST … ROWS ONLY を使う。 骨架の規則 00 §5 は Oracle 一覧のページングに ROWID 方式を推奨する。 | ["R60UserController.py:983-990", ".claude/rules/00-project-global.md §5"] | 大量件数では OFFSET の走査コストが増える。設計書自体は方式を指定しない。 | R60 既存実装の事実として記録。greenfield では ROWID を第一候補にする。 |
| D-US-15 | 更新者 ID をクライアントから受け取る | implementation_only | low | /edit は ksn_stf_id（更新者 ID）を要求パラメータとして受け取り、そのまま KSN_STF_ID に保存する。 画面はログインユーザの stf_cd を送るが、端点はセッションから解決しない。 | ["R60UserController.py:1357 / 1417", "R60UserEdit.vue:646: ksnStfId: userInfo.stf_cd"] | API を直接呼ぶと更新者を詐称できる。緊急配信の引数にも同じ値が使われる。 | R60 既存実装の事実として記録。greenfield ではセッションから解決する。 |
| D-US-16 | 調査票の endpoints=7 は AB の actionId 数で、実装端点は 5 | survey | low | scores/R60User.yaml は endpoints=7 と記録する。実装の @router.post は 5 件、 Service メソッドも 5 件。A/B の actionId は head / init / check / search / search / detail / modify の 7 件。 | ["R60UserController.py: 5 端点（init / getSskUnitNm / search / initEdit / edit）", "R60UserService.ts: 5 メソッド", "AB summary.md: actionId 7 件"] | 複雑度スコアの端点シグナルが 1.4 倍に見える。 | 本カードは実測 5 を採る。 |

## design_internal_inconsistencies

- 組織ユニット名称のエンティティ記載（D-US-03）
- 経理用事業場の複合キーと S_JIG_CD の分解規則（D-US-04）
- R60W0005 の上限値直書き（D-US-10）
- 検索シート No8 のエンティティが『ユーザマスタ.会社コード』。実列名は SZK_CMP_CD。

## open_questions

- D-US-02: 検索の会社初期値は所属会社か S 会社か。
- D-US-05: 自工／他工は OR 条件か、入力優先か。
- D-US-11: 未知エラー時の成功表示を許容するか。
- D-US-09: R60W1003 の用途。R60W0103 の誤記か。

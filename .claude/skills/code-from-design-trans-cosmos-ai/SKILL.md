---
name: code-from-design-trans-cosmos-ai
description: "trans-cosmos-ai 設計→製造 (design-to-code) パイプラインスキル。上流 SE の R-ID を起点に、基本設計(BD)/詳細設計(DD)/製造（コーディング）の全ステップを Claude Code 自身が一貫して実行し、R-ID/F-ID/I-ID/D-ID/L-ID/E-ID/TC-ID のトレーサビリティを ids.yml 単一ソース配下で確保する。既存 R60Common.ts の共通関数および r60const.py の ACTION_ID へのマッピングを強制し、並行新版の作成を禁止する。**本スキルは `build_mode: migration` の案件（既存システム・旧設計書を持つ案件）向けである**（`build_mode` の宣言は `docs/00_plan/coach/<module>/case.yml`。既定は `greenfield`＝從無到有で、その場合の共通部品は本案件で新規定義するため発動しない）。R60Area ファミリー（R60AreaService 7 メソッド / R60_AREA_M_TBL 56 画面項目）の製造コードや設計文書を生成・レビューするときは必ずこのスキルを使用すること。"
id: SKL-001
type: skill
req_ids: [R-101]
status: baselined
sensitivity: internal
owner: AI-PG
version: 0.1.0
---

# code-from-design-trans-cosmos-ai スキル定義書

## スキル概要

本スキルは、trans-cosmos-ai 案件における設計情報から製造コードを自動生成するエンドツーエンドのパイプラインを提供する。上流SEが作成したR-ID（要求ID）をトリガーとし、基本設計BD、詳細設計DD、製造（コーディング）実行の4ステップを **Claude Code 自身が** 順に実行する。各工程はids.ymlによるID管理の下でトレーサビリティを確保し、trace_check --strictによる閉ループ検証を必須とする。**交接工程は存在しない**。Claude Code は設計からコード生成・検証までを単独で担い、人間はレビュー／承認ゲート（要件合意・設計評審・合否判定・リリース判定）を保持する。

本貫通例のトレース連鎖は **R-101 → F-042 → I-201..I-256 → D-043 → L-014/L-015 → E-001..E-008 → TC-001..TC-008** であり、前方向・逆方向の双方で途切れなく閉じていることを `trace_check --strict` で検証する。

参照先実装コードは `D:\AI_work\Front-end\src\views\R60Area.vue` の onMountedフック、同じく `D:\AI_work\Front-end\src\service\R60AreaService.ts` の7メソッド（init / search / download / initEdit / getPlcNm / delete / edit）、`D:\AI_work\api\fastapi_oracle_pjt\app\utils\r60const.py` のACTION_ID 40個、および `D:\AI_work\Front-end\src\common\R60Common.ts` の **16 関数（本書 §3.5 の関数活用マップが唯一の定義）** をベースラインとする。

> **関数数の数え方（混同しやすい）**: `R60Common.ts` 全体は **54 関数**（`CLAUDE.md` §2 禁①）。
> 本スキルが製造で実際に呼び出す**代表関数は §3.5 の 16 件**。`.claude/rules/03-design-coding.md` §3 の表は
> このうち**呼び出し順で特に重要な 13 件を抜粋**したものである。**全リストの定義は本書 §3.5 のみ**（NFR-1）。

---

## 適用範囲（Scope）

本スキルの適用対象は **R60Area（R-101）系の設計→製造パイプライン**（BD → DD → 製造）である。

**適用条件**
- 対象 R-ID が `docs/00_registry/ids.yml` の R セクションに **事前登録済み**であること（§1.3 の判定に従う）。

**適用外（本スキルを使わない）**
1. **要件の構造化（ノード1 需求理解）** — 要件書を「需求结构化表」へ構造化する作業は本スキルの守備範囲外である。教程 `tutorial/R60Login` のノード1 では、提示済みの「節点1 プロンプト」を用いる。
2. **ids.yml 未登録の R-ID（教学号段など）** — 例 `R-201`。実測済み: これを渡すと **Step 1（§1.3 の事前登録確認）で受理拒否**となり、先へ進まない。

**逸脱した場合の症状**
- 未登録 R-ID を渡すと Step 1 で受理拒否される。R60Area 以外の題材では設計方針が噛み合わない。

---

## Step 1: R-ID受理（要求登録段階）

### 1.1 入力情報の確認

上流工程から引き渡されたR-ID（R-101など）の妥当性を検証する。R-IDは `ids.yml` のRセクションに事前登録されている必要があり、未登録のR-IDは受理しない。R-IDには以下の情報が含まれることを確認する：

- 要求名称、要求概要、機能分類
- 優先度（A/B/C）、想定工数、リリース時期
- 関連する既存機能（画面ID、APIエンドポイント）
- 利害関係者（要求元、承認者）

### 1.2 R60Areaコードとの対応付け

`R60Area.vue` onMounted（194行目-238行目）における画面初期化のフローを基準とし、R-IDがどの画面ライフサイクルフックに影響するかを特定する。具体的には：

- onMounted内の `dataService.init()` 呼出し（206行目）に対応するR60AreaService.initメソッド
- 会社/事業場ドロップダウン設定（208-214行目）
- ページ数ドロップダウン設定（217-218行目）
- カラム定義設定（227-237行目）

R60AreaService.tsの7メソッドの役割：
| No | メソッド名      | 用途                          | 対応ACTION_ID                 |
|----|-----------------|-------------------------------|-------------------------------|
| 1  | init            | 一覧画面初期化                | ACTION_ID_INIT                |
| 2  | search          | 検索処理                      | ACTION_ID_SEARCH              |
| 3  | download        | CSVダウンロード処理           | ACTION_ID_DOWNLOAD            |
| 4  | initEdit        | 入力画面初期化                | ACTION_ID_DIALOG              |
| 5  | getPlcNm        | ロケーション名称取得          | ACTION_ID_HEAD                |
| 6  | delete          | 論理削除処理                  | ACTION_ID_DELETE              |
| 7  | edit            | 更新/登録処理                 | ACTION_ID_REGIST / ACTION_ID_MODIFY |

### 1.3 ids.ymlへの事前登録確認

`ids.yml` のF-ID（機能ID）とI-ID（画面項目ID）の体系を確認する。本貫通例では機能は **F-042**（R60Area全画面機能）1 件、画面項目は **I-201..I-256**（56 件 = R60_AREA_M_TBL 56 列相当）である。R-ID に対応する F-042 / I-201..I-256 が登録済みであることを確認する。

---

## Step 2: 基本設計BD生成

### 2.1 ids.ymlへのF-ID・I-ID登録

BD作成の前に、ids.ymlに以下のIDを登録する：

```yaml
R:
  R-101:
    name: "R60Areaマスタ検索登録修正削除"
    status: baselined
F:
  F-042:
    r_id: R-101
    name: "R60Area全画面機能"
    description: "一覧検索画面 + 登録修正複製ダイアログの 2 画面構成"
    service: R60AreaService
    endpoints:                       # 7 API endpoints（R60AreaService の 7 メソッドに対応）
      - "POST /R60Area/init"         # R60AreaService.init
      - "POST /R60Area/search"       # R60AreaService.search
      - "POST /R60Area/download"     # R60AreaService.download
      - "POST /R60Area/initEdit"     # R60AreaService.initEdit
      - "POST /R60Area/getPlcNm"     # R60AreaService.getPlcNm
      - "POST /R60Area/delete"       # R60AreaService.delete
      - "POST /R60Area/edit"         # R60AreaService.edit
I:
  # 画面項目 = R60_AREA_M_TBL 56 列相当（cmpCd / jigCd / araCd ... regSts）。I-201..I-256 の 56 件。
  # 個別定義は docs/00_registry/ids.yml を参照。ここでは範囲のみ記載（全 56 件を列挙しない）。
  I-201..I-256:
    f_id: F-042
    count: 56
    note: "56 画面項目/データ項目。D-043（R60_AREA_M_TBL）の列と 1:1 対応。"
```

### 2.2 bd-template.yamlへの埋め込み

登録したF-ID・I-IDをbd-template.yamlのfrontmatter7項目に埋め込む：

```yaml
---
id: BD-R60Area-001
type: basic-design
req_ids: [R-101]
func_ids: [F-042]
if_ids: [I-201..I-256]   # 56 画面項目（範囲表記、個別定義は ids.yml）
status: baselined
sensitivity: internal
owner: AI-PG
version: 0.1.0
---
```

### 2.3 BD本体の作成項目

基本設計書には以下を記載する：

1. 画面構成：R60Area.vueのtemplate構造（ヘッダー、Splitter条件部/結果部、フッター、編集ダイアログ）
2. 画面項目一覧：検索条件（会社、事業場、エリアコード、削除含む、1頁件数）、結果一覧カラム（28項目+複製/送信/削除）
3. 権限制御：R60Common.subListBtnDisabledによるボタン活性制御、KGN_KBN_Y/Nと自工/他工フラグの組合せ
4. 画面遷移：一覧→新規/複製/修正ダイアログ（R60AreaEdit.vue）、業務終了ウィンドウクローズ
5. 共通部品呼出し：§3.5 の 16 関数の使い分け（うち呼び出し順の要は showMessageDialog, subCheckSubmit, subSetSubmitFlg, subInitSubmitFlg, spreadResults, resetErrors, subCheckAlphabetNumber, showErrorAndFocus, subDownload, subListBtnDisabled, subResultListInit, initReset, resetSortIcon の 13 件）

### 2.4 r60const.py ACTION_ID 40個対応表

r60const.py 15-43行目に定義されるACTION_ID 40個は基本設計の操作分類として用いる：

- 初期化系：ACTION_ID_INIT / ACTION_ID_HEAD / ACTION_ID_CHECK / ACTION_ID_CONDITION
- 検索系：ACTION_ID_SEARCH / ACTION_ID_DETAIL / ACTION_ID_CHILD_SEARCH / ACTION_ID_CHILD_DETAIL
- 登録系：ACTION_ID_NEW / ACTION_ID_REGIST / ACTION_ID_MODIFY / ACTION_ID_COPY / ACTION_ID_DUPLI
- 削除系：ACTION_ID_DELETE
- ダイアログ系：ACTION_ID_DIALOG
- 画面遷移系：ACTION_ID_BACK / ACTION_ID_END / ACTION_ID_TITLE_CHANGE
- ドロップダウン系：ACTION_ID_MAKEDROPDOWN / ACTION_ID_CHILD_RESULT / ACTION_ID_FOOT
- 明細系：ACTION_ID_ADD_RECORD / ACTION_ID_CHILD_REGIST / ACTION_ID_CHILD_MODIFY / ACTION_ID_CHILD_NEW
- ファイル系：ACTION_ID_DOWNLOAD / ACTION_ID_DATAINIT / ACTION_ID_CHECK_UPLOAD / ACTION_ID_FILE_UPLOAD

---

## Step 3: 詳細設計DD

### 3.1 D-ID/L-ID/E-IDの登録

ids.ymlにD-ID（データモデル）とL-ID（業務ロジック）とE-ID（エラー・イベント）を追加する：

```yaml
D:
  D-043:
    f_id: F-042
    name: "R60Area詳細設計（DML定義）"
    description: "R60_AREA_M_TBL に対する SELECT/INSERT/UPDATE の物理設計"
L:
  L-014:
    d_id: D-043
    name: "search 業務（検索ロジック）"
    file: "R60AreaController.py"
    lines: "1499-1647"
  L-015:
    d_id: D-043
    name: "initEdit/edit/delete 業務（排他+参照+重複）"
    file: "R60AreaController.py"
    lines: "1713-2915"
E:
  E-001:
    l_id: L-014
    error_id: R60W0010
    jp: "検索結果0件"
  E-002:
    l_id: L-015
    error_id: R60W0006
    jp: "排他エラー（KSN_DAT不一致）"
  E-003:
    l_id: L-015
    error_id: R60W0014
    jp: "キー重複エラー"
  E-004:
    l_id: L-015
    error_id: R60W0024
    jp: "被参照エラー（削除不可）"
  E-005:
    l_id: L-015
    error_id: R60E0025
    jp: "システムエラー"
  E-006:
    l_id: L-015
    error_id: R60W0033
    flg: "1"
    jp: "ロケーション未登録（原材料）"
  E-007:
    l_id: L-015
    error_id: R60W0033
    flg: "2"
    jp: "ロケーション未登録（半製品）"
  E-008:
    l_id: L-015
    error_id: R60A0039-0040
    jp: "削除確認メッセージ"
```

### 3.2 dd-template.yaml作成

詳細設計テンプレートを作成し、SQLテンプレートを埋め込む。frontmatter7項目は以下の通り：

```yaml
---
id: DD-R60Area-001
type: detail-design
req_ids: [R-101]
logic_ids: [L-014, L-015]
data_ids: [D-043]
error_ids: [E-001, E-002, E-003, E-004, E-005, E-006, E-007, E-008]
status: baselined
sensitivity: internal
owner: AI-PG
version: 0.1.0
---
```

### 3.3 L-014 SQLテンプレート（検索）

R60AreaController.py:1499-1647（L-014）に対応するSQLセグメント：

```sql
-- 総件数取得
SELECT COUNT(CMP_CD)
FROM R60_AREA_M_TBL
WHERE 1=1
  AND CMP_CD = :CMP_CD
  AND JIG_CD = :JIG_CD
  AND ARA_CD LIKE :ARA_CD ESCAPE '\'
  AND REG_STS = :REG_STS
  AND DEL_FLG = :DEL_FLG;

-- 明細ページング取得（OFFSET/FETCH）
SELECT SEND_STS, CMP_CD, JIG_CD, CMP_NM, JIG_NM, ARA_CD, ARA_NM, ARA_RNM,
       UKH_PLC_CD, UKH_PLC_NM, UKH_KEIJ_JIG_CD, UKH_KEIJ_JIG_NM, UKH_KEIJ_BSY_CD, UKH_KEIJ_BSY_NM,
       SAIM_KEIJ_JIG_CD, SAIM_KEIJ_JIG_NM, SAIM_KEIJ_BSY_CD, SAIM_KEIJ_BSY_NM,
       SAIKN_KEIJ_JIG_CD, SAIKN_KEIJ_JIG_NM, SAIKN_KEIJ_BSY_CD, SAIKN_KEIJ_BSY_NM,
       JID_HAR_SYN_FLG, SHR_ANSY_TDK_NM,
       IDO_DFLT_PLC_CD_GZR, IDO_DFLT_PLC_NM_GZR, IDO_DFLT_PLC_CD_HSH, IDO_DFLT_PLC_NM_HSH,
       SYCH_KBI_CMP_CD, SYCH_KBI_CMP_NM, SYCH_KBI_JIG_CD, SYCH_KBI_JIG_NM,
       SYCH_KBI_UKH_KEIJ_JIG_CD, SYCH_KBI_UKH_KEIJ_JIG_NM, SYCH_KBI_UKH_KEIJ_BSY_CD, SYCH_KBI_UKH_KEIJ_BSY_NM,
       SYCH_KBI_UKH_SAIM_JIG_CD, SYCH_KBI_UKH_SAIM_JIG_NM, SYCH_KBI_UKH_SAIM_BSY_CD, SYCH_KBI_UKH_SAIM_BSY_NM,
       SYCH_KBI_UKH_SAIKN_JIG_CD, SYCH_KBI_UKH_SAIKN_JIG_NM, SYCH_KBI_UKH_SAIKN_BSY_CD, SYCH_KBI_UKH_SAIKN_BSY_NM,
       DEL_STATUS, DEL_FLG, JIG_HYJ_SEQ
FROM R60_AREA_M_TBL
WHERE 1=1 AND ...同上...
ORDER BY DEL_FLG, CMP_CD, TO_NUMBER(R60_Get_Jig_Information_FNC(CMP_CD,JIG_CD,'3')), JIG_CD, ROWID
OFFSET :offset ROWS FETCH FIRST :page_limit ROWS ONLY;
```

### 3.4 L-015 SQLテンプレート（編集初期化詳細取得）

R60AreaController.py:1713-2915（L-015）に対応するSQLセグメント：

```sql
SELECT
  CMP_CD,
  R60_Get_Cmp_Information_FNC(CMP_CD, '1'),
  JIG_CD,
  R60_Get_Jig_Information_FNC(CMP_CD, JIG_CD, '2'),
  ARA_CD,
  TRIM(REPLACE(ARA_NM, ' ', '')),
  RTRIM(ARA_RNM, '  '),
  UKH_PLC_CD,
  R60_Get_Ukh_Plc_Info_FNC(CMP_CD, JIG_CD, UKH_PLC_CD, '1'),
  UKH_KEIJ_JIG_CD,
  R60_Get_Jig_Information_FNC(CMP_CD, UKH_KEIJ_JIG_CD, '2'),
  UKH_KEIJ_BSY_CD,
  R60_Get_Hiyo_Keij_Bsy_Info_FNC(CMP_CD, UKH_KEIJ_BSY_CD, '1'),
  SAIM_KEIJ_JIG_CD,
  R60_Get_Jig_Information_FNC(CMP_CD, SAIM_KEIJ_JIG_CD, '2'),
  SAIM_KEIJ_BSY_CD,
  R60_Get_Hiyo_Keij_Bsy_Info_FNC(CMP_CD, SAIM_KEIJ_BSY_CD, '1'),
  SAIKN_KEIJ_JIG_CD,
  R60_Get_Jig_Information_FNC(CMP_CD, SAIKN_KEIJ_JIG_CD, '2'),
  SAIKN_KEIJ_BSY_CD,
  R60_Get_Hiyo_Keij_Bsy_Info_FNC(CMP_CD, SAIKN_KEIJ_BSY_CD, '1'),
  JID_HAR_SYN_FLG,
  R60_Get_Code_Chi_Meisai_FNC('000000115', JID_HAR_SYN_FLG, '0'),
  RTRIM(SHR_ANSY_TDK_NM, '  '),
  IDO_DFLT_PLC_CD_GZR,
  R60_Get_Plc_Infomation_FNC(CMP_CD, JIG_CD, IDO_DFLT_PLC_CD_GZR, '1'),
  IDO_DFLT_PLC_CD_HSH,
  R60_Get_Plc_Infomation_FNC(CMP_CD, JIG_CD, IDO_DFLT_PLC_CD_HSH, '1'),
  SYCH_KBI_CMP_CD, SYCH_KBI_JIG_CD,
  SYCH_KBI_UKH_KEIJ_JIG_CD, SYCH_KBI_UKH_KEIJ_BSY_CD,
  SYCH_KBI_UKH_SAIM_JIG_CD, SYCH_KBI_UKH_SAIM_BSY_CD,
  SYCH_KBI_UKH_SAIKN_JIG_CD, SYCH_KBI_UKH_SAIKN_BSY_CD,
  KSN_KBN, SEND_KBN, DEL_FLG,
  CASE SEND_STS WHEN '9' THEN SEND_STS ELSE '0' END,
  TO_CHAR(KSN_DAT, 'YYYY/MM/DD HH24:MI:SS'),
  TO_CHAR(REV_NO)
FROM R60_AREA_M_TBL
WHERE CMP_CD = :cmp_cd AND JIG_CD = :jig_cd AND ARA_CD = :ara_cd;
```

### 3.5 R60Common 関数活用マップ

R60Common.tsからエクスポートされる代表関数とDD上での活用箇所（既存資産を唯一真源とし、新規類似関数の自作は禁止）：

| No | 関数名                | 用途                                      | 使用箇所                        |
|----|-----------------------|-------------------------------------------|---------------------------------|
| 1  | showMessageDialog     | メッセージダイアログ                      | エラー/情報通知時全般           |
| 2  | subCheckSubmit        | 二度押し防止チェック                      | 全ボタンイベント先頭            |
| 3  | subSetSubmitFlg       | 二度押し防止フラグON                      | API呼出直前                    |
| 4  | subInitSubmitFlg      | 二度押し防止フラグOFF                     | API呼出finallyブロック         |
| 5  | spreadResults         | 条件/結果領域スプレッド                   | toggle関数                     |
| 6  | resetErrors           | エラー状態リセット                        | 検索実行前                     |
| 7  | subCheckAlphabetNumber| 半角英数字チェック                        | エリアコード入力チェック       |
| 8  | showErrorAndFocus     | エラー表示+フォーカス移動                 | 入力チェックNG時               |
| 9  | subDownload           | CSVファイルダウンロード                   | doDownload関数                 |
| 10 | subListBtnDisabled    | 一覧画面ボタン活性/非活性                 | 検索成功後                     |
| 11 | subResultListInit     | 結果一覧初期化                            | 検索成功後                     |
| 12 | initReset             | スクロール/ページャ初期化                 | 検索実行前                     |
| 13 | resetSortIcon         | ソートアイコン初期化                      | 検索実行前                     |
| 14 | byteCheck             | バイト数チェック                          | 全角/半角混在項目の桁数検証     |
| 15 | subCheckKanaByte      | カナ・バイト数チェック                    | カナ項目（例: エリア名）検証    |
| 16 | chkHanEngNum3         | 半角英数字3種チェック                     | コード系項目の文字種検証        |

- 呼び出し順の典型: `subCheckSubmit` → `resetErrors`/`initReset`/`resetSortIcon` → 入力検証（`subCheckAlphabetNumber`/`byteCheck`/`subCheckKanaByte`/`chkHanEngNum3`）→ `subSetSubmitFlg` → API → `subResultListInit`/`subListBtnDisabled` → `subInitSubmitFlg`(finally)。

---

## Step 4: 製造（コーディング）実行

**本ステップは Claude Code 自身が実行する。外部ツールへの交接は行わない。**

### 4.1 CLAUDE.md と禁止事項の再確認

製造開始前に `D:\AI_work_dev\CLAUDE.md` および `.claude/rules/` を読み込み、分工红线・禁止事項（案件固有 5 条）・commitメッセージ7様式を再確認する。特に以下の禁止事項を遵守する：

- 禁①：R60Common.ts / r60util.py の手改変禁止
- 禁②：BaseCamelModel 4行ConfigDict（alias_generator / populate_by_name / serialize_by_alias / extra）改変禁止
- 禁③：ids.yml未登録の野号（F/I/L/E/Dの飛び番や自作ID）禁止
- 禁④：trace_check --strict スキップ禁止
- 禁⑤：マスクされていない真正の機密情報（社員名・企業名・個人情報）を外のLLMに投げることは禁止、mask_demoを経由せよ

### 4.2 ids.ymlの読込みとD-ID払出し

対象のR-ID→F-ID→I-ID→L-ID/E-IDをids.ymlから読出し、D-ID（製造ID）を払い出す。D-IDはD-043（R60Area edit/delete登録系）を起点とする。

```yaml
D:
  D-043:
    f_id: F-042
    target: "R60_AREA_M_TBL SELECT/INSERT/UPDATE 物理設計（R60AreaController.py search+edit）"
    branch: "feature/D-043-R60Area-search-edit"
```

### 4.3 Git 7種子分岐モデル

trans-cosmos-ai では以下の7種のブランチを標準運用する：

| 分岐名                       | 用途                        | 命名規則                     |
|------------------------------|-----------------------------|------------------------------|
| main                         | リリース済安定版            | main                         |
| develop                      | 統合開発ベース              | develop                      |
| feature/R-ID                 | 要求単位機能分岐            | feature/R-101                |
| feature/F-ID                 | 機能単位小分岐              | feature/F-042                |
| feature/D-ID                 | 製造単位の最小分岐          | feature/D-043                |
| hotfix/YYYYMMDD-事象番号     | 緊急障害対応                | hotfix/20261008-001          |
| release/vX.Y.Z               | リリース準備                | release/v0.1.0               |

製造時は `feature/D-043-R60Area-search-edit` を作成し、そのブランチ上で実装する。

### 4.4 製造（コーディング）実行手順

Claude Code 自身が D-043 のコードを実装する。以下の**自然言語の製造指示テンプレート**を入力として、設計文書を正として実装を進める：

> **【製造指示 / D-043】**
> 対象: R60AreaController の search / edit / delete エンドポイント。
> 入力とする設計: L-014（検索ロジック）と L-015（initEdit/edit/delete の排他+参照+重複）を正とする。
> 準拠する既存資産: R60AreaService.ts の 7 メソッド、R60Area.vue onMounted のパターン、および本スキル §3.5 の R60Common.ts 関数マッピング表。
> 実装スタック: FastAPI + Pydantic + SQLAlchemy + oracledb Thin。`BaseCamelModel` の 4 行 `model_config` は改変しない。
> 遵守事項: 禁止事項5条（案件固有・§4.1）を厳守。R60Common.ts / r60util.py を改変せず、既存関数をそのまま呼び出す。SQL は §3.3/§3.4 のテンプレートに準拠し、値はプレースホルダで束縛する。
> 完了条件: 実装後、下記 §4.5 のトレース検証を実行し `Exit 0` を確認する。

実装は設計（L-014 / L-015）と既存パターンの写像として行い、設計に無い独自ロジックの追加や野号 ID の混入を行わない。

### 4.5 trace_check --strict による閉ループ検証

実装完了後、Claude Code 自身が必ず以下を実行してトレーサビリティ閉ループを検証する：

```
py -3 -m tools.trace_check --strict --report reports/trace_R101.json
```

検証項目：
- R-IDからD-IDまでが途切れなくつながっている（`chain_complete=true`）
- 各commitメッセージに正しいD-ID/F-ID/R-IDが埋め込まれている
- ids.ymlにない野号が出現していない
- R60Common.ts / r60util.py / BaseCamelModel 4行configの改変がない
- 機密情報の外投げがない（mask_demo通過済）

検証が `Exit 0` とならない場合は製造工程を完了とみなさず、人間のレビューは行わない。

以上、4ステップを Claude Code 自身が実行し、SKL-001 code-from-design-trans-cosmos-ai スキルを完了とする。各工程の出口で人間がレビュー／承認ゲート（要件合意・設計評審・合否判定・リリース判定）を保持する。

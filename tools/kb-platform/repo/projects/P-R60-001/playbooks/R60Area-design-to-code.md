---
id: PLAY-R60-001-R60AREA
type: knowledge
req_ids:
- R-101
status: baselined
sensitivity: internal
owner: AI-PG
version: 0.1.0
doc_id: r60-001-playbooks-r60area-design-to-code
scope: project
project_id: P-R60-001
title: R60Area 設計→製造 貫通例（BD/DD/製造の実値）
doc_type: howto
conf_level: 30
updated_at: 2026-10-29
generated_by: tools/kb_migrate.py
---

# R60Area 設計→製造 貫通例（BD/DD/製造の実値）

> この文書は **案件固有の値**（R-101 / F-042 / I-201..I-256 / D-043 / L-014 / L-015 / E-001..E-008、
> SQL テンプレート、既存実装の行番号）を持つ。**方法（順序・門番・禁止事項）は
> `.claude/skills/code-from-design-trans-cosmos-ai/SKILL.md` が持つ**。両者を混ぜないこと。
>
> 読む順序：方法 → `SKILL.md` ／ 案件の実値 → 本文書 ／ 共通部品の一覧 → `standards/r60common-map.md`
> ／ 操作 ID → `standards/r60const-action-id.md`

貫通例のトレース連鎖：
**R-101 → F-042 → I-201..I-256 → D-043 → L-014/L-015 → E-001..E-008 → TC-001..TC-008**

---

## 1. 参照先実装コード

| 対象 | 場所 | 本貫通例での役割 |
|---|---|---|
| 画面 | `R60Area.vue` の onMounted フック | 画面初期化の順序 |
| サービス | `R60AreaService.ts` の 7 メソッド | API 契約の実値 |
| 定数 | `r60const.py` の ACTION_ID 40 個 | 操作分類（→ `standards/r60const-action-id.md`） |
| 共通部品 | `R60Common.ts` の 16 関数 | 呼び出し規約（→ `standards/r60common-map.md`） |

> 実ファイルは旧案件側（読み取り専用）。本知識庫はその写しではなく**要約と対応表**を持つ。

---

## 2. コードとの対応付け（Step 1.2 の実例）

`R60Area.vue` onMounted（194 行目-238 行目）における画面初期化フローの基準点：

- onMounted 内の `dataService.init()` 呼出し（206 行目）→ `R60AreaService.init`
- 会社／事業場ドロップダウン設定（208-214 行目）
- ページ数ドロップダウン設定（217-218 行目）
- カラム定義設定（227-237 行目）

`R60AreaService.ts` の 7 メソッドと ACTION_ID の対応：

| No | メソッド名 | 用途 | 対応 ACTION_ID |
|----|-----------|------|----------------|
| 1 | init | 一覧画面初期化 | ACTION_ID_INIT |
| 2 | search | 検索処理 | ACTION_ID_SEARCH |
| 3 | download | CSV ダウンロード処理 | ACTION_ID_DOWNLOAD |
| 4 | initEdit | 入力画面初期化 | ACTION_ID_DIALOG |
| 5 | getPlcNm | ロケーション名称取得 | ACTION_ID_HEAD |
| 6 | delete | 論理削除処理 | ACTION_ID_DELETE |
| 7 | edit | 更新／登録処理 | ACTION_ID_REGIST / ACTION_ID_MODIFY |

---

## 3. ID の登録実値（Step 1.3 / 2.1 / 3.1）

本貫通例では機能は **F-042**（R60Area 全画面機能）1 件、画面項目は **I-201..I-256**
（56 件 = `R60_AREA_M_TBL` 56 列相当）である。

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

詳細設計側の登録実値：

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

---

## 4. テンプレートの実値（Step 2.2 / 3.2）

基本設計書の front matter：

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

詳細設計書の front matter：

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

---

## 5. BD 本体の記載項目（Step 2.3 の実例）

1. **画面構成**：`R60Area.vue` の template 構造（ヘッダー、Splitter 条件部／結果部、フッター、編集ダイアログ）
2. **画面項目一覧**：検索条件（会社、事業場、エリアコード、削除含む、1 頁件数）、
   結果一覧カラム（28 項目＋複製／送信／削除）
3. **権限制御**：`subListBtnDisabled` によるボタン活性制御、`KGN_KBN_Y/N` と自工／他工フラグの組合せ
4. **画面遷移**：一覧 → 新規／複製／修正ダイアログ（`R60AreaEdit.vue`）、業務終了ウィンドウクローズ
5. **共通部品呼出し**：`standards/r60common-map.md` の 16 関数の使い分け
   （呼び出し順の要は同書 §2 の 13 件）

---

## 6. SQL テンプレート（Step 3.3 / 3.4 の実例）

> 書き方の規約（許可ソート項目の白名单・値のプレースホルダ束縛・`ROWID` ページング）は
> `.claude/rules/03-design-coding.md` §5 が持つ。ここにあるのは**実値**である。

### 6.1 L-014（検索）— `R60AreaController.py:1499-1647`

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

### 6.2 L-015（編集初期化詳細取得）— `R60AreaController.py:1713-2915`

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

---

## 7. 製造指示の実例（Step 4.4）

> 以下は**例であり、様式の強制ではない**。案件が変われば対象・既存資産・スタックが変わる。

> **【製造指示 / D-043】**
> 対象: `R60AreaController` の search / edit / delete エンドポイント。
> 入力とする設計: L-014（検索ロジック）と L-015（initEdit/edit/delete の排他+参照+重複）を正とする。
> 準拠する既存資産: `R60AreaService.ts` の 7 メソッド、`R60Area.vue` onMounted のパターン、
> および `standards/r60common-map.md` の関数マッピング表。
> 実装スタック: FastAPI + Pydantic + SQLAlchemy + oracledb Thin。`BaseCamelModel` の 4 行 `model_config` は改変しない。
> 遵守事項: 禁止事項 5 条を厳守。`R60Common.ts` / `r60util.py` を改変せず、既存関数をそのまま呼び出す。
> SQL は §6 のテンプレートに準拠し、値はプレースホルダで束縛する。
> 完了条件: 実装後に `py -3 -m tools.trace_check --strict` を実行し `Exit 0` を確認する。

---

## 8. 出所

- 移設元：`docs/95_legacy/r60/`（2026-10-29 に削除。履歴は git にある）
- 本貫通例を含んでいたスキル定義書：`.claude/skills/code-from-design-trans-cosmos-ai/SKILL.md` v0.1.0
  （同 v0.2.0 で方法だけを残し、案件固有値を本文書へ移した）

---
id: PPT-WALKTHROUGH
type: knowledge
req_ids: [R-101]
status: baselined
sensitivity: internal
owner: AI-SE
version: 1.0.0
---

# 落地篇 PPT 示例 端到端走査（D1 → D7 実走記録）

> **根拠**: 《AI実践に基づくソフトウェア開発プロセスの再考_落地篇.pptx》
> — **S7「端到端走査」**（1 件の機能追加要望を 7 日でデリバリする例）
> — **S21 / S22 / S23**（基本設計・詳細設計・テスト仕様書の成果物例）
> — **S17**（人機分工 RACI：AI は実行主体、人は責任主体）
>
> **走査対象**: 朝日ビール R60 エリアマスタ（**R-101**）
> **実行環境**: Windows / `py -3`（Python 3.14.3 + pyyaml 6.0.3）
> **注記**: 本書のコマンド出力はすべて**実行時の実出力**である。机上の想定ではない。

---

## 0. この走査と PPT の関係（先に読む）

PPT S7 は「**D1 要件受領 → D7 報告・引渡**」の 7 日間で 1 機能を届ける流れを示している。
各日の末尾は**工程の区切り**であり、同時に**人が拍板するポイント**でもある（PPT S6/S17）。

PPT S21–S23 の成果物例は `F-042` / `L-014` / `TC-003` という ID を使っている。
本骨架は**同じ ID 体系をそのまま採用**して実装してあるので、ID レベルで 1 対 1 で対応する。

> **⚠ 1 点だけ正確に言っておく**: PPT のサンプルは「在庫引当／出荷数」という**説明用の創作例**である。
> 本骨架では同じ ID 群（R-101 / F-042 / I-201.. / D-043 / L-014 / E-00x / TC-00x）を
> **R60 の実案件である「エリアマスタ」に割り当てている**。
> したがって **ID の骨格は PPT と同一、中身は R60 の実業務**である。
> 以降、PPT のサンプル値を併記して「PPT ではこの形 → 本骨架ではこの実物」と対比する。

---

## 1. 登場人物と道具

| 役割 | 担当 |
|------|------|
| **Claude Code** | 8 工程の実行（読解・生成・検査・集計） |
| **人（SE）** | G1 要件合意 / G2 設計評審 / G5 リリース判定 |
| **人（PG）** | G3 コードレビュー |
| **人（テスター）** | G4 合否判定 |
| **門番** | `tools/trace_check`（6 重ゲート）— commit 前に必ず実行 |
| **発号元** | `docs/00_registry/ids.yml` — 全 ID の唯一の口 |

---

## 2. 走査本体（D1 → D7）

### 📅 D1 要件受領 — 工程① 要件理解

> **PPT の記述**: 日方要件定義書・メール → AI 読解要約・曖昧点抽出 → 要件構造化シート、確認事項一覧 → **SE 確認 → 日方へ質問**

**人が入力するもの**
- 日方の要件定義書・議事録・メール（`D:\AI_work\doc\02_INPUT/` の連携資料）
- 今回やらないことの当たり（スコープ上限）

**Claude Code への依頼（実際に投げた文）**
> `doc/02_INPUT/` の資料を読んで、業務フローと用語を抽出し、曖昧点・矛盾点・前提不足を Q-ID で列挙してください。
> 要件を構造化シートにし、ID は `docs/00_registry/ids.yml` で **R-ID を発号**してから `docs/10_requirements/` に置いてください。

**成果物**：`docs/10_requirements/R-101-R60Area.yaml`

```yaml
id: R-101
type: requirement
req_ids: [R-101]
status: baselined
...
background:        # 5 条（cmpCd+jigCd+araCd 三鍵 / 56 項目 / 排他 ksn_dat+rev_no / CSV / モード1・2・3）
business_rules:     # 5 条（REG_STS 15 項目判定 / 集中購買 concat / ロケ未登録 error_flg / 排他 / 被参照）
non_goals:          # 3 条
```

**人のゲート（G1 要件合意）— ここで答える**
- 確認事項一覧のうち、どれを日方に質問するか／自分で決めてよいか
- やらないことを明示したか（Non-Goals）
- 発号は `ids.yml` 経由か（**野号ゼロ**）

**実行した検証**
```console
$ py -3 -m tools.trace_check --strict --only-check id-chain
[trace_check] gate1=PASS gate2=PASS | total_ids=79 orphans=0 field_count=0
```
→ 結果: **R-ID の連鎖に野号なし**。合格サイン充足。

---

### 📅 D2 基本設計 — 工程② 基本設計

> **PPT の記述**: 要件構造化シート → AI 機能/画面/入出力一覧生成 → 基本設計書初稿 → **SE・日方レビュー**

**人が入力するもの**
- D1 の要件構造化シート（R-ID 確定済み）
- 日方の設計規約（`doc/02_INPUT/10.規約/`）

**Claude Code への依頼**
> R-101 から機能一覧・画面一覧を起こし、入出力一覧に **I-ID を付与**（型・桁・必須・由来要件 ID）してください。
> 非機能要件と制約のチェックリストを適用し、`docs/20_basic_design/` に置いてください。

**成果物**：`docs/20_basic_design/F-042-R60Area.yaml`

**PPT S21 のサンプルとの対比**（`req_ids: [R-101, R-102]` と `item_id: I-201 / name: 出荷数` が PPT の例）

| PPT の例 | 本骨架の実物 |
|---------|-------------|
| `feature_id: F-042` | `id: F-042`（一致） |
| `io_list: [{item_id: I-201, name: 出荷数, type: NUMBER(9,0)}]` | `input_ids: [I-201 … I-256]`（**56 項目**、名前は D-043 側で単一ソース管理） |
| `open_issues: [{id: Q-007, text: 端数処理は切捨てで良いか}]` | `open_issues: []`（**未解決の確認事項は無い**。F-042 の内容は骨架構築段階で内部確定させたため。ただし **Q-ID は 1 件も発号していない** — 日方との合意が必要な事項が生じた時点で `ids.yml` の `Q` プレフィックスで発号し、ここに載せる） |

**実行した検証**
```console
$ # F-042 の中身
F-ID: F-042 | screens: SCR-01 R60Area.vue(一覧検索) / SCR-02 R60AreaEdit.vue(登録修正複製ダイアログ)
             | I-IDs 56 | tables 7
```
→ 結果: **画面 2 枚・I-ID 56 項目・使用テーブル 7 本**。飞び番なし。

**人のゲート（G2 設計評審）**
- 機能の切り方・画面分割は業務に合っているか
- 入出力一覧に漏れ・余剰はないか（**飛び番禁止** = 紅线①）
- 日方との合意が必要な点を質問として立てたか

---

### 📅 D3 詳細設計 — 工程③ 詳細設計

> **PPT の記述**: 基本設計書 → AI 処理フロー/項目定義/SQL/エラー一覧生成 → 詳細設計書 → **PG レビュー**

**人が入力するもの**
- D2 の基本設計書
- 実装上の非機能制約（**排他・性能・桁あふれ** — AI が最も苦手な領域なので人が必ず補う）

**Claude Code への依頼**
> F-042 から処理フローを **L-ID 単位**に分割し、項目定義・テーブル定義・SQL 一覧・**エラー処理一覧（E-ID）**・境界値を生成してください。
> `docs/30_detail_design/` に置いてください。

**成果物**：`D-043-R60Area.yaml`（論理設計＋項目定義の単一ソース）／`L-014-R60Area-search.yaml`／`L-015-R60Area-edit.yaml`／`E-001-E005-R60Area.yaml`

**PPT S22 のサンプルとの対比**（PPT の `logic_id: L-014 / name: 在庫引当`, `errors: [{code: E-001, cond: 必須項目が空}]`）

本骨架の `L-014` は **search 業務（検索ロジック）**：

```yaml
logic_id: L-014
name: search 業務
sql_location: R60AreaController.py L1499-L1647
sort_whitelist: [CMP_CD, JIG_CD, ARA_CD]     # 白名单外は JIG_HYJ_SEQ にフォールバック
steps:    # 5 段
  - step: 1   name: online 使用可否チェック   lines: 1436-1437
  - step: 2   name: WHERE 条件組み立て        lines: 1450-1472
  - step: 3   name: 総件数 COUNT によるページ計算
  - step: 4   name: select_column 動的取得
  - step: 5   name: OFFSET-FETCH + ROWID ソート → 56 項目割当
```

**単一ソース原則の実証**（6 原則④）
```console
$ grep -rn "受払場所コード" docs/10_requirements docs/20_basic_design docs/30_detail_design | wc -l
1
```
→ 結果: **項目名の定義は D-043 の `io_definitions` に 1 箇所だけ**

```yaml
# D-043-R60Area.yaml（io_definitions は 56 項目）
- {item_id: I-206, jp_name: 受払場所コード, column_name: UKH_PLC_CD}
```
F-042 は `I-206` という ID でしか参照しない。**同じ情報を二箇所に書かない**（不整合の温床を作らない）。

**人のゲート（G2 設計評審・続き）**
- 分岐条件は実業務と一致するか
- **排他制御・性能**の設計判断（AI の最弱領域）
- エラー一覧の網羅（異常系の漏れ）
- 上記 grep が 1 であること

---

### 📅 D4 製造 — 工程⑤ 製造（コーディング）

> **PPT の記述**: 詳細設計書 → AI ソース＋単体テストコード生成、静的解析 → **PG コードレビュー**

**人が入力するもの**：**無し**。設計が確定していれば人は入力を足さない。
（PPT S6 の「人は要件定義とレビューに約 6 割」に対応 — 製造は AI の独壇場）

**Claude Code への依頼**（CLAUDE.md §5 のテンプレート）
> `L-014` / `L-015` を読んで実装してください。**設計は変更せず、実装のみ**。
> `R60Common.ts` の既存関数にマッピングし、並行新版は作らないこと。
> 完了後に `py -3 -m tools.trace_check --strict` を実行し結果を報告してください。

**成果物**：`R60AreaController.py` の該当エンドポイント実装 ＋ 設計-コード対応表（`L-014` → `1499-1647`、`L-015` → `1713-2915`）

**PPT S12 の「設計-コード対応表を自動生成」の実装**：`docs/30_detail_design/*.yaml` の `sql_location` がそのまま対応表になっている。

**人のゲート（G3 コードレビュー）**
- 実装が L-ID の記述どおりか
- 例外処理の握り潰しがないか
- **禁止事項 5 条**（案件固有）（`R60Common.ts` 改変 / `BaseCamelModel` 変更 / 野号 / `trace_check` 跳过 / 未マスク外部送信）

---

### 📅 D5 単体テスト — 工程⑥ 単体テスト

> **PPT の記述**: 生成ソース → AI テスト実行/集計/原因候補提示 → 結果＋カバレッジ → **PG が合否判定**

**人が入力するもの**
- 業務上ここは絶対に外せない、という観点の勘所

**Claude Code への依頼**
> L-014/L-015 からテスト観点（同値分割・境界値・デシジョンテーブル）を生成し、
> **正常 3 / 境界 2 / 異常 3** の比率で TC を作ってください。各 TC に `design_ids` と `req_ids` を必ず付けてください。
> （`trans-cosmos-ai-node6-unit-test` サブエージェントに任せると比率と観点技法が強制される）

**成果物**：`docs/50_unit_test/TC-001-TC-008-R60Area.yaml`

**PPT S23 のサンプルとの対比**（PPT の `case_id: TC-003 / design_id: D-043 / req_id: R-101 / viewpoint: 境界値 / precondition: 在庫なし / input: 出荷数 = 1 / expected: E-003 警告を表示 / coverage: {req: 100%, viewpoint: 94%}`）

| PPT の字段 | 本骨架の実装 |
|-----------|-------------|
| `case_id: TC-003` | `TC-003`（既存修正・正常系） |
| `design_id` / `req_id` | `design_ids: [D-043, L-015]` / `req_ids: [R-101]` |
| `viewpoint: 境界値` | `viewpoint`（同値分割 / 境界値 / デシジョンテーブル） |
| `expected: E-003 警告` | `expected_output` に E-ID を記載（TC-006→E-003 重複、TC-008→E-006 ロケ未登録） |

**実行した検証**
```console
$ # TC の分布と design_ids の有無
TC count 8 | all have design_ids: True
分類内訳: 正常 3 / 境界 2 / 異常 3     ← PPT S13 の最低標準どおり
```
→ 結果: **比率・出典ともに合格**。PPT S23 の「全ケースに期待値の出典（設計 ID）を紐付」を満たす。

**人のゲート（G4 合否判定）**
- 観点の妥当性（業務上重要な観点が落ちていないか）
- **落ちた原因は実装バグかテストの誤りか**（診断は人）
- **合否判定そのもの**（AI は候補提示まで）
- 未検証観点の把握

---

### 📅 D6 結合テスト — 工程⑦ 結合・総合テスト

> **PPT の記述**: 詳細設計書・テスト観点 → AI 仕様書＋データ生成、エビデンス整理 → 結合テスト仕様書 → **テスター観点レビュー**

**人が入力するもの**
- 業務シナリオ（どの業務の流れを検証するか）
- 日方と合意した観点

**Claude Code への依頼**
> R60Area の 7 接口（init → search → initEdit → getPlcNm → edit → delete → download）で IT-001 を作ってください。A/B 比較の断言対象は 3 主キー＋業務項目としてください。

**成果物**：`docs/60_integration_test/IT-001-R60Area-e2e.yaml`

```yaml
api_sequence:   # 7 步骤
  - {step: 1, method: POST, path: /R60Area/init,     expect: 通常初期化（会社・事業場・1頁件数・メッセージ）}
  - {step: 2, method: POST, path: /R60Area/search,   ...}
  - {step: 3, method: POST, path: /R60Area/initEdit, ...}
  - {step: 4, method: POST, path: /R60Area/getPlcNm, ...}
  - {step: 5, method: POST, path: /R60Area/edit,     ...}
  - {step: 6, method: POST, path: /R60Area/delete,   ...}
  - {step: 7, method: POST, path: /R60Area/download, ...}
ab_comparison_assert_fields:   # A/B 比較断言（cmp_cd/jig_cd/ara_cd 3 主キー + 業務項目）
```

**人のゲート（G4 合否判定）**
- シナリオが実業務の流れを再現しているか
- 日方との観点合意
- **合否判定**（人の責任）
- 障害の重要度判断

---

### 📅 D7 報告・引渡 — 工程⑧ リリース・運用保守

> **PPT の記述**: テスト結果 → AI 結果報告書＋リリースノート生成 → **テスター判定 → 日方報告**

**人が入力するもの**
- リリース可否の判断材料（残課題・障害状況）

**Claude Code への依頼**
> `docs/70_release/release-template.md` に沿ってリリース手順書と切戻し手順を作ってください。

**成果物**：`docs/70_release/release-template.md`（リリースノート・切戻し手順・baseline tag）／`docs/80_operation/operation-runbook.md`／`reports/`

**実行した検証（全 6 ゲート）**
```console
$ py -3 -m tools.trace_check --strict --gate 6
[trace_check] gate1=PASS gate2=PASS gate3=PASS gate4=PASS gate5=PASS gate6=PASS
              | total_ids=79 orphans=0 field_count=56
```
→ 結果: **R-101 → F-042 → I-201..256 → D-043 → L-014/L-015 → E-001..008 → TC-001..008 の全链路に断線なし**。

**人のゲート（G5 リリース判定）**
- **リリース判定**（人の責任・最終判断）
- **本番作業**（AI に本番操作を委ねない）
- 切戻し手順が実際に実行可能か
- 顧客に説明できるか

---

## 3. 走査結果の総括

| 日 | 工程 | 成果物（実ファイル） | 人のゲート | 結果 |
|---|------|-------------------|-----------|------|
| D1 | 要件理解 | `docs/10_requirements/R-101-R60Area.yaml` | G1 要件合意 | ✅ 野号ゼロ |
| D2 | 基本設計 | `docs/20_basic_design/F-042-R60Area.yaml` | G2 設計評審 | ✅ 56 I-ID / 7 テーブル |
| D3 | 詳細設計 | `docs/30_detail_design/` 4 ファイル | G2 設計評審 | ✅ 単一ソース grep == 1 |
| D4 | 製造 | 実装 ＋ 設計-コード対応表 | G3 コードレビュー | ✅ 禁止事項 5 条 |
| D5 | 単体テスト | `docs/50_unit_test/TC-001-TC-008-*.yaml` | G4 合否判定 | ✅ 3/2/3・出典あり |
| D6 | 結合テスト | `docs/60_integration_test/IT-001-*.yaml` | G4 合否判定 | ✅ 7 API シーケンス |
| D7 | リリース | `docs/70_release/`・`reports/` | G5 リリース判定 | ✅ 6 ゲート全 PASS |

**PPT S7 の 7 日間が、本骨架では上記の実ファイル群に対応する。**
人の関与は各日の末尾のゲートに集中し、生成・整理・検査は Claude Code が担う。

---

## 4. 自分で追試するには

上の走査は**既に構築済みの成果物に対する実走**である。**ゼロから自分で作る**手順は
`docs/90_knowledge/onboarding-checklist.md` の 10 ステップにある。
あちらは **R-102 / F-043 / L-016 / E-009 / TC-009** を新規発号して 1 周させる練習問題になっている。

```console
# 追試の入口（新人 Walkthrough の手順⑩）
$ py -3 -m tools.gen_formal.gen_excel --dry-run --module R-101
[gen_formal] field_count=56 | output_columns=ara_cmp_list_56items.csv
$ py -3 -m tools.masking.mask_demo --self-test
[mask_demo] mask_hits=11 unmask_ok=true exit=0
```

---

## 5. PPT 成果物例（S21–S23）と本骨架の対応まとめ

| PPT のスライド | PPT のサンプル | 本骨架の対応物 | 形状の一致 |
|---------------|---------------|--------------|-----------|
| S21 基本設計書 | `F-042` + `io_list[I-201]` + `open_issues[Q-007]` | `docs/20_basic_design/F-042-R60Area.yaml` | ✅ 機能 ID・入出力 ID。**未確定事項のみ不一致** — PPT は `Q-007` を持つが、本骨架の F-042 は `open_issues: []`（Q-ID 未発号。§3 の表を参照） |
| S22 詳細設計書 | `L-014` + `steps[S1: cond/then/else]` + `errors[E-001]` | `docs/30_detail_design/L-014-R60Area-search.yaml` | ✅ ロジック ID・段階・エラー |
| S23 テスト仕様書 | `TC-003` + `design_id/req_id` + `coverage` | `docs/50_unit_test/TC-001-TC-008-R60Area.yaml` | ✅ ケース ID・出典 ID・観点 |
| S19 成果物マップ | 工程×成果物×形態×レビュア | `docs/90_knowledge/ai-dev-playbook.md` §4 | ✅ |
| S20 成果物 6 原則 | 構造化 / ID 付与 / 入出力明示 / 単一ソース / 二重形態 / 前提明示 | gate1・gate3・gate5 が機械検査 ＋ 人がレビュー | ✅ |
| S7 端到端走査 | D1–D7 | **本書** | ✅ |

> **結論**: PPT の「ID 付与された構造化成果物」という形は、本骨架では*説明用サンプル*ではなく
> **実際に動く YAML ファイル**として存在し、`trace_check` が毎回その整合を機械検証している。

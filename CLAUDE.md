# CLAUDE.md — trans-cosmos-ai AI 全流程開発 唯一真源（Claude Code 単一ツール）

> 本ファイルは**二つの要件源**に基づく骨架の入口である。
> **① 認知・範式層**：《基于统一 AI 平台的全生命周期软件工程方案_v1》（中文 13 页）— 痛点・誤解・思考転換・
> 統一プラットフォーム四層（接入／能力編排／知識庫／模型網関）。対応付けは `docs/90_knowledge/v1-platform-4layer.md`。
> **② 工程・実装層**：《AI実践に基づくソフトウェア開発プロセスの再考_落地篇 30 页》PART01-PART04 の落地細則。
> 両者は**互いに表裏**（v1＝宏观の認知共有 → 落地篇＝微观の工程細則）であり、片方だけでは片翼である。
> **統合版**：`AI全链路软件工程平台_实施规格书.md`（根目录）——上記 2 份 PPT を 1 本に統合した実施规格书。
> **4 層知識モデル（§11.3）・7 層プラットフォーム（§11.1）・8 工程・成果物 6 原則（§9.2）** の語彙はこの文書を正とする。
> 本骨架の資産がそのどの層に属するかは `docs/90_knowledge/platform-map.md` が唯一の対応表である。
> **PPT に対する追加要素・差異は `docs/90_knowledge/ppt-deviation-register.md` が唯一の登録簿**である。
> 同表に無い追加要素は「PPT 準拠」と誤認されるため、追加したら必ず 1 行足すこと。
> **既定の案件形態は新規構築（從無到有／`greenfield`）**である。〈初回案件: 朝日ビール R60 共通マスタ〉は既存システム・旧設計書を持つ**特例（`migration` 変種）**であって、既定ではない。成果物 6 原則と、工程をまたいで守るべき **7 条红线** を定める。
> **ツール構成**：Claude Code 単一。8 工程すべてを Claude Code が実行し、人はレビューゲートで拍板する（詳細は §0）。
> **案件形態**：既定は `greenfield`（從無到有）。既存システム・旧設計書がある案件は `migration` 変種として、
> `docs/00_plan/coach/<module>/case.yml` に明示宣言する（唯一の宣言場所）。
> **対象スタック**：骨架は値を固定しない。`migration` は案件プロファイル（`docs/01_context/case-profile-<案件>.yaml`）が与え、
> `greenfield` は工程 04 で人が承認して確定する（紅线④）。
> **ID 発号の唯一口**：`docs/00_registry/ids.yml`。要件 R-101／機能 F-042／画面項目 I-201..I-256／データ D-043／
> ロジック L-014・L-015／エラー E-001..E-008／テスト TC-001..TC-008。
> **工程管理系の計画文書**：`docs/00_plan/`（spec.md / tasks.md / review.md）。

---

## 0. ツール構成と設定の所在

Claude Code が 8 工程（要件理解・基本設計・詳細設計・框架構築・製造・単体テスト・結合総合テスト・リリース運用保守）を
すべて実行する。**人は「実行」ではなく「拍板」を担う** — AI は実行主体、人は責任主体。

| 設定 | 場所 | 役割 |
|------|------|------|
| プロジェクト記憶 | `CLAUDE.md`（本ファイル） | 常時ロードされる中核制約。簡潔に保つ |
| 工程別ルール 7 份 | `.claude/rules/` | 起動時に自動ロード。各工程の詳細規約（`00` 総則／`01` 機密／`02` 要求管理／`03` 設計製造／`04` テスト／`05` commit／`06` 知識飛輪） |
| スキル | `.claude/skills/` の 5 つ（`code-from-design-trans-cosmos-ai`・`trans-cosmos-ai-lifecycle-coach`・`legacy-r60-navigator`・`virtual-requirement-author`・`requirement-interrogator`） | 設計→製造パイプライン（description で自動起動）／8 工程の伴走進行役（進捗は `docs/00_plan/coach/<module>/` に 1 ノード 1 ファイル）／歴史案件の読取専用ナビゲータ／**節点 0**＝節点1 の入力を実在資産から倒推して作る（8 工程の外側。`build_mode: migration` では使わない）／**要求書審査**＝顧客の要求書から「確認すべき点」を立てる（実在案件の QA 票 177 件から抽出した 51 の観点。真案件で使う本命） |
| サブエージェント | `.claude/agents/` | **検証系**：`spec-reviewer` / `secret-auditor` / `deliverable-reviewer` / `drill-comparator`（訓練の対比・帰因。合否は判定しない）/ `legacy-module-surveyor`（旧案件モジュールの選型普查）。**工程実行系**：`trans-cosmos-ai-node1-requirements` … `trans-cosmos-ai-node8-release-ops` と旁路環 `trans-cosmos-ai-node9-change`（各工程の産出を独立コンテキストで担い、`trans-cosmos-ai-lifecycle-coach` が派発する）。**テスト設計の専用 agent は置かない**（工程 06 の実行体が担う） |
| 成果物の変換 | `tools/gen_view/`・`tools/gen_formal/` | 機読源 → 人向けビュー（`gen_view`）／日文正式 Excel（`gen_formal`・Phase1 は dry-run のみ） |
| 権限・フック | `.claude/settings.json`（共有）／`settings.local.json`（個人・gitignore 済） | 門番コマンドの権限、機密ファイルの参照禁止 |
| 計画文書 | `docs/00_plan/` | spec / tasks / review（旧 Trae Spec Mode 成果物の移設先） |

> **不熟悉的人从根目录 `使用手册.md` 的「三分钟版」一节开始。** 那里是**唯一的门**：8 工程怎么走、
> 说哪 10 句话、哪些文件夹不用打开、QA 指摘来了走哪条环，全在那一节。（原 `START_HERE.md` 已于
> 2026-10-28 并入 `使用手册.md`，那个文件不再单独存在。）**本文件（CLAUDE.md）是给 AI 与治理看的
> 常时约束，不是给第一次上手的人看的**。新人不必先读懂本文件。
>
> 人向けの役割定義書は `docs/00_plan/roles.md`（旧 `AGENTS.md`。2026-10-28 に移設・入庫）。
> Claude Code はこれを自動ロードしない。要点は `使用手册.md` の「角色与分工」にある。

---

## 1. 7 条红线（工程横断・これだけは越えない）

| # | 红线 | 根拠 |
|---|------|------|
| ① | **野号禁止**：R/F/I/D/L/E/TC の全 ID は `docs/00_registry/ids.yml` からのみ発号する | NFR-1 単一ソース |
| ② | **設計なき製造禁止**：詳細設計（D/L/E）が確定する前に製造工程へ進まない | 工程順序の厳守 |
| ③ | **人の評審ゲート無承認で次工程へ進まない**：要件合意・設計評審・合否判定・リリース判定の 4 点 | 人は責任主体 |
| ④ | **スタックの無断変更禁止**：`migration` は案件プロファイル（`docs/01_context/case-profile-*.yaml`）が与える既存スタック、`greenfield` は工程 04 で人が承認した採用スタックを、以降の人の承認なく置換・変更しない（値は案件ごとに異なる） | Constraints Technical |
| ⑤ | **出典なきテストケース禁止**：全 TC は `design_ids`（D/L と E）と `req_ids` を必ず持つ | NFR-3 追跡閉ループ |
| ⑥ | **`trace_check --strict` なき commit 禁止**：`--skip` による門隙突破も禁止 | AC-2 / AC-6 |
| ⑦ | **未マスクの機密外投禁止**：外部送信前に `tools/masking/mask_demo.py` を通す | NFR-2 機密紅線 |

---

## 2. 禁止事項（全案件共通 3 条 ＋ 案件固有 2 条）

> **禁③④⑤ は全案件共通**（ID 単一ソース・工程順序・機密）。ここが唯一真源である。
> **禁①② は `migration` 案件固有**（既存資産を改変しない）。既定の `greenfield` では適用対象が無い。
> R60 の実値（`R60Common.ts` 54 関数・`BaseCamelModel` の 4 行）は
> **案件プロファイル `docs/01_context/case-profile-R60.yaml` §2 が唯一真源**。ここには書かない。

- **禁③**：`ids.yml` 未登録の **野号**（飛び番・自作 ID）を引入しない。
- **禁④**：`trace_check --strict` を跳过しない。
- **禁⑤**：マスク未処理の敏感値を外抛しない（`PWD_1` / `IP_1` / `TBL_1` 等へ占位化）。
- **禁①／禁②**：案件プロファイル §2 を参照（`migration` のみ）。

---

## 3. commit 7 種格式（種別固定・Trace/AI/Review 三段必須）

種別は `req` / `design` / `feat` / `test` / `fix` / `rel` / `chore` の 7 種のみ。末尾に attribution 行（§6）を付す。

- req: R-101 エリアマスタ要求を登録 | Trace:R-101 | AI:code-from-design-trans-cosmos-ai@v0.1 | Review:SE-001
- design: F-042 基本設計（一覧+登録修正複製 2 画面）を確定 | Trace:R-101->F-042->I-201..I-256 | AI:code-from-design-trans-cosmos-ai@v0.1 | Review:SE-001
- feat: D-043 R60AreaController の search/edit を製造 | Trace:F-042->D-043->L-014,L-015 | AI:code-from-design-trans-cosmos-ai@v0.1 | Review:PG-002
- test: TC-001..TC-008 単体テスト設計を追加 | Trace:L-014,L-015->E-001..E-008->TC-001..TC-008 | AI:code-from-design-trans-cosmos-ai@v0.1 | Review:TEST-003
- fix: KSN_DAT 不一致の排他処理を修正 | Trace:L-015->E-002 | AI:code-from-design-trans-cosmos-ai@v0.1 | Review:PG-002
- rel: release/v0.1.0 リリース準備（Phase1） | Trace:R-101 全链路 | AI:code-from-design-trans-cosmos-ai@v0.1 | Review:SE-001
- chore: .gitignore に masking_dict.json を追加 | Trace:none | AI:code-from-design-trans-cosmos-ai@v0.1 | Review:AI-004

`Review:` には**人の拍板者**の識別子を書く（AI ではない）。これが红线③の機械可読な証跡になる。

---

## 4. 設計成果物の位置（R60Area 貫通例）

- 検索ロジック **L-014**：`docs/_samples/30_detail_design/L-014-R60Area-search.yaml`
  → 実装対応 `R60AreaController.py:1499-1647`（総件数 COUNT + OFFSET/FETCH ページング、`ALLOWED_SORT_FIELDS` 白名単）。
- 編集ロジック **L-015**：`docs/_samples/30_detail_design/L-015-R60Area-edit.yaml`
  → 実装対応 `R60AreaController.py:1713-2915`（排他 + 被参照 + 重複 + ロケ確認 + REG_STS 判定 + 緊急配信）。
- データモデル **D-043**：`docs/_samples/30_detail_design/D-043-R60Area.yaml`（`R60_AREA_M_TBL` の SELECT/INSERT/UPDATE、項目名の単一ソース）。
- エラー **E-001..E-008**：`docs/_samples/30_detail_design/E-001-E005-R60Area.yaml`。
- 要求・基本設計：`docs/_samples/10_requirements/R-101-R60Area.yaml` / `docs/_samples/20_basic_design/F-042-R60Area.yaml`。

---

## 5. Claude Code への依頼テンプレート（自然言語・CLI フラグではない）

```
docs/00_registry/ids.yml、docs/_samples/30_detail_design/L-014-R60Area-search.yaml、
docs/_samples/30_detail_design/L-015-R60Area-edit.yaml を読んでください。

D-043 として R60AreaController の search / edit エンドポイントを実装します。
R60AreaService.ts の 7 メソッドと R60Area.vue onMounted のパターンに合わせ、
FastAPI + SQLAlchemy + Oracle で書いてください。

守ること:
- CLAUDE.md §2 の禁止事項 5 条（案件固有）
- commit は §3 の 7 種様式 + Trace/AI/Review 三段
- 設計（D-043 / L-014 / L-015）は変更しない。実装のみ。
- 完了後に py -3 -m tools.trace_check --strict を実行し、結果を報告すること。
```

受け入れ条件：`trace_check --strict` が Exit 0、`chain_complete=true`、`orphan_ids=[]`、`field_count=56`。

---

## 6. commit attribution 規則（必須）

- すべての `git commit` メッセージ末尾に次の行を必ず追加する：

  `Co-Authored-By: Claude Code <noreply@anthropic.com>`

- 例：

  ```text
  feat: D-043 R60AreaController の search/edit を製造

  Trace:F-042->D-043->L-014,L-015
  AI:code-from-design-trans-cosmos-ai@v0.1
  Review:PG-002

  Co-Authored-By: Claude Code <noreply@anthropic.com>
  ```

- Pull Request の説明末尾には `🤖 Generated with [Claude Code](https://claude.com/claude-code)` を付与する。

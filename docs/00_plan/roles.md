# AGENTS.md — AI Agent 角色一覧（trans-cosmos-ai AI 全流程骨架 / 既定: 從無到有の新規構築）

本文件定义 trans-cosmos-ai 全流程中参与协作的 AI／人角色、各自职责边界、以及每个角色可直接复用的「启动 Prompt 模板」。**本文件の内部実行役割 8 つはすべて Claude Code が実行する**（工程内只有一个 AI 工具）。これに加えて、**社外の発注者である「日方顧客」を役割として併記する**（実行はせず、各ゲートで合意を与える主体）。人は各工程のレビュー・承認ゲート（要件合意・設計評審・合否判定・リリース判定）で拍板する。所有角色共用同一发号口 `docs/00_registry/ids.yml`。設計→製造パイプライン Skill `.claude/skills/code-from-design-trans-cosmos-ai/SKILL.md`（Skill 名 `code-from-design-trans-cosmos-ai`）は **`build_mode: migration` 案件向け**である（既定の `greenfield`＝從無到有 では既存共通部品が無く、共通部品を本案件で新規定義するため発動しない）。機密点検・Review 独立検査・成果物還流・訓練対比・旧資産普查の 5 役割には専用サブエージェント（`.claude/agents/secret-auditor.md` / `.claude/agents/spec-reviewer.md` / `.claude/agents/deliverable-reviewer.md` / `.claude/agents/drill-comparator.md` / `.claude/agents/legacy-module-surveyor.md`）を割り当てる。**テスト設計には専用 agent を置かない** —— 工程 06 の実行体 `trans-cosmos-ai-node6-unit-test` が担う（比率と観点技法は `04-testing.md` が強制する）。訓練の入力（仮想需求書）は `.claude/skills/virtual-requirement-author/` が実在資産から倒推して作る（**8 工程の外側＝節点 0**。`build_mode: migration` では使わない）。分工红线参见根目录 `CLAUDE.md`：Claude Code が 8 工程すべてを実行し、人はレビュー・承認ゲートで拍板する。

> **注記**：Claude Code は `CLAUDE.md` が存在する場合 `AGENTS.md` を自動ロードしない。本ファイルは人向けの役割定義ドキュメントとして維持する。

## 0. 角色总览

| # | 角色 | 主体 | 主要工序 | 依据 Skill / 资产 |
|---|------|------|----------|-------------------|
| 1 | 上流SE | Claude Code（人ゲート: 要件合意・設計評審） | 要件理解 / 基本設計 | `code-from-design-trans-cosmos-ai`（Step 1-2） |
| 2 | 下流PG | Claude Code | 製造 / コードレビュー | `code-from-design-trans-cosmos-ai`（Step 4） |
| 3 | テスト設計担当 | Claude Code（`.claude/agents/trans-cosmos-ai-node6-unit-test.md`） | 単体テスト / 結合総合テスト | `code-from-design-trans-cosmos-ai`（Step 3） |
| 4 | AI推進担当 | Claude Code（人ゲート: 全体統制） | 模板・Skill 維持・度量 | `code-from-design-trans-cosmos-ai` 全 Step |
| 5 | 機密点検担当 | Claude Code（`.claude/agents/secret-auditor.md`） | 全工程（ゲート） | `tools/masking/mask_demo.py` |
| 6 | Review 独立検査担当 | Claude Code（`.claude/agents/spec-reviewer.md`） | 全工程（独立検証） | `tools/trace_check.py --strict` |
| 7 | 成果物還流担当 | Claude Code（`.claude/agents/deliverable-reviewer.md`） | 成果物可読化・顧客確認依頼書 | `tools/gen_view` |
| 8 | 訓練対比担当 | Claude Code（`.claude/agents/drill-comparator.md`） | 訓練の対比・帰因（8 工程の外側を横断。合否は判定しない） | `.claude/agents/drill-comparator.md` |
| — | **日方顧客** | **人（社外・発注者）** | 要件合意 / 設計評審 / 合否判定 / リリース判定 | — |

> **日方顧客 の位置づけ**：PPT 第 S6 页（六角色）および S17 页（RACI）は **日方顧客** を明示的な役割として置く。
> 本表の #1〜#8 は**骨格内部の実行役割**であり、日方顧客はその**外側**にいて各ゲートで合意を与える主体である。
> したがって番号を振らず、末尾に `—` として併記する。RACI の列としては §7 に含める。
> PPT 第 S6 页の六角色との対応：#1=SE（上流）／#2=PG（製造）／#3=テスター／#4=AI 推進担当（新設）／
> #5=統制・セキュリティ（新設）の**機密部分**／日方顧客。
> ただし PPT の「統制・セキュリティ」は **監査・権限設計**まで含むのに対し、本骨格の #5 は
> **マスキングと機密走査まで**しか実装していない（残りは `ROADMAP_3PHASE.md` Phase2 項）。
> また #6（Review 独立検査）・#7（成果物還流）・#8（訓練対比）は **PPT に対応する役割が無い本骨架独自の追加**である。

---

## 1. 上流SE（要件理解 / 基本設計）

- **責務**：R-ID の発号と要件確定、F-ID への機能分解、I-ID（画面項目）の確定。ID は `ids.yml` のみで発号し野号を排除。
- **成果物**：`docs/_samples/10_requirements/R-101-R60Area.yaml`、`docs/_samples/20_basic_design/F-042-R60Area.yaml`。
- **红线**：機能・画面項目の欠落番号禁止。設計の真源は本リポジトリの `.claude/skills/`・`.claude/rules/`（Claude Code）。人の要件合意・設計評審ゲートを経て次工程へ進む。

### 启动 Prompt 模板

```
あなたは trans-cosmos-ai 案件の上流SE です。Claude Code Skill「code-from-design-trans-cosmos-ai」の Step 1-2 を実行してください。
入力: 要件メモ（対日受託・R60Area マスタ）
やること:
1) docs/00_registry/ids.yml を確認し、未発号なら R-101 を発号（野号厳禁）。
2) 要件を F-042（R60Area 全画面機能）へ分解、I-201..I-256 を画面項目として登録。
3) docs/_samples/10_requirements/R-101-R60Area.yaml と docs/_samples/20_basic_design/F-042-R60Area.yaml を front-matter 7項目付きで出力。
制約: CLAUDE.md の禁止事項5条を厳守。敏感情報は mask_demo で占位化。
```

---

## 2. 下流PG（製造 / コードレビュー）

- **責務**：詳細設計（D-043 / L-014 / L-015）に従い、`feature/D-xxx` 分岐でコードを製造。製造は Claude Code が担当。設計は変更しない。
- **成果物**：`R60AreaController.py` の search/edit 実装、コミット（Trace/AI/Review 三段付き）。
- **红线**：`R60Common.ts`・`BaseCamelModel.model_config` 不変、野号禁止、trace_check 必須。

### 启动 Prompt 模板

```
あなたは R60 プロジェクトの下流PG（Claude Code 製造担当）です。Claude Code Skill Step 4 の製造工程を実行してください。
入力: docs/_samples/30_detail_design/L-014-R60Area-search.yaml, L-015-R60Area-edit.yaml, docs/00_registry/ids.yml
やること:
1) branch feature/D-043-R60Area-search-edit を作成。
2) R60AreaService.ts の 7メソッド（init/search/download/initEdit/getPlcNm/delete/edit）に合わせ、
   FastAPI+SQLAlchemy+Oracle で R60AreaController の search/edit を実装。
3) commit は「feat: ... 」形式 + Trace/AI/Review 三段 + Co-Authored-By。
制約: 設計改変禁止。R60Common.ts / BaseCamelModel.model_config 不変。実装後 trace_check --strict R-101。
```

---

## 3. テスト設計担当（単体テスト / 結合総合テスト）

- **責務**：D-043 / L-014 / L-015 / E-001..E-008 からテスト観点を設計し、TC-001..TC-008 を発号・作成。合否判定も担当。
- **成果物**：`docs/_samples/50_unit_test/TC-001-TC-008-R60Area.yaml`、`docs/60_integration_test/`。
- **红线**：テストは E-ID（エラー）と L-ID（ロジック）へ必ず trace させる。

### 启动 Prompt 模板

```
あなたは R60 プロジェクトのテスト設計担当です。Claude Code Skill Step 3 のテスト観点設計を実行してください。
入力: docs/30_detail_design/L-014-*.yaml, L-015-*.yaml, E-001..E-008
やること:
1) L-014/L-015 と E-001..E-008 を網羅する観点表を作成（正常/境界/異常）。
2) TC-001..TC-008 を ids.yml に発号し、docs/_samples/50_unit_test/TC-001-TC-008-R60Area.yaml を出力。
   各 TC は r_id/d_id/l_id/e_id を必ず持つ。
3) 結合・総合テスト観点は docs/60_integration_test/ に整理。
制約: 野号禁止。TC-ID は連番で再利用禁止。
```

---

## 4. AI推進担当（模板 / Skill 維持 / 度量）

- **責務**：`.claude/skills/code-from-design-trans-cosmos-ai/SKILL.md`、テンプレート、rules を維持し、ID 体系の単一源を保護。KPI／ROI の度量。
- **成果物**：Skill 更新、`docs/90_knowledge/` ナレッジ、オンボーディング整備。
- **红线**：Skill 内の ID は必ず `ids.yml` と一致させる（F-042 / I-201..I-256 / D-043 / L-014・L-015 / E-001..E-008）。

### 启动 Prompt 模板

```
あなたは R60 プロジェクトの AI推進担当です。
入力: .claude/skills/code-from-design-trans-cosmos-ai/SKILL.md, docs/00_registry/ids.yml
やること:
1) SKILL.md 内の全 ID 参照を ids.yml と突合し、不一致（野号/飛び番）を修正。
2) 4ステップ構造（R-ID受理→BD生成→DD生成→製造交接）と R60Common 関数表・ACTION_ID 一覧を維持。
3) オンボーディング手順と KPI（削減率・品質）を docs/90_knowledge/ に追記。
制約: R60Common 関数数・ACTION_ID 数を減らさない。ID を新規に発明しない。
```

---

## 5. 機密点検担当（セキュリティゲート）

- **責務**：全工程の成果物・コミットに対し機密 3 級（公開可／要脱敏／禁止外投）を点検。外部 LLM 送信前の脱敏を承認。
- **成果物**：脱敏済占位（PWD_1 / IP_1 / BUCKET_1 / TBL_1 等）、点検記録。
- **红线**：`.claude/rules/01-security-redlines.md` の L3 禁止外投 13 条。筋書きのない敏感値の外投絶対禁止。

### 启动 Prompt 模板

```
あなたは R60 プロジェクトの機密点検担当です。
入力: 対象成果物/差分, .claude/rules/01-security-redlines.md, tools/masking/
やること:
1) 対象ファイルに対し機密パターン（内部 IP・接続ユーザ／パスワード・スキーマ名。実値は記載せず `IP_1`／`PWD_1`／`TBL_1` で代表）をスキャン。
2) ヒットしたら tools/masking/mask_demo.py で占位化（TBL_1/COL_1/PWD_1/KEY_1/MASKED）。
3) 脱敏後も双方向に復元可能かを確認し、点検結果を記録。1件でも残れば commit を差し戻す。
制約: masking_dict.json は Git に入れない（NFR-2）。
```

---

## 6. Review 独立検査担当（独立検証）

- **責務**：製作者とは独立に、トレーサビリティ閉ループ・front-matter 7 項目・野号ゼロ・禁止事項遵守を検証。4 級验收（rule/rubric 等）の合否を独立に判定。
- **成果物**：`reports/trace_R101.json`、検査チェックリスト。
- **红线**：`trace_check --strict` Exit 0 が合格条件。検査役は製造者と兼任しない。

### 启动 Prompt 模板

```
あなたは R60 プロジェクトの Review 独立検査担当です。製造者とは独立に検証してください。
入力: 差分, docs/00_registry/ids.yml, docs/00_registry/traceability.yml
やること:
1) py -3 -m tools.trace_check --strict --report reports/trace_R101.json を実行。
2) chain_complete=true / orphan_ids=[] / front-matter 7項目 / 野号ゼロ を確認。
3) R-101→F-042→I-201..I-256→D-043→L-014,L-015→E-001..E-008→TC-001..TC-008 の往復 trace を検証。
4) R60Common.ts / BaseCamelModel.model_config 改変がないこと、mask_demo 通過を確認。
制約: 自力で修正せず、不合格は製造側へ差し戻す。
```

---

## 7. RACI 表（8 工程 × 人機分担）

### 7.1 PPT 原文（落地篇 S17 人機分工マトリクス）— 忠実転記

凡例（PPT 原文）: `◎`主担当　`○`支援・レビュー　`△`合意・承認　`－`関与小

| # | 工程 | AI | SE（上流） | PG（製造） | テスター | 日方顧客 |
|---|------|:---:|:---:|:---:|:---:|:---:|
| 1 | 要件理解 | ◎ | ◎ | ○ | － | △ |
| 2 | 基本設計 | ◎ | ◎ | ○ | － | △ |
| 3 | 詳細設計 | ◎ | ○ | ◎ | － | － |
| 4 | 框架・環境構築 | ○ | △ | ◎ | － | － |
| 5 | 製造（コーディング） | ◎ | ○ | ◎ | － | － |
| 6 | 単体テスト | ◎ | － | ◎ | ○ | － |
| 7 | 結合・総合テスト | ◎ | ○ | ○ | ◎ | △ |
| 8 | リリース・運用保守 | ○ | ◎ | ○ | ○ | △ |

> PPT 原文の結論: **「AI は実行主体、人は責任主体 — どの工程でも最終責任は人に残る」**。
> **日方顧客**は ①要件理解 ②基本設計 ⑦結合・総合テスト ⑧リリース・運用保守 の 4 工程で `△合意・承認` を持つ。

### 7.2 本骨架の展開版（骨格内部の 7 役割まで分解）

PPT の 5 列（AI / SE / PG / テスター / 日方顧客）を、本骨格の内部 7 役割まで分解したものが下表である。
**PPT 原文（7.1）が要件であり、本表はその展開**である。両者が食い違った場合は 7.1 を正とする。

- 人（担当者）= **A / I**（Accountable 説明責任 / Informed 情報共有）
- AI（Claude Code）= **R / C**（Responsible 実行責任 / Consulted 相談）

凡例：`A`=説明責任（人）／`I`=情報共有（人）／`R`=実行責任（AI）／`C`=相談（AI）／`—`=関与なし。

| # | 工程 | 上流SE(人) | 下流PG(人) | テスト設計(人) | AI推進(人) | 機密点検(人) | Review検査(人) | 日方顧客(人) | Claude Code(AI) |
|---|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | 要件理解 | A | I | I | C | I | I | △ | R |
| 2 | 基本設計 | A | C | C | C | I | I | △ | R |
| 3 | 詳細設計 | A | C | C | C | I | I | — | R |
| 4 | 框架構築 | A | C | I | C | I | I | — | R |
| 5 | 製造（コーディング） | I | A | I | C | C | I | — | R |
| 6 | 単体テスト | I | C | A | C | I | I | — | R |
| 7 | 結合・総合テスト | A | C | A | C | C | I | △ | R |
| 8 | リリース・運用保守 | A | C | I | I | C | A | △ | R |

> 各工程の AI(R/C) は Claude Code が Claude Code Skill「code-from-design-trans-cosmos-ai」の該当 Step および製造工程として一貫して実行する。人は各工程のレビュー・承認ゲート（要件合意・設計評審・合否判定・リリース判定）で拍板し、人側の A（説明責任）は常に 1 名に集約する。

> **★表に列を持たない役割がある（誤解しやすい点）**：#7 成果物還流 と #8 訓練対比 は、
> **8 工程のいずれか 1 つに属する役割ではなく、全工程に横断して走る役割**である
> （成果物還流は各節点の成果物に、訓練対比は各節点の直後に走る）。したがって本 RACI 表には**列を持たない**。
> これは「関与が無い」という意味ではない。無理に列を作ると、8 工程 × 役割の見かけを保つために
> **実態と合わない A（説明責任）を誰かに割り当てる**ことになるため、意図的に外している。

### 7.3 二つの記号系の対応

| PPT（7.1） | 本表（7.2） | 意味 |
|-----------|------------|------|
| `◎` 主担当（AI 列） | `R` | 実行を担う（本骨格では Claude Code） |
| `◎` 主担当（人 列） | `A` | その工程の説明責任を負う人 |
| `○` 支援・レビュー | `C` | 相談を受ける／レビューする |
| `△` 合意・承認 | `△`（日方顧客列のみ） | 社外の合意。内部の `A` とは別主体なので記号を分けている |
| `－` 関与小 | `I` または `—` | 情報共有のみ／関与なし |

> **7.2 が 7.1 に無い列（AI推進・機密点検・Review 独立検査・成果物還流）を持つ理由**：
> PPT は 5 列（AI / SE / PG / テスター / 日方顧客）で描くが、本骨格は内部統制の役割を分離したため列が増えている。
> **工程ごとの主担当（◎）と日方顧客の合意（△）は 7.1 と一致させること**が要件であり、
> 残りの支援列は本骨格の運用上の追加である。

---

## 8. 訓練対比担当（対比・帰因 / 8 工程の外側を横断）

- **責務**：節点が 1 つ終わるたびに、AI の産出物と**人間が書いた版**を突き合わせ、差分を**帰因分類**に振り分けて訓練報告へ追記する。**合否は判定しない**（紅线③。判定は人）。
- **成果物**：`reports/drill/<module>/comparison.md`（節点ごとに 1 節。**追記のみ**で既存節を書き換えない）。
- **红线**：帰因を省略して「AI が劣る／優る」と結論しない（根拠は `docs/90_knowledge/legacy-r60/09-ai-workflow.md` §7.1 の逐語）。**人版の内容を AI 側の成果物へ還流させない**（答案の漏洩であり測定を壊す）。
- **位置づけ**：これは**案件の納品物ではない**。このフレーム自体が使えるかを測るための**訓練の測定器**である。したがって顧客には出さない。

### 启动 Prompt 模板

```
あなたは訓練対比担当（.claude/agents/drill-comparator.md）です。
対象: tutorial/R60Login（試点 #0）／節点 N
1) reports/drill/R60Login/freeze.yaml と provenance.yaml を読み、
   要求書の sha256 を再計算して book_sha256 と一致するか確認する。
2) seal grep を実行し、下流成果物が実在資産を引用していないか走査する（空であること自体が証拠）。
3) 対象節点の AI 産出物と人版（画面カード docs/90_knowledge/legacy-r60/screens/<module>.md の
   file:line を索引に使う）を、項目ごとに突き合わせる。
4) 差分を R／A1／A2／A3／G1／G2／D／H に帰因分類し、根拠（file:line かコマンド）を添える。
5) reports/drill/<module>/comparison.md に「節点 N」の 1 節を追記する（既存節は書き換えない）。
制約: 合否を書かない。実値を書かない（reports/** は gate6 の走査対象）。試点 #0 の汚染を明記する。
```

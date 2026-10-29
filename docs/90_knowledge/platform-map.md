---
id: PLATFORM-MAP
type: knowledge
req_ids: []
status: draft
sensitivity: internal
owner: AI-SE
version: 0.2.0
---

# 7 層プラットフォーム対応マップ（trans-cosmos-ai AI 全流程骨架）

本ドキュメントは《AI実践に基づくソフトウェア開発プロセスの再考_落地篇.pptx》PART04 プラットフォーム篇の 7 層アーキテクチャ（PPT 第 S26 页）を、本リポジトリ（trans-cosmos-ai AI 全流程開発骨架）の実在資産へ 1 対 1 で対応付けたものである。各層は「已有（導入前から存在）」「本次新建（本骨架で新規作成）」「Phase 2+ 予定（後続段階）」の 3 列で整理する。対応付けの原則は PPT 第 S26 页「全 Agent が共通コンテキスト（要件 ID）とナレッジを参照し、工程間の情報断絶をなくす」である。

> 凡例：`已有` = 本骨架導入前から存在する資産。`本次新建` = 本骨架（Phase 1）で新規に作成した資産。`Phase 2+ 予定` = PPT 第 S30 页 3 段階計画の Phase 2/3 で整備する資産。
> 出典：7 層の名称・役割定義は PPT 第 S26 页、主要コンポーネント 6 要素は PPT 第 S27 页、技術選型は PPT 第 S28 页による。

---

## 0. 4 層知識モデル（統合実施規格書 §11.3）× 実在資産

統合実施規格書（`AI全链路软件工程平台_实施规格书.md` ルート）§11.3 の **4 層知識モデル**は、
7 層アーキテクチャとは**別の切り口**（技術視点ではなく「AI に何を読ませるか」の視点）である。
両方を持つ理由は §11.1.1 のとおり——業務層に説明するときは 4 層、技術層に設計を説明するときは 7 層。

| 層 | 規格書の定義（§11.3.1） | 本リポジトリの実在資産 | 成熟度 |
|---|---|---|---|
| ① 入口層（Entry） | AI が最初に読む「プロジェクトの地図」 | `CLAUDE.md`（唯一の常時ロード制約）／`使用手册.md`＋`.zh.html`（新人の唯一の門＝巻頭「三分钟版」、全機能は同書の後半）／`AGENTS.md`（人向け役割定義。Claude Code は自動ロードしない） | 充足 |
| ② 規則層（Rules） | ベストプラクティス・禁止パターン・用語集・教訓 | `.claude/rules/` 7 份（`00` 総則／`01` 機密／`02` 要求管理／`03` 設計製造／`04` テスト／`05` commit／`06` 知識飛輪）＋ `docs/90_knowledge/`（`answer-engine.md`＝出典等級 E1〜E4 の唯一真源、`ai-dev-playbook.md` 等） | 充足 |
| ③ 実行層（Execution） | プロンプトテンプレート・AI スキル | `.claude/skills/` 5 個、`.claude/agents/` 14 個（工程実行系 9＝8 工程＋旁路環／検証・補助系 5）、`tutorial/R60Login/节点*/` の作業票 | 充足 |
| ④ 検証層（Verification） | 品質ゲート・自動チェック | `tools/trace_check/`（6 gate ＋ seal ＋ freeze）／`tools/masking/mask_demo.py --self-test`／`tools/gen_view --self-test`／`.github/workflows/ai-gate.yml`（占位） | 充足 |


> **成熟度の判定**（規格書 §11.3.3 の L0〜L4）：本リポジトリは **L3**（検証層まで到達）。
> **L4（進化メカニズムが自動で回る）ではない** —— 規則 06 の飛輪は「記録 → 規則化 → 検査追加」を
> **手動で回す**運用であり、anomaly の自動創建・検査の自動追加提案は未実装である（規則 06 §6 が同じことを書いている）。

---

## 1. 利用層（接点）

接点層。開発者が AI 能力へアクセスする窓口。出典：PPT 第 S26 页「利用層（接点）：IDE プラグイン（VS Code）・チャット・Web 画面・CLI・CI/CD 連携」。

| 已有 | 本次新建 | Phase 2+ 予定 |
|---|---|---|
| Claude Code（IDE 統合＋CLI 実行環境） | `CLAUDE.md`＋`AGENTS.md`（Claude Code 単一ツールの真源・役割紅線）<br>`.claude/rules/` 7 份（project-global / security-redlines / requirements / design-coding / testing / commit-messages / knowledge-flywheel） | VS Code プラグイン拡張<br>Web 統合画面（ブラウザ接点）|

- 参照：PPT 第 S26 页（利用層＝接点）、PPT 第 S6 页（SE/PG/テスター/AI 推進の役割再構築）。各資産は Claude Code 単一ツール（8 工程実行）と人的レビュー・承認ゲートの唯一入口として機能する。

## 2. 編成層

工程の編成・オーケストレーション。出典：PPT 第 S26 页「編成層：工程別 Agent（要件・設計・製造・テスト）・ワークフロー・プロンプト/テンプレート管理」、PPT 第 S27 页「工程別 Agent」。

| 已有 | 本次新建 | Phase 2+ 予定 |
|---|---|---|
| 手作業の工程受け渡し（メール・口頭・レビューでの都度すり合わせ） | **工程の編成体**：`.claude/skills/trans-cosmos-ai-lifecycle-coach/`（8 工程の伴走進行役。`nodes/n01..n09` の作業票＋`references/node-worker-contract.md`）<br>**工程別 Agent 9 体**：`trans-cosmos-ai-node1-requirements` … `node8-release-ops` ＋旁路環 `node9-change`<br>**検証・補助 Agent 5 体**：`spec-reviewer`／`secret-auditor`／`deliverable-reviewer`／`drill-comparator`／`legacy-module-surveyor`<br>`.claude/skills/code-from-design-trans-cosmos-ai/SKILL.md`（4 件套 Skill：R-ID 受理→BD/DD 双向生成→製造→trace_check 検証）<br>`CONTRIBUTING.md`（`req/R-xxx` 集成分支＋`R-xxx/01-req`〜`07-release` 8 工程子分支の編成） | 内網 GitLab runner を `ai-gate.yml` へ接続<br>プロンプト・テンプレートの独立ライブラリ化（規格書 §11.4） |

- 参照：PPT 第 S26 页（編成層）、PPT 第 S27 页（工程別 Agent「各 Agent が専用ツール（DB・Git・Excel・テスト実行）を呼出」）。

## 3. 能力層

AI と自動化の実行能力。出典：PPT 第 S26 页「能力層：モデルゲートウェイ・コード生成・ドキュメント生成・テスト生成・RAG 検索・静的解析」、PPT 第 S27 页「モデルゲートウェイ」「評価・ガバナンス」。

| 已有 | 本次新建 | Phase 2+ 予定 |
|---|---|---|
| 手動でのコード生成・設計書作成・レビュー | `tools/trace_check/`（6 重門番：ID 合法／追溯双方向／front-matter 7 字段／生成物一致／snake-camel 命名分区／機密ゼロヒット）<br>`tools/gen_formal/`（機読源→日文正式 Excel。`gen_excel` は dry-run、`book` は参考書体裁の .xlsx を `reports/` 配下へ生成）<br>`tools/gen_view/`（機読源→中文ビュー `.zh.html`）<br>`tools/masking/`（双方向脱敏スクリプト `mask_demo.py`＋辞書例） | 顧客テンプレート接続（Phase2）<br>RAG 検索・ベクトル検索基盤の実装 |

- 参照：PPT 第 S27 页（主要コンポーネント 6 要素、「品質評価セットで出力を採点、採用率・修正率・指摘密度を計測」）、PPT 第 S20 页（成型 6 原則＝能力層の生成品質規約）。

## 4. 知識層

再利用可能な知識資産。出典：PPT 第 S26 页「知識層：過去案件成果物・コーディング規約・用語辞書・既存ソース・設計パターン」、PPT 第 S27 页「ナレッジベース（RAG）」。

| 已有 | 本次新建 | Phase 2+ 予定 |
|---|---|---|
| `project_memory.md` §18-§26（241 行・26 章の方法論。**原文の行数・章数は失効**——現物 11 行。`docs/00_plan/spec.md:34` を参照）<br>`doc/02_INPUT/`（日方規約／DB 定義／画面規約／旧 Java ソース／DDL）<br>`doc/03_AI/AB_Reports/`（A/B 比較レポート群） | `docs/90_knowledge/review_diff_assets/`（R60Area/R60Code/R60Item の review_before / review_after / review_comments 審査差分資産）<br>`docs/00_registry/glossary.yml`（中日英三語の用語集・30 用語以上）<br>`tools/kb-platform/repo/projects/P-R60-001/`（**migration 案件の読取専用ナレッジ**：画面卡・chunks・DB/API/規約・偏差記録。`legacy-r60-navigator` skill と `tools/legacy` が入口）<br>`docs/90_knowledge/answer-engine.md`（**出典等級 E1〜E4 の唯一真源**。確認票の根拠の格付け）<br>`docs/90_knowledge/ai-dev-playbook.md` / `onboarding-checklist.md` / `platform-map.md`（方法論・新人 Walkthrough・本マップ） | RAG 検索の精度向上（索引は `build/rag/`・語料から再生成可）<br>32 モジュール全量の資産インベントリ |

- 参照：PPT 第 S27 页（ナレッジベース「過去案件・用語辞書・設計規約・既存ソースを検索、流用資産を提示」）、PPT 第 S19 页（全鏈路成果物マップ）。

## 5. データ・コンテキスト層

成果物と ID コンテキストの保持。出典：PPT 第 S26 页「データ・コンテキスト層：成果物リポジトリ（Git）・要件 ID 管理・トレーサビリティ DB・ベクトル DB」、PPT 第 S27 页「コンテキストハブ」。

| 已有 | 本次新建 | Phase 2+ 予定 |
|---|---|---|
| R60 既存 Git リポジトリ（`src/`／`api/fastapi_oracle_pjt/app/routers/`／`Front-end/src`）<br>`doc/` 既存設計ドキュメント（200+ 件） | `docs/00_registry/ids.yml`（R/Q/F/I/D/L/E/TC/CR/BUG の発号統合レジストリ・唯一発号口）<br>`docs/00_registry/traceability.yml`（R→F→I→D→L→E→TC の forward/back 双方向リンク）<br>8 工程テンプレート（`docs/10_requirements/req-template.yaml` 〜 `docs/80_operation/operation-runbook.md`、機読源の雛形） | トレーサビリティ DB 化（全文検索・ベクトル DB）<br>コンテキストハブの自動供給 |

- 参照：PPT 第 S26 页（データ・コンテキスト層）、PPT 第 S16 页（工程間連携 7 メカニズム＝コンテキストハブ／トレーサビリティ・マトリクス）、PPT 第 S24 页（成果物の二重化＝機読源は Git 版管理）。

## 6. 統制・ガバナンス層

品質・機密・権限の統制。出典：PPT 第 S26 页「統制・ガバナンス層：権限・認可・監査ログ・機密マスキング・品質評価・コスト管理」、PPT 第 S27 页「セキュリティ」。

| 已有 | 本次新建 | Phase 2+ 予定 |
|---|---|---|
| 散在する機密情報（`.env` 内の接続情報等）・属人的なレビュー | `CODEOWNERS`（`.claude/rules/`／`.claude/skills/`／`docs/10_requirements`／`docs/20-30_design`／`tools/`／`docs/90_knowledge`／`.github/` の 11 ブロック）<br>`.claude/rules/01-security-redlines.md`（公開可／要脱敏／禁止外投の 3 級機密清单・13 敏感点）<br>`tools/trace_check/` gate6（機密ゼロヒット・スキャン＝gitleaks 等価） | gitleaks 実 CLI への置換<br>監査ログ基盤・SSO・データ分類ポリシーの本格運用 |

- 参照：PPT 第 S27 页（セキュリティ「データ分類・マスキング・閉域網・権限分離でコードとデータの漏洩リスクを統制」）、PPT 第 S28 页（ガバナンス「監査可能性と権限分離を最優先」）。

## 7. 基盤層

インフラと実行基盤。出典：PPT 第 S26 页「基盤層：クラウド/オンプレ・GPU・閉域網・認証基盤」、PPT 第 S28 页「技術選型」。

| 已有 | 本次新建 | Phase 2+ 予定 |
|---|---|---|
| Oracle DB 基盤（NLS_DATE_FORMAT 固定）<br>認証基盤（閉域網内の認証サービス）<br>オブジェクトストレージ基盤 | 標準ディレクトリ骨格 `docs/10_requirements`〜`docs/90_knowledge`（8 工程＋レジストリ＋ナレッジの器）<br>`.gitignore` AI 骨格可选忽略ブロック（`AI_FULL_LIFECYCLE=1` 指定時のみ納入・生産コード非侵襲 NFR-5） | クラウド/オンプレ・GPU・閉域網の本格構成<br>CI runner 基盤の常設化 |

- 参照：PPT 第 S26 页（基盤層）、PPT 第 S28 页（技術選型「機密データの扱いを決める → 成果物の形式を決める → モデルと工具を決める」、選定順序）。機密情報の実値は本マップに記載せず、すべてプレースホルダで表現する。

---

## 8. 統合実施規格書との差分（未実装・未充足 — 正直な線引き）

統合実施規格書の各節のうち、**本リポジトリにまだ無いもの**を先に書く。ここを空にしないことが、
「できている」と「できるはず」を混同しないための唯一の方法である。

| 規格書の節 | 項目 | 本リポジトリの現状 | 受け皿（誰が／いつ） |
|---|---|---|---|
| §13.1 | **KPI 六大维度**（生産性・品質・AI 活用度・網羅性・リードタイム・知識資産）の数値計測 | **未実装**。指標を採る仕組みが無い。定性材料（`reports/drill/*/comparison.md`・`reports/AC-selfcheck.md`）のみ | Phase 2。まず製造・テスト工程で測る（§13.1 の指示どおり） |
| §11.4 | **Prompt 模板库**の独立した置き場 | **独立していない**。プロンプトは `.claude/skills/**/references/` と各作業票に分散 | Phase 2。分割するかは、分散で困ってから決める（規則 00 §12 と同じ判断） |
| §12.2 | **モデルゲートウェイ**（モデル路由・安全フィルタ・コスト管理） | **未実装**。モデル選択は Claude Code 任せ | Phase 2+。閉域・機密の要件が固まってから |
| §10.2.1 | **差分検証パターン**（設計vs実装、新旧比較、要件vsテスト） | **部分的**。`drill-comparator` agent と `docs/90_knowledge/review_diff_assets/` が「審査前後の差分」を扱う。設計vs実装の自動差分は未実装 | Phase 2 |
| §9.3 | **成果物の二重化**（機読源 → 日文正式 Excel／Word） | **部分的**。`tools/gen_formal/book.py` が md → `.xlsx` を `reports/` 配下に生成できる。**顧客テンプレートへの接続と受控回流は Phase 2** | Phase 2（`tools/gen_formal/README.txt`） |
| §16 | **実績データ**（Harmony 70%／JET 25% 等） | 本骨架自身の実績は**無い**。引用できるのは社内実績 PPT の値のみ | 実案件適用後に測る |

> **7 層との関係**：§11.1.1 のとおり 4 層（機能視点）と 7 層（技術視点）は同じプラットフォームの異粒度表現である。
> 本マップは 7 層を主とし、§0 で 4 層への写像を持つ。**両方に同じ内容を書かない**（NFR-1）。

---

## 集計（AC-7 第①子条件の検証用）

| 層 | 本次新建 条目数 | 主な PPT 引用 |
|---|---|---|
| 利用層 | 2 | S26 / S6 |
| 編成層 | 5 | S26 / S27 |
| 能力層 | 3 | S26 / S27 |
| 知識層 | 6 | S26 / S27 / S19 |
| データ・コンテキスト層 | 3 | S26 / S27 / S16 |
| 統制・ガバナンス層 | 3 | S26 / S27 / S28 |
| 基盤層 | 2 | S26 / S28 |
| **合計** | **24（>= 14）** | 各層 >= 2 を充足 |

## 関連ドキュメント
- **`docs/90_knowledge/repo-inventory.md`（リポジトリ棚卸し — 全内容と階層の説明）**
  本書は「層」の視点で資産を並べる。**「どこに何があり、誰が作り、捨ててよいか」**は
  あちらが 1 枚で示す（件数・容量の実測つき）。両方に同じ表を書かない。
- **`AI全链路软件工程平台_实施规格书.md`（ルート。統合実施規格書 — 4 層・7 層・8 工程の語彙の正）**
  本書 §0 は同規格書 §11.3 の 4 層モデルを、§1〜§7 は同じく §11.1 の 7 層を扱う。
- **`docs/90_knowledge/v1-platform-4layer.md`（方案 v1 の四層との対応表 — 必読）**
  本書は落地篇の **7 層**を扱う。v1 の **4 層**（接入／能力編排／知識庫／模型網関）との対応関係は
  あちら §3 で定義している。**両者は同じプラットフォームの異粒度表現**であり、対応表を二重に書かないこと（NFR-1）。
- **`docs/90_knowledge/ppt-deviation-register.md`（PPT に無い追加要素・PPT との差異の登録簿）**
  本書の 7 層のうち、PPT に無い追加要素（`gen_view`・6 重門番・サブエージェント（検証系 A-5／工程実行系 A-12）・`tutorial/` 等）は
  あちら §2 が唯一の登録簿である。**「7 層すべてが PPT 由来」ではない**ことを忘れないこと。
- `ROADMAP_3PHASE.md`（PPT 第 S30 页 3 段階計画・Phase 2/3 の具体化）
- `docs/90_knowledge/onboarding-checklist.md`（NFR-4 新人 2 時間 Walkthrough）
- `.claude/rules/01-security-redlines.md`（統制・ガバナンス層の機密 3 級清单）
- `tools/trace_check/`（能力層・統制層の 6 重門番）

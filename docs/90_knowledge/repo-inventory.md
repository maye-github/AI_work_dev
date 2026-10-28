---
id: REPO-INVENTORY
type: knowledge
req_ids: []
status: draft
sensitivity: internal
owner: AI-SE
version: 0.1.0
---

# リポジトリ棚卸し — 全内容と階層の説明

> **この文書の役割**：`D:\AI_work_dev` 配下に**何があり、誰が作り、誰が読み、捨ててよいか**を 1 枚で示す。
> **唯一真源ではない。** 各領域の真源はそれぞれ別にある（§3 の表の「真源」列を参照）。
> 本書は **2026-10-26 時点の実測**に基づく。件数・容量は測り直せば変わる。
> **2026-10-28 に再測した項目**：入口文書の本数・容量（§1・§2・§3）、`ids.yml` の件数（§1・§5）、
> `*.zh.html` の本数（§11）、`tasks.md` のタスク数（§12 #8）。他は 10-26 の値のままである。

---

## 1. 一枚図

```
D:\AI_work_dev
│
├─【入口】人が読む文書（7 ファイル）
│   CLAUDE.md／使用手册.md＋.zh.html／AGENTS.md／
│   AI全链路软件工程平台_实施规格书.md／ROADMAP_3PHASE.md／CONTRIBUTING.md／CODEOWNERS
│
├─【設定】AI が読む（.claude/ 568KB）
│   ├─ rules/    7 本 … 起動時に自動ロードされる工程規約
│   ├─ skills/   5 個 … 手順書（description で自動起動）
│   ├─ agents/   14 体 … 工程実行体 9（n01〜n08＋n09）＋検証・補助 5
│   └─ settings.json … deny 5 件＋フック 2 本
│
├─【成果物の器】docs/ 2.2MB
│   ├─ 00_plan/      … 工程管理（spec/tasks/review）＋ coach/R60Login/ の状態 11 ファイル
│   ├─ 00_registry/  … ID 台帳（ids.yml 164 件）・traceability・glossary 50 語
│   ├─ 01_context/   … 案件プロファイル（スタックの事実）
│   ├─ 10〜80_*/     … 工程ごとの器。**テンプレ 8 本＋見本 R-101 系 13 本**
│   └─ 90_knowledge/ … 知識・対応表・旧案件ナレッジ（1.4MB）
│
├─【演習】tutorial/R60Login/ 4.6MB
│   8 節点 ×（入力模板 → AI 産出 → 承認版）＋ README（685 行）
│   ※ コードが在るのは節点5 だけ。他は文書。
│
├─【道具】tools/ 1.0MB … 8 パッケージ（trace_check／gen_view／gen_formal／masking／
│                        registry／impact／coach_brief／rag・ingest・legacy）
│
├─【記録】reports/ 4.9MB … 訓練記録・自動生成 Excel・一度きりの調査出力
├─【判定材料】eval/ 32KB（RAG 評価セット）／build/ 1.2MB（RAG 索引・再生成可）
└─【統制】.github/workflows/ai-gate.yml／.vscode/extensions.json／.gitignore
```

---

## 2. 件数と容量（実測）

| 領域 | 主なファイル数 | 容量 | 性質 | 捨てられるか |
|---|---|---|---|---|
| ルート文書 | 7 | 186KB | 人が読む説明・統制 | ✗ |
| `.claude/rules` | 7 | 124KB | 規約（真源） | ✗ |
| `.claude/skills` | 18 | 360KB | 手順書（真源） | ✗ |
| `.claude/agents` | 14 | 80KB | 実行体・検証体 | ✗ |
| `docs/00_plan` | 16 | 292KB | 計画＋進行状態 | ✗ |
| `docs/00_registry` | 4 | 60KB | ID 台帳（**単一発号口**） | ✗ |
| `docs/01_context` | 3 | 16KB | 案件プロファイル | ✗ |
| `docs/10〜80_*` | 17 | 84KB | テンプレ＋見本 | ✗ |
| `docs/90_knowledge` | 92 | 1.8MB | 知識 | ✗（一部は整理余地） |
| `tutorial/R60Login` | 88 | 4.6MB | 演習の全記録 | ✗ |
| `tools/` | 41 | 1.0MB | 道具（真源） | ✗ |
| `reports/drill` | 14 | 333KB | 訓練の測定記録 | ✗ |
| `reports/_auto` | 2 | 236KB | 自動生成 Excel | ○（次回生成で作り直される） |
| `reports/module-survey` | 234 | 3.4MB | **一度きりの**モジュール普查 | △（結論は `module-selection.md` に保存済み） |
| `reports/legacy-raw` | 29 | 376KB | 旧設計書からの生テキスト抽出 | △（`tools/legacy` で再抽出可） |
| `reports/ingest` | 7 | 374KB | `tools/ingest` の試走結果 | △ |
| `reports/` 直下 | 11 | 68KB | 過去の門番出力・Phase 記録 | △（`docs/00_plan/*.md` が証拠として引用） |
| `eval/` `build/` | 4 | 1.2MB | RAG 評価セット／索引 | ○（索引は語料から再生成） |

---

## 3. 入口 —— 人が読む 7 ファイル

| ファイル | 容量 | 誰が読む | 自動ロード | 中身 | 他との重複 |
|---|---|---|---|---|---|
| `CLAUDE.md` | 12KB | AI（毎回） | **○** | 7 条紅线・禁止 5 条・commit 様式・設定一覧 | 役割表が `AGENTS.md` と重複 |
| `使用手册.md`＋`.zh.html` | 59KB | 全員 | ✗ | **巻頭「三分钟版」＝新人の唯一の門**。以後 6 規則・フロー・トラブル | 入口 3 本の内容を含む最上位版 |
| `AGENTS.md` | 18KB | 人（役割定義） | ✗（CLAUDE があるため） | 14 役割とその起動プロンプト | `CLAUDE.md §0` と重複 |
| `AI全链路软件工程平台_实施规格书.md` | 76KB | 企画・管理 | ✗ | **上流 2 本の PPT の統合稿**。4 層知識モデル・7 層平台・8 工程 | なし（最上位の語彙の正） |
| `ROADMAP_3PHASE.md` | 12KB | 管理 | ✗ | Phase 1/2/3 の計画 | 規格書 §14 と同じ内容 |
| `CONTRIBUTING.md` | 6KB | 開発 | ✗ | ブランチ規約・Tag 規約 | — |
| `CODEOWNERS` | 2KB | Git | ✗ | 11 ブロックの承認者 | — |

> **重複の実測**：`CLAUDE.md §0` と `AGENTS.md §0` の資産一覧は同源である（§12 #1）。
> かつて `START_HERE.md`（12KB）が `使用手册.md` の「8 節点表・会話の復帰・変更環・ディレクトリ案内」と
> 長短 2 版になっていたが、**2026-10-28 に `使用手册.md` 巻頭「三分钟版」へ統合し、`START_HERE.md` は削除した**。

---

## 4. AI の設定 —— `.claude/`

### 4.1 `rules/`（7 本・起動時自動ロード）

| # | ファイル | 何を縛るか |
|---|---|---|
| 00 | `00-project-global.md` | 工程横断 13 条（暗号化は案件ごと・NLS・ROWID・野号禁止・commit 様式・機密・媒体規約…） |
| 01 | `01-security-redlines.md` | 機密 L3 の 13 項目と脱敏占位（**gate6 の走査対象から唯一除外されるファイル**） |
| 02 | `02-requirements.md` | R/Q 発号 SOP・A/B/C 分類・回答の受領と突合・状態機・上流欄位の移送検査 |
| 03 | `03-design-coding.md` | `BaseCamelModel` 4 行・snake/camel 分区・SQL 白名单 |
| 04 | `04-testing.md` | TC 正常3/境界2/異常3・`design_ids`・双方向閉ループ・A/B の記録先 |
| 05 | `05-commit-messages.md` | commit 7 種・Trace/AI/Review 三段・Tag 命名 |
| 06 | `06-knowledge-flywheel.md` | 踩坑→規則化→検査追加→全隊免疫の 5 段と、**紅线を増やさない**原則 |

### 4.2 `skills/`（5 個）

| skill | 中身 | いつ使うか |
|---|---|---|
| `trans-cosmos-ai-lifecycle-coach` | `SKILL.md`＋`nodes/n01〜n09`（**各節点の作業票**）＋`references/node-worker-contract.md`＋`templates/`（雛形） | 8 工程の進行役。引数なし起動で現在地を自動復帰 |
| `code-from-design-trans-cosmos-ai` | 設計→製造の 4 段パイプライン | `migration` 案件の製造 |
| `requirement-interrogator` | **51 の審査観点**（実在案件 QA 票 177 件から抽出） | 節点1 の要求書審査（真案件の本命） |
| `virtual-requirement-author` | 実在資産から節点1 の入力を倒推 | 節点0（8 工程の外側） |
| `legacy-r60-navigator` | 旧 R60 資産の**読取専用**ナビゲータ | `migration` 案件の調査 |

### 4.3 `agents/`（14 体）

| 種別 | 体数 | 名前 |
|---|---|---|
| 工程実行系 | 9 | `trans-cosmos-ai-node1-requirements` … `node8-release-ops` ＋旁路環 `node9-change` |
| 検証・補助系 | 5 | `spec-reviewer`／`secret-auditor`／`deliverable-reviewer`／`drill-comparator`／`legacy-module-surveyor` |

> **テスト設計の専用 agent は無い**（2026-10-26 に `test-designer` を廃止し、工程 06 の実行体へ統合）。

### 4.4 `settings.json`

- `permissions.deny` 5 件（機密ファイル・`.env`・鍵）
- フック 2 本：**SessionStart**（`tools/coach_brief.py --hook` で現在地を文脈へ差し込む）／
  **Stop**（`tools/gen_formal/auto.py` で基本設計書の Excel プレビューを描き直す）

---

## 5. 成果物の器 —— `docs/`

| ディレクトリ | 中身 | 真源か |
|---|---|---|
| `00_plan/` | `spec.md`／`tasks.md`／`review.md`（受入基準 CP 12 本）／`phase0-closure.md` | 工程管理の真源 |
| `00_plan/coach/R60Login/` | `case.yml`＋`n01〜n09.yml`＋`handoff.md`（**1 ノード 1 ファイル**） | 進行状態の真源（機械生成物） |
| `00_registry/` | `ids.yml`（**164 件**：R2/Q0/F2/I77/D6/L10/E18/TC29/IT13/CR5/BUG2）／`traceability.yml`（roots=R-101,R-201）／`glossary.yml`（50 語）／`ingest-manifest.yml` | **ID 発号の唯一口**（紅线①） |
| `01_context/` | `case-profile-R60.yaml`（migration のスタック）／`case-profile-sample-greenfield.yaml`／`R-101-R60Area.md` | スタックの事実 |
| `10〜80_*/` | **テンプレ 8 本**（`*-template`）＋**見本 13 本**（R-101/F-042/I/D-043/L-014/L-015/E-001..005/TC-001..008/IT-001） | 器の雛形と記入例 |
| `90_knowledge/` | 手法・対応表・旧案件ナレッジ・審査差分資産（§6） | 知識（一部は派生） |

> **混同しやすい点**：`docs/10_requirements/R-101-R60Area.yaml` の **R-101 は演習ではない**。
> 骨架を作るときに **R60Area（実在案件）を見本として書き下したもの**である。
> 演習は **R-201（R60Login）** で、`tutorial/R60Login/` 側にある。両方 `ids.yml` に登録済み。

---

## 6. 知識 —— `docs/90_knowledge/`

| ファイル／ディレクトリ | 中身 |
|---|---|
| `platform-map.md` | **7 層平台 × 実在資産**の対応表＋4 層知識モデル＋未実装の差分（§8） |
| `ppt-deviation-register.md` | **PPT に無い追加要素の唯一の登録簿**（A-1〜A-31） |
| `v1-platform-4layer.md` | 方案 v1 の 4 層との対応（platform-map と役割分担） |
| `answer-engine.md` | **出典等級 E1〜E4 の唯一真源**（確認票の根拠の格付け） |
| `ai-dev-playbook.md`／`onboarding-checklist.md` | 方法論 7 原則／新人 2 時間 Walkthrough |
| `dual-deliverable.md` | 機読源と対外 Excel の二重化の設計 |
| `reference-design-book.md` | 参考設計書（`50.設計書`）の体裁メモ |
| `requirement-review-capability.md` | 要求書審査 capability の設計 |
| `ppt-coverage-assessment.md` | PPT の各頁をどこまで実装したか |
| `claude-code-migration-guide.md` | Trae → Claude Code の移行記録 |
| `agent-run-record.md` | 8 工程を走破した記録の索引 |
| `internal/`（2） | Harmony 5 道ゲート／SDS2・SDS3 の教訓 |
| `legacy-r60/`（65 ファイル・1.4MB） | **migration 用の読取専用ナレッジ**：手引き 10 本＋画面卡 8＋chunks 7＋モジュール別 YAML 37＋RAG 手順 |
| `review_diff_assets/`（11 ファイル・336KB） | 審査前後のスナップショット対（R60Area/R60Code/R60Item）＋SOP＋RC-SK 記録 |

---

## 7. 演習 —— `tutorial/R60Login/`

```
tutorial/R60Login/
├── README.md（685 行）＋ README.zh.html   ← 手順書（スキルの印刷用ビュー）
├── 节点1_需求/      16 files 1.8MB  ← 要求書入力〜承認版。PDF 2 本（AB 類・C 類）を含む
├── 节点2_基本设计/  14 files 708KB  ← 図なし。_archive 2 つ（教学样例・导航合并）
├── 节点3_详细设计/  11 files 856KB
├── 节点4_框架构筑/   5 files 312KB
├── 节点5_制造/       5 files＋code 232KB  ← **唯一コードを持つ節点**（backend 9／frontend 5）
├── 节点6_单元测试/   5 files 200KB  ← TC 20 件
├── 节点7_结合测试/   7 files 300KB  ← IT 11 件＋verification.md（A/B をしない案件の記録先）
└── 节点8_发布运维/   5 files 224KB
```

**各節点のファイル番号（実測・節点ごとに不揃い）**

| 節点 | 00 | 01 | 02 | 03 | 04 | 05 | 06 | その他 |
|---|---|---|---|---|---|---|---|---|
| 1 | 入力要求書 | AI 産出（md＋yaml） | **回答受領チェック**＋**確認事項一覧**（02 が 2 本） | 確認依頼書 AB＋技術者課題 C（各 md＋pdf） | 承認版 | — | — | — |
| 2 | 入力模板 | **入力_已填写**＋**AI 産出**（01 が 2 本） | **你在这里审查**＋**审查结果**（02 が 2 本） | 組内審査意見 | AI 改修版 | 承認版 | — | — |
| 3 | 入力模板 | AI 産出 | 你在这里审查＋审查结果 | **無し** | AI 改修版 | 承認版 | — | — |
| 4 | 入力模板 | AI 産出 | — | — | — | 承認版 | — | — |
| 5 | 入力模板 | — | — | — | — | 承認版 | 設計との差異 | `backend/` `frontend/` |
| 6 | 入力模板 | AI 産出 | — | — | — | 承認版 | — | — |
| 7 | 入力模板 | AI 産出 | — | — | — | 承認版 | — | `verification.md` |
| 8 | 入力模板 | AI 産出 | — | — | — | 承認版 | — | — |

---

## 8. 道具 —— `tools/`

| パッケージ／ファイル | 役割 | 呼び出され方 |
|---|---|---|
| `trace_check/`＋`trace_check.py` | **門番 6 道**（ID 合法／追溯双方向／front-matter 7 字段／生成物一致／命名分区／機密）＋seal＋freeze | 人が毎回・CI 占位 |
| `gen_view/` | 機読源 → 人向け HTML（**日文 chrome／中文 chrome** を出し分け） | 各節点の後 |
| `gen_formal/` | 機読源 → 日文正式 Excel（`book` は参考書体裁）＋`auto.py` は Stop フック | 自動 |
| `masking/` | 双方向の脱敏（`mask_demo.py`・辞書例） | 外部送信前 |
| `registry.py` | `ids.yml` への発号・阻塞・失効（`mark-stale`） | 人（発号は人の行為） |
| `impact.py` | ID から下流/上流の影響面を逆引き | n09 環 |
| `metrics.py` | 実施規格書 §13 の 6 次元 KPI の基準値を測る（測れない次元は「測れない」と書く） | 手動（節目ごと） |
| `kb_export.py` | 知識 `.md` を社内知識基盤 `kb-platform` の形（8 字段 front matter）へ書き出す。片方向・再生成可 | 手動 |
| `kb-platform/` | 社内知識基盤の複製（ベンダリング）。`run.py` で lint／ingest／search／eval／stats。**上流は `D:\AI_platform\kb-platform`、本項は抄本**（`VENDORED.md`） | 手動 |
| `coach_brief.py` | 現在地の要約（SessionStart フック） | 自動 |
| `rag/`・`ingest/`・`legacy/` | RAG 索引／旧資産の取り込み／旧 Excel のテキスト化 | 手動 |
| `paths.py` | パス解決の共通部品 | 内部 |

---

## 9. 記録・出力 —— `reports/` と `eval/`・`build/`

| パス | 中身 | 位置づけ |
|---|---|---|
| `drill/R60Login/` | `README.md`（既知の坑 7 つ）／`comparison.md`（節点ごとの AI vs 人 の帰因）／`answer-key.md`／`interrogation.md`／`requirement-defects.md`／`provenance.yaml`／`freeze.yaml` | **訓練の測定記録**（真源） |
| `_auto/R60Login/` | 節点2・3 の承認版 Excel プレビュー（`_预览版`） | 自動生成（捨ててよい） |
| `module-survey/` | 13 モジュールの選型普查（234 ファイル） | 一度きり。結論は `legacy-r60/module-selection.md` |
| `legacy-raw/` | 旧設計書から抽出した生テキスト | 再抽出可 |
| `ingest/JET-R60/` | 旧案件取り込みの試走結果 | 試走 |
| `rag/` | RAG 評価結果 JSON | 評価記録 |
| `metrics/` | §13 KPI の基準値スナップショット（`.md` ＋ `.json`）。**手で編集しない**、`py -3 -m tools.metrics --out …` で再生成 | 時点記録 |
| `AC-selfcheck.md`／`DELIVERY_MEMO.md`／`PHASE15-EXIT.md` | Phase 1 の受入・引渡・出口記録 | 履歴（`review.md` が引用） |
| `trace_*.json`（5）／`gate6_report.json`／`seal_before.json`／`gen_formal_columns_R101.json` | 過去の門番の生出力 | `spec.md`/`tasks.md`/`review.md` が証拠として引用 |
| `eval/gold-qa.yaml` | RAG 評価用の設問セット | `tools/rag/evaluate.py` が読む |
| `build/rag/` | RAG 索引（`.sqlite` 2 本＋文脈束 1 本） | **再生成可**（`.gitignore` 済み） |

> **附贈層（骨組みの一部ではない）の目印**：`module-survey/` と `legacy-raw/` は
> **R60 専用の付随データ**であり、8 工程・6 道の門番・`trace_check` のどこからも参照されない。
> 各ディレクトリ直下の `README.md` に「中身・誰が使うか・**削ってよいか**・機密度」を書いてある。
> `docs/90_knowledge/legacy-r60/`（migration 専用の知識庫）も同じ附贈層に属する
> （入口 `legacy-r60/00-index.md` の冒頭に、`greenfield` では参照しない旨の断りがある）。

---

## 10. 統制

| ファイル | 役割 |
|---|---|
| `.gitignore` | `.claude/` はコミット、`docs/`・`tools/`・`reports/` は既定で除外、機密辞書は恒久除外 |
| `CODEOWNERS` | 11 ブロック。承認者は人（紅线③の機械可読な裏付け） |
| `.github/workflows/ai-gate.yml` | **占位**。実際の runner は無い（内網前提） |
| `.vscode/extensions.json` | 拡張の推奨だけ |

---

## 11. 二つの流れ（最も混同しやすい）

```
【演習】 tutorial/R60Login/节点N/  … 人が読む日本語 .md ＋ 中文 .zh.html
          ↓ 承認（nNN.yml の approved_by に人の識別子）
        次の節点へ。状態は docs/00_plan/coach/R60Login/nNN.yml

【実案件】 docs/10_requirements/ … docs/80_operation/ … 機読源（.yaml/.md）
          ↓ trace_check の 6 道
        ID は docs/00_registry/ids.yml からのみ発号
```

- **演習は教材**、**`docs/` は本番の器**。演習の成果物を `docs/` へ移す運用はしない（番号系が違う）。
- **生成物は触らない**：`*.zh.html`（42 本）／`reports/_auto/*.xlsx`／`build/rag/`。
  修正は必ず機読源へ入れ、再生成する（単一ソース原則）。

---

## 12. 現状の問題（棚卸しの結果）

| # | 問題 | 実測 | 影響 |
|---|---|---|---|
| 1 | ~~入口文書が 5 本で役割が重なる~~ **→ 4 本に減らした（2026-10-28）** | `CLAUDE.md`／`使用手册.md`／`AGENTS.md`／規格書＝166KB。`START_HERE.md` は `使用手册.md` 巻頭へ統合 | 残る重複は `CLAUDE.md §0` ↔ `AGENTS.md §0` の 1 組のみ |
| 2 | **`docs/` に中文ビューが 0** | `docs/**/*.md` 58 本に対し `.zh.html` 0 本 | 媒体規約（規則 00 §12）は実質 tutorial/reports にしか適用されていない |
| 3 | **節点のファイル番号が不揃い** | 節点1 は `02_` が 2 本、節点2 は `01_`・`02_` が各 2 本、節点3 は `03_` が無い、節点4〜8 は 00/01/05 だけ | 「03 はどこ？」が毎節点で起きる |
| 4 | **見本と演習が同じ名前空間** | `docs/10_requirements/R-101-R60Area.yaml`（見本）と `tutorial/.../节点1/R-201`（演習） | R-101 を演習と誤解しやすい |
| 5 | **一度きりの調査出力が 4.1MB** | `module-survey` 3.4MB＋`legacy-raw` 376KB＋`ingest` 374KB | 容量の 84% を占める。結論は別途保存済み |
| 6 | **Office のロックファイルが残存** | `节点1_需求/.~lock.03_客户確認依頼書（AB類）.pdf#` | 単なるゴミ |
| 7 | **`reports/drill` の 6 ファイルに中文ビューが無い** | `human-answer-sim.md`／`requirement-defects.md` 等 | 訓練記録の可読性が揃わない |
| 8 | **`docs/00_plan/tasks.md` は全タスク `pending` のまま** | Task 1〜22 すべて `pending` | 実際は完了している。履歴として残すなら注記が要る |
| 9 | **`gen_view` の chrome は直したが、本文の言語判定はしない** | `.zh.md` を書く人の責任 | 中文ビューに日文が混ざっても機械は止めない（意図的な設計） |

---

## 13. 「さらに深く整理する」場合の選択肢

| # | やること | 得られるもの | 代償・危険 |
|---|---|---|---|
| A | **節点ファイルの番号を統一**（`02a_`/`02b_` 等に振り直す、または `00_入力 → 10_AI産出 → 20_審査 → 30_承認` の 10 番台に） | 「03 が無い」問題が消える | 全節点のファイル名変更＋SKILL の 9 作業票＋`nNN.yml` の `artifacts`＋`使用手册` の記述を同時更新。**参照が広いので一括置換の事故が起きやすい** |
| B | ~~入口を 2 本に統合~~ **→ 一部実施（2026-10-28）**：`START_HERE.md` を `使用手册.md` へ統合。`AGENTS.md` の移動は**未実施** | ルート直下の人が読む文書が 1 本減った | `AGENTS.md` を動かすには `docs/00_plan/review.md` CP-R-1（6 根級ファイルの存在を要求）と `CLAUDE.md §0` を同時に直す必要がある |
| C | **見本（R-101 系）に印を付ける**（ファイル名先頭に `_sample_`、または `docs/_samples/` へ） | 演習との混同が消える | `traceability.yml`・`review.md`・`tasks.md` のパス参照を全部直す |
| D | **一度きりの調査出力を削除**（`module-survey`・`legacy-raw`・`ingest`） | 4.1MB 減る | 再調査のコスト。**結論は `module-selection.md` に在るので実害は小さい**（あなたの判断で「全部残す」となった経緯あり） |
| E | **`docs/` にも中文ビューを付ける** | 媒体規約が全域で成立 | 58 本 × 翻訳。**規約を「節点成果物のみ」と明文化する方が安い** |
| F | **`tasks.md` を完了記録として閉じる** | 「pending だらけ」の誤解が消える | 計画文書の性質を変える（`phase0-closure.md` と役割が重なる） |

---

## 14. 関連ドキュメント

- `docs/90_knowledge/platform-map.md` — 7 層平台・4 層知識モデルへの対応（**層の視点**）
- `docs/90_knowledge/ppt-deviation-register.md` — PPT に無い追加要素の登録簿
- `使用手册.md`「三分钟版」§6 ディレクトリ導覧 — 新人向けの「どこを開くか」（**本書の要約版**）
- `使用手册.md`「文件都去哪了」 — 同上（より詳しい）
- `ROADMAP_3PHASE.md` — Phase 1/2/3 の計画

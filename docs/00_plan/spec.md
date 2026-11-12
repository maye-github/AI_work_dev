# AI 全流程开发步骤正式落地（朝日ビール R60 共通マスタ实战化） - Product Requirements Document

> **★状態（2026-10-28 追記）**: 本文件は**旧 Trae 期の計画文書**であり、現在の基準ではない。
> - **いまの基準**は `AI全链路软件工程平台_实施规格书.md`（プラットフォーム像）と
>   各節点の作業票（`.claude/skills/trans-cosmos-ai-lifecycle-coach/nodes/*.md`）。
> - 本文中の `AGENTS.md` は `docs/00_plan/roles.md`、`ROADMAP_3PHASE.md` は `docs/00_plan/roadmap-3phase.md`、
>   `CONTRIBUTING.md` は `.claude/rules/05-commit-messages.md` §7 に移設・統合済み（2026-10-28）。
> - 受入の判定は `docs/00_plan/review.md`（CP）と `reports/AC-selfcheck.md` で行う。本文件の AC 記述は当時のものである。

> **⚠ 訂正注記（2026-10-12 追記）** — 本文件は旧 Trae 期の計画文書であり、以下の点を訂正した。
> 原文は「骨架を `D:\AI_work` 根に落とす」と書いていたが、**実際の骨架は `D:\AI_work_dev` にある**。
> `D:\AI_work` は **R60/JET の歴史案件（参照元）** であり、落地先ではない。混同を避けるため
> 落地先の記述のみ `D:\AI_work_dev` に訂正し、**参照元としての `D:\AI_work` 記述はそのまま維持**した。
> 併せて、実在しないパス（`D:\maye\other` / `D:\maye\knowledge`）と失効した行数（`project_memory.md §18-§26 = 241 行`）を
> 実態（知識庫は `D:\TraeWork_memory\`）に合わせ、実行コマンドを `py -3 -m tools.trace_check` に統一した。
>
> **さらに 2026-10-14 追記**：下記 Constraints Technical 1・2 の「既存スタック」の**値の唯一真源は
> `docs/01_context/case-profile-R60.yaml`** である。骨架本体（`CLAUDE.md` 紅线④・`.claude/rules/`）は
> 特定案件のスタック値を固定せず、案件プロファイルを参照する形へ分離した。
> 本節は**旧 Trae 期の記述として履歴保存**する（消さない）。スタック値を引用するときは案件プロファイルを見ること。

## Overview
- **Summary**：按照《AI実践に基づくソフトウェア開発プロセスの再考_落地篇.pptx》PART01-PART04（8 工程落地後形态 × 人机RACI × 成果物6原則 × 7层平台架构 + 3 段阶 Phased 落地） 的具体规范，结合本仓库已有的 R60 Area/Code/Item 3 个代表模块历史实际代码（Front-end: views/R60Area.vue + components/R60AreaEdit.vue + service/R60AreaService.ts；Back-end: routers/R60AreaController.py；共通：R60Common.ts + r60const.py），正式产出一套可直接复用到任何同类对⽇ Vue3+FastAPI+Oracle 项目的 **AI 全流程开发 8 工程 × 4 级验收 × Claude Code 单工具执行（人担当评审门）× Git+ID 追溯体系 × 机密脱敏规则 × 6 周执行计划 × R60 已有资产的 3 模块示例** 的完整方案，并以代码骨架、规则文件、YAML 模板、示例机读成果物、CI 本地脚本等实际可运行资产落入 `D:\AI_work_dev` 项目根。
- **Purpose**：把已存入知识库（`D:\TraeWork_memory\`）的规范与方法论，从「知识」变成「可执行」；R60 本体从零散 AI 使用 → 全链路 AI 化，并可复制给下一 批 Harmony/酒税/SDS 等同构项目。
- **Target Users**：R60 团队 SE（上流定義·日方合意）·PG（编码·レビュー）·テスター（観点設計·合否）·AI 推進担当（模板·知识·度量）。

## Goals
1. 落地篇 PPT 30 页 × 4 PART 做到 **每页可追溯到本项目 1 套实际资产**（不是文档，是可执行的 rules/skills/ids.yml/spec 模板）。
2. 工程篇 S9-17 的 8 大工程，**每个工程产出本项目可复用模板 1 套 + 以 R60Area 作 R-101/F-042 全链路示例 1 套**，从 R-ID 贯通到 TC-ID，证明追溯不断链。
3. 成果物篇 S18-24 的 **二重化**：机读源（.md+YAML）→ 日文正式 Excel/Word 的 gen_formal 脚本模板 1 套，严格单一数据源（禁手改日文版）。
4. 平台篇 S25-30 的 **7 层架构最小可行落地**：利用层/编成层/能力层用 Claude Code＋Python 脚本实现；知识层绑定现有 project_memory.md + doc/；数据层绑定 Git+ids.yml；统制层=机密分级清单+6 重 CI 门禁脚本；基盤层=现有 Oracle/Auth0/S3。
5. 落地篇 S30 3 段阶 Phase 1/2/3：**Phase 1（1~2 ヶ月）的完整清单落地**，剩余 Phase 2/3 明确写入 roadmap.md 作为后续任务。

## Non-Goals
- ❌ 不修改 R60 现有 `src/` / `tests/` / `app/routers` **任何生产代码**，除非是 example 文件或骨架目录。
- ❌ 不造新的 AI 平台产品（不搭自建 7 层平台后端），仅用现有 Claude Code / Git / Python 脚本 **最小可行落盘**；Phase 2/3 平台化不在本次实施。
- ❌ 不做 32 模块全量登记，只做 **R60Area（简单）/ R60Code（中等）/ R60Item（复杂 Multi）** 3 个代表模块的全链路 ID 贯通示例；其余模块按 开球周盘点 SOP 后续登记。
- ❌ 不生成最终交付版日文正式 Excel/Word（需要客户模板和脱敏审批，占位留脚本）。

## Background & Context
1. **知识库现状**：知识库は `D:\TraeWork_memory\`（`knowledge_ai_software_engineering.md` = 両 PPT の逐页転写、`project_memory.md` = 原始硬約束、`正式创建与落地.md` = Trae 構築ログ、`knowledge_reference_materials.md` = 参考資料 9 本）に存在する。両 PPT の内容は学習・吸収済みで、実行層への転換が本次作業である。**訂正**: 原文が参照していた `D:\maye\other` / `D:\maye\knowledge` は**実在しない**。`project_memory.md` も現在 11 行（原文記載の「241 行·26 章」は失効）。
2. **R60 资产现状**：32 模块 Vue3 + FastAPI，R60Area 最简单（cmpCd/jigCd/araCd 3 键 55 字段），R60Code 中等（区分値/メッセージ/ｺｰﾄﾞ体系），R60Item 最难（Multi+Help+CSV+排他）；现有文档 `doc/02_INPUT/` 已含日方規約/DB定義/画面規約/旧Javaソース/DDL。
3. **当前痛点（PPT v1 S3-4 与 R60 现状吻合）**：
   - 32 模块生产代码与 AI 流程 **未结构化挂钩**（无 R-ID、L-ID、无设计代码自动双向追溯）。
   - 共通 R60Common（54+函数）/ r60util（31 类）经验存在但 **无 AI 技能化描述**（不能被 Claude Code Skill 自动调用）。
   - 机密分级清单缺失（AES/连接串/Auth0/S3 现在散落 .env），**违背 PPT S28 选型順序第一条**。
   - 无 6 重 CI 本地门禁（目前仅有前端 npm build / 后端 pip install 的构建动作）。
4. **参考案例实绩**（已学）：R60/JET 自身 22 API × 25% 削減 + SDS3 月 45 元/人 + SDS2 品質 86%↑ + Harmony 70% 削減 + 访谈片 15/18 自动化，说明方法论可落地。

## Functional Requirements
- **FR-1 标准骨架落地（§24 7 子目录规则 + §25 ids.yml）**：在 `D:\AI_work_dev` 根新建 `.claude/rules/`（6 份 rule 文档：project-global/req/design/test/commit-message/security）、`.claude/skills/code-from-design-trans-cosmos-ai/`（JET 版を再構成した 4 Skills）、`CLAUDE.md` + `AGENTS.md`、`docs/00_registry/ids.yml` + `glossary.yml` + `traceability.yml`、`docs/_samples/01_context/R-101-R60Area.md`、docs/10~99_inbound 标准目录。
- **FR-2 8 大工程操作模板（落地篇工程篇 S9-17）**：docs/10_requirements/ 放 `req-template.yaml` 与 `R-101-R60Area 示例`；docs/20_basic_design/ 放 `bd-template.yaml` 与 F-042-I-201~256 示例；docs/30_detail_design/ 放 `dd-template.yaml` 与 L-014/L-015 例（含 SQL/エラー一覧/境界値）；docs/40_framework/ 放选型记录；docs/50_unit_test/ + 60_integration_test/ 放 `tc-template.yaml` TC-001+TC-002 例；docs/70_release/ 放 `release-template.md`。
- **FR-3 成果物二重化（PPT S20-S24 成果物6原則 + 二重形态）**：tools/gen_formal/ 放 `gen_excel.py` + R60 日文 Excel 模板占位；tools/trace_check/ 实现 §25.4 CI 6 门闸中的 ①ID 合法②追溯完整③front-matter 七字段④生成一致（本地可 `py -3 -m tools.trace_check --strict` 直接跑）。
- **FR-4 机密与脱敏分级清单（PPT S27-S28 选型順序第一条）**：`.claude/rules/01-security-redlines.md` + tools/masking/ 双向脱敏脚本 `mask_demo.py` + `masking_dict.example.json`（真实字典占位 .gitignore，词典不进 Git）。
- **FR-5 6 周执行计划 开球周验收（§23）+ R60Area/R60Code/R60Item 三模块评审差分资产**：tools/kb-platform/repo/projects/P-R60-001/review/ 为 3 模块各建 `R-xxx/{review_before,review_after,review_comments.md}` 目录结构 + R60Area 1 份填充实例（从 doc/01_内部用資料/ 已存 QA 票和修正依頼抽出），写清操作 SOP 满足新人猜中率 ≥70% 验收。
- **FR-6 Git 运行规范（§25）+ CI 本地门禁脚本**：CODEOWNERS、`CONTRIBUTING.md`（分支 req/R-xxx + R-xxx/01-req~07-release；7 种 Commit 类型：req/design/feat/test/fix/rel/chore；baseline/R-xxx/basic-v1.0 Tag 约定）；.github/workflows/ai-gate.yml 占位（本地上传切换）。
- **FR-7 7 层平台最小可行落地映射表（PPT S26-27）**：tools/kb-platform/repo/company/standards/platform-map.md，把 7 层每层都对应到「本仓库已有/本次新建/Phase 2 实施」三件套。
- **FR-8 Phase 1 清单落地（PPT S30 3 段阶）+ Phase2/3 路线图**：`ROADMAP_3PHASE.md` 写入 R60 Phase1 全 16 条待办 × Phase2（3-6 ヶ月）/ Phase3（6-12 ヶ月）具体条目与验收指标。

## Non-Functional Requirements
- **NFR-1 单一源一致性（PPT S20 4 条単一ソース）**：所有 R-ID/F-ID/I-ID/D-ID/L-ID/E-ID/TC-ID 的唯一发号口是 docs/00_registry/ids.yml，任何野号被 trace_check 打回；本项目不允许同一业务字段在两份 MD 文档中重复定义（除非是中文 Glossary + 日文正式版自动生成的 pair）。rule：`grep 字段名 → 唯一 hit 位置 = 定义处`。
- **NFR-2 机密红线不越界（PPT S27 セキュリティ 6 要素）**：masking_demo 中可识别真实 Oracle/Auth0/AWS 值的关键字（接入ユーザ/内部 IP/接続ユーザ）**必须替换成 TBL_1/COL_1/PWD_1/IP_1** 占位（规则 01 §L3 第 1・6・7 条）；masking_dict.json 加入 .gitignore；在 01-security-redlines.md 写清单：公开可 / 需脱敏 / 禁止外投 3 级覆盖 §14 Lessons Learned 中已列明的 13 项敏感点，任何 trace_check 未脱敏敏感词打 Exit 1。
- **NFR-3 可追溯闭环（PPT S16 7 連携ﾒｶﾆｽﾞﾑ）**：trace_check.py 必须双向检查 R→F→I→D/L→Code→TC 不断链；反向 TC → req_ids →设计→需求 也可通；R60Area 示例闭环 1 条 R-101 → L-015 → TC-003。
- **NFR-4 新人 2 小时可上手（Phase1 目标值，对应落地篇 S6 SE/PG 角色再定义）**：tools/kb-platform/repo/company/patterns/howto/onboarding.md 含 10 条 walkthrough，执行后新人能独立走通 `R-ID 发 → BD → DD → Claude Code 造代码 → trace_check → commit` 全流程；rubric 评分 ≥80。
- **NFR-5 无侵入不破坏生产（非 Goal 1）**：本次新建目录/文件**必须全部出现在 .gitignore 的可选忽略白名单**中，可一键 `git add AI_FULL_LIFECYCLE=1` 时才纳入，默认不影响现有 R60 代码 Git 仓库构建与部署；现有 src/、app/routers 零修改。
- **NFR-6 跨平台本地可実行（対応 §25 CI スクリプトが Git サービス非依存）**：tools/ 配下は Python 標準ライブラリのみに依存（`pyyaml` のみ許可）；trace_check は追加依存なし。**リポジトリルートで** `py -3 -m tools.trace_check --strict` が Windows／社内網でそのまま実行できる（外部モデル・外部サービス不要）。
  > コマンド統一の理由: Windows では裸の `python` が Microsoft Store のスタブに解決される環境があり、`python -m` は起動しないことがある。`py -3`（Python Launcher）を唯一の起動子とする。

## Constraints
- **Technical**：
  1. Vue3 + `<script setup>` + TypeScript + PrimeVue + Pinia + Vite（现有栈，不允许替换 React 或 Angular）。
  2. FastAPI + Pydantic BaseCamelModel（snake↔camel alias_generator） + SQLAlchemy + oracledb Thin（现有栈，不替换 PostgreSQL/MySQL）；SQL 文 2026-05 约定 ROWID vs OFFSET-FETCH 参照 doc/01/OFFSET_FETCH_ROWID 修改报告。
  3. Oracle：`NLS_DATE_FORMAT = 'RR-MM-DD'` 不可变；加密方式不在骨架层固定，由案件档案（`migration`）或工程 04 已批准设计（`greenfield`）确定；R60 实案**不是 AES-256-ECB**，而是既有设计书规定的「逐位变换＋当日 `yyyymmdd` 加算」，解密使用 `R60_DECRYPTION_FNC`。
  4. 现有 R60Common.ts 54 项函数、r60util.py 31 util 类为唯一设计/代码真源（不造新版 parallel），AI Skill 必须在注释里映射到共通函数。
  5. Git：不装 Git 新服务；.github 仅占位；内部 GitLab/Gitea 用户可自行复制 workflow；统一脚本支持 Windows PowerShell 5。
- **Business**：
  1. `doc/02_INPUT/10.規約/` 的「基刷_調達生産_マスタ_画面共通仕様書_v1.2.xlsx」「画面規約_v1.1.xlsx」「コーディング規約_v1.0.xlsx」是日本客户正式验收基准，任何 AI 模板必须吻合。
  2. 不泄露朝日ビール真实项目数据给任何外部模型；机密 Level=禁止外投。
- **Dependencies**：
  1. 知識庫 `D:\TraeWork_memory\` の 4 文書（`knowledge_ai_software_engineering.md` / `project_memory.md` / `正式创建与落地.md` / `knowledge_reference_materials.md`）。
  2. ~~D:\maye\other + D:\maye\knowledge~~ → **実在しないパス。原文の記載ミス**。参考資料 9 本は上記 `knowledge_reference_materials.md` に既に統合済み。
  3. doc/ 现有 200+ 设计文档（00_管理/01_内部用資料/02_INPUT）。
  4. R60 已识别 Lessons：当日 Key（非 AES）、NLS、PrimeVue Select、Blob JSON 拦截、ROWID 分页、A/B 测试 32 模块健康度（§ Lessons Learned）。

## Assumptions
1. 走默认推荐口径（之前 AskUserQuestion skip）：落地到 `D:\AI_work_dev` 根·三模块 R60Area/Code/Item·机密清单+脱敏脚本·Python 本地 + GitHub Actions 占位。若用户不认可，再返回 Specify 调整。
2. 开球周评审差分资产实操：实际写 review_comments.md 时，使用「doc/00_管理/QA票共通マスタ.xlsx」和修正依頼里的公开字段，不引述实际数据值（避免违反 NFR-2 假设）。
3. 日文正式 Excel 模板暂时不包含朝日ビール客户指定的公司抬头 Logo 等（Phase2 再补）。
4. JET 的 Skill V3 4 件套 AI 技能 与 JET 原实现细节可参考但不可直接拷贝（只拷贝约定部分；不引述别家客户代码）。
5. Phase 1 的 KPI 基线值（S29 6 KPI），在 ROADMAP 里留公式和占位，实际值必须是真实项目 1 个月跑完后填入。

## Acceptance Criteria

### AC-1: 标准骨架落盘完整对应落地篇
- **Type**: `rule`
- **Given**: 干净的 `D:\AI_work_dev` 目录（不包含本次骨架）
- **When**: 对本次创建的文件/目录运行清单比对
- **Then**: 满足「6 rules + trans-cosmos-ai skills 1 套 + CLAUDE.md/AGENTS.md + ids.yml/glossary.yml/traceability.yml + R-101 context + docs/10~99_inbound 标准目录」一一存在，对应 PPT PART01 落地後形态（S4 8 工程×S6 新設 AI 推進担当×統制セキュリティ）
- **Pass Condition**: `ls .claude/rules/*.md | wc -l ≥ 6` 且 `ls docs | wc -l ≥ 18` 且 `CLAUDE.md` 前 10 行含「落地篇 30 页」「7 条红线」两个关键词
- **Evidence**: PowerShell 命令结果 + CLAUDE.md 头 20 行快照

### AC-2: 8 工程 YAML 模板 × R60Area 全链路贯通示例
- **Type**: `rule`
- **Given**: 已生成的 FR-2 全部模板与 R60Area 示例
- **When**: `cd D:\AI_work_dev && py -3 -m tools.trace_check --strict --report reports/trace_R101.json`
- **Then**: R-101 → F-042 → I-201~256（56项目，对应 R60Area 56 DB 字段）→ D-043 → L-014, L-015（initEdit/search 2 业务逻辑）→ E-001~005（5 个常见错误码 R60W0010/0006/0014/0024/E0025）→ TC-001~TC-008（3 正常+2 境界+3 异常，每个 TC 带 design_id + req_id）链路上不缺 ID；所有 front matter 的 7 字段（id/type/req_ids/status/sensitivity/owner/version）齐全且 status 在 {draft,open,baselined,changed,done}
- **Pass Condition**: Exit code 0，报告 JSON 中 chain_complete=true / orphan_ids=[] / field_count=56
- **Evidence**: trace_check 控制台输出 + reports/trace_R101.json key stats

### AC-3: 成果物二重化 & 单一源严格执行
- **Type**: `rule`
- **Given**: 已填充的 R60Area 示例
- **When**: ①执行 `tools/gen_formal/gen_excel.py --dry-run --module R-101`；②运行 grep：`grep -rn "受払場所コード" docs/10_requirements docs/20_basic_design docs/30_detail_design`
- **Then**: ①dry-run 输出字段数=56（与 I-201~ 一致，说明转换表正确）；②grep 命中行 ≤1（仅 docs/30_detail_design 定义处；其他 docs 只能用 source_req 引用，不可重复写同定义）
- **Pass Condition**: 两项均 True
- **Evidence**: gen_excel 日志行 + grep 计数

### AC-4: 机密分级 + 脱敏 demo 自检通过
- **Type**: `rule`
- **Given**: `.claude/rules/01-security-redlines.md`、`tools/masking/`（`__init__.py` + `mask_demo.py` + `masking_dict.example.json`）
- **When**: ①`py -3 -m tools.masking.mask_demo --self-test`；②`py -3 -m tools.trace_check --strict --only-check secrets`
- **Then**: ①mask_demo self-test は**架空フィクスチャ**（`oracle+oracledb://demo_user:demo_pass_xxxx@198.51.100.11:1521/DEMODB1` 等 3 行。RFC5737 の文書用 IP を使用）を入力に取り、脱敏後の出力に `[[PWD_1]]` / `[[IP_1_1]]` / `[[SID_1]]` / `[[TBL_1]]` / `[[COL_1_*]]` / `[[BUCKET_1]]` / `[[PROFILE_1]]` / `[[DOM_1]]` の占位が現れ、かつ `reversible=True`（原文へ完全復元）で Exit 0。stdout に `mask_hits=<n> unmask_ok=true exit=0` を出力。**実環境の値は使用しない**（テストベクタに実値を書くことは本 AC が禁じる行为そのものである）；②trace_check secrets check Exit 0（`docs/**`・`reports/**` を含む走査対象に、マスクされない機密の形が 1 件も現れない）
- **Pass Condition**: ①双向还原 OK ②secrets check Exit 0
- **Evidence**: mask_demo 测试输出 + trace_check secrets 报告

### AC-5: 开球周评审差分资产 SOP 可操作 + R60Area 1 份示例填充
- **Type**: `rubric`
- **Dimension**: 开球周资产配对「新人猜中率模拟 + review_comments 结构完整度」
- **Scale**: 1-5（1=review_comments 无分类; 2=只有原因, 没有为什么→怎么改; 3=5 模板全有（问题/根因/修正/予防/关联R-ID）但没举例；4=5 模板 + R60Area 具体 3 条（从 doc/QA 票引述问题编号 + 场景）；5=5 模板+10 条评论，且新人盲猜验证模拟（用 review_after vs review_before 对照）还原度 ≥70% ）
- **Pass Threshold**: ≥ 4
- **Evidence**: review_comments.md 全文（10 条评论）+ 模拟猜中率的统计段

### AC-6: 6 重 CI 门闸脚本本地自检通过
- **Type**: `rule`
- **Given**: tools/trace_check.py（实现 6 重前 5+代码/密钥共 6）
- **When**: `cd D:\AI_work_dev && py -3 -m tools.trace_check --strict --gate 6`
- **Then**: 6 重结果都 pass：①ID 合法 ②追溯完整 ③front-matter OK ④生成物一致（gen_formal dry-run 字段数==I-ID 数）⑤空跑代码 ESLint 占位（对前端 vue-tsc --noEmit 的 docs 级等价：不允许模板 YAML 中 snake/camel 命名出现不一致：如 cmp_cd vs cmpCd 仅在各自位置合法，混写打回）⑥ gitleaks 自检（内置关键字扫描 mask 后是否全 0 hit）
- **Pass Condition**: Exit 0 + gate6_report.json 中 pass=6/fail=0
- **Evidence**: gate6_report.json stats + 控制台 summary

### AC-7: 7 层平台映射 + 3 Phase Roadmap 完整覆盖落地篇 S25-30
- **Type**: `rule`
- **Given**: platform-map.md + ROADMAP_3PHASE.md
- **When**: 人工逐条核对 7 层 × 2 个文档（每个对应 3 件事：已/本次/Phase 2+）+ 3 Phase 条目（Phase1 16条 / Phase2 12条 / Phase3 8条）
- **Then**: ①7 层每层 ≥2 条「本次新建」映射不空缺；②Phase1 全 16 条含负责人位·预计完成日·基线·验收公式；③Phase2/3 各条目均有「对 PPT 第 x 页→xxx 条」引用
- **Pass Condition**: 3 子条件全 True
- **Evidence**: Check-list 快照（Spec 文档 Review 阶段独立检查员打勾记录）

### AC-8: 新人 Walkthrough 可操作性
- **Type**: `rubric`
- **Dimension**: Onboarding 2-hour walkthrough 流畅度
- **Scale**: 1-5（1=跳步骤/不可跑；3=步骤齐全但每步超10分；4=≤90分完成 10 条 checklist 全部 7/10 通过；5=≤60分 10/10 且能自动产出 TC-009 新用例 1 条过 trace_check）
- **Pass Threshold**: ≥ 4
- **Evidence**: onboarding-checklist.md 10 条任务 + 本地模拟执行记录（时间·命令·输出快照）

## Open Questions
- [ ] 开球周评审差分资产实操：R60Code/R60Item 的填充量级，是否按与 Area 同等（10 review_comments）做，或留 SOP 空壳由后续人填 → 默认 Area 填充 10 条 / Code+Item 填 3 条示例 + SOP 留足（Assumption #2）
- [ ] 是否要引入实际的 GitHub Actions / 内网 GitLab CI runner / 脚本直接对接现有 Jenkins？→ 默认两者都不做，仅 .github/workflows/ai-gate.yml 占位（NFR-5/Constraints Technical #5）。
- [ ] gen_formal 脚本是否要接入真实 R60 日文 Excel 模板？→ 暂留占位，待客户侧提供（Phase2）。
- [ ] 是否需要生成 JET 同版本 Skill（code-from-design）的 .claude/skills 完整 SKILL.md，还是仅放 Rule 级映射？→ 默认完整放 SKILL.md 4 件套但改名 code-from-design-trans-cosmos-ai 避免与 JET 同名冲突。

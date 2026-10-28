---
id: FILE-INVENTORY-2026-10-28
type: knowledge
req_ids: []
status: draft
sensitivity: internal
owner: AI-SE
version: 0.1.0
---

# 逐文件清点（断舍离用）— 2026-10-28

> **这份文件回答三个问题**：这个文件是干什么的、谁在用它、能不能删。
> 判定的依据全部可复算：`git ls-files` 701 个文件、入向引用图（脚本第 §12 节）、
> 以及首部/全文阅读。**凡「用途」栏带 ※ 的，是我只读了首部或据目录结构推定，没有通读。**
>
> **这不是唯一真源**。真源仍是各自的文件。本文只是**一次性清点**，清点完可以作废。

---

## 0. 五个判定标记

| 标记 | 含义 | 是否需要你点头 |
|---|---|---|
| **留** | 原样保留 | 否 |
| **删** | 可以删，风险已评估 | 删「可逆」类不需要；删「不可再生」类需要 |
| **并** | 内容并入另一处，本文件消失 | 需要 |
| **移** | 换路径或改名 | 需要（引用面广） |
| **重组** | 目录结构变化 | 需要（一次决定，影响全仓） |

「可逆」＝删了还能用一条命令重新生成，或 git 历史里就有。

---

## 1. 乱在哪：55% 的体积是三类东西

| 类别 | 文件 | 体积 | 占比 | 性质 |
|---|---|---|---|---|
| 一次性调查产物（module-survey 234 ／ legacy-raw 29 ／ ingest 7） | 270 | 3.5 MB | 25% | 跑过一次，结论已存别处 |
| 生成物 `.zh.html` | 38 | 2.4 MB | 17% | 机读源的派生物 |
| 自动备份 `_backup/*.bak` | 54 | 1.7 MB | 12% | 每次发号都新增一个 |
| **小计** | **362** | **7.6 MB** | **54%** | **都不是「真源」** |

剩下的 46%（339 个文件、6.5MB）才是真东西：规则、skill、agent、工具、工程产物、演练记录。

**但体积不是唯一的乱。** 第二个乱是**说明文有 5 个版本**：

| 文件 | 行数 | 讲什么 | 和谁重复 |
|---|---|---|---|
| `CLAUDE.md` | — | AI 的常时约束 | 角色表与 `AGENTS.md` 重复 |
| `START_HERE.md` | 285 | 新人唯一入口 | 8 节点表与 `使用手册` 重复 |
| `使用手册.md`（1053 行 51KB）＋`.zh.html`（95KB） | 1053 | 全功能手册 | 包含上面两本的内容 |
| `AGENTS.md`（**未入 git**） | 241 | 14 个角色定义 | `CLAUDE.md §0` + RACI 与规则 02 §8 重复 |
| 规格书（78KB） | — | 目标态（不是现状） | 与 `使用手册` 的"为什么"部分重叠 |

**入口 5 本、共 190KB 的说明文，讲同一件事。** 这是"打开就晕"的真正原因——不是文件多，是**同一件事有五个说法，且没有一处写着"以我为准"**。

第三个乱：**盘上有、git 里没有**的 4 个文件（`AGENTS.md`／`ROADMAP_3PHASE.md`／`CONTRIBUTING.md`／`CODEOWNERS`）。
别人 clone 下来拿不到，但它们被其它文档引用着。

---

## 2. 总账

| 区域 | 入库 | 盘上另有 | 小计 | 判定分布 |
|---|---|---|---|---|
| 根目录 | 7 | **4** | 11 | 留 8 ／ 并 2 ／ 待定 1 |
| `.claude/` | 40 | 0 | 40 | 留 40 |
| `tools/` | 41 | 0 | 41 | 留 41 |
| `docs/` | 190 | 0 | 190 | 留 131 ／ 删 55 ／ 并 4 |
| `tutorial/R60Login/` | 111 | 0 | 111 | 留 110 ／ 删 1 |
| `reports/` | 311 | 0 | 311 | 留 35 ／ 删 274 ／ 待定 2 |
| `eval/` | 1 | 0 | 1 | 留 1 |
| **合计** | **701** | **4** | **705** | **留 366 ／ 删 330 ／ 并 6 ／ 待定 3** |

> 根目录那 4 个「盘上另有」是 `AGENTS.md`／`ROADMAP_3PHASE.md`／`CONTRIBUTING.md`／`CODEOWNERS`，
> 被 `.gitignore` 排除，**clone 下来不存在**，但其它文档引用着它们。
>
> 删除的 330 个里，**329 个是可逆的**（自动备份 54 ＋ 一次性调查 270 ＋ 孤立产物 5）。
> 真正需要你想一下的只有 **6 项**，在 §11。

---

## 3. 根目录（11）

| 文件 | 用途 | 谁在用 | 判定 | 说明 |
|---|---|---|---|---|
| `CLAUDE.md` | AI 的常时约束；7 红线 / 禁止 5 条 / commit 样式 / 设定表 | **AI 每轮自动加载** | 留 | 唯一被自动加载的入口。不能动 |
| `START_HERE.md` | 新人门：走哪 8 步、说哪 10 句话 | 人 | 留 | 与 `使用手册` 重号（见 §4 问题 1） |
| `使用手册.md` | 1053 行全功能手册 | 人 | 并 | **建议作为"唯一的人读说明书"**，把 `START_HERE` 与 `AGENTS` 吸收进来 |
| `使用手册.zh.html` | 上面那本的中文视图（95KB） | 人 | 留 | 生成物；改了 md 要重新生成 |
| `AI全链路软件工程平台_实施规格书.md` | 目标态定义（78KB） | 企划/管理 | 留 | **不是现状**，是要求。与我的调查报告对照着看 |
| `AGENTS.md` ※ | 14 个角色 + RACI | 人 | 并 | **未入 git**。角色表与 `CLAUDE.md §0`、规则 02 §8 三重重复 |
| `ROADMAP_3PHASE.md` ※ | 三期计划 | 管理 | 待定 | **未入 git**。与规格书 §14 是两套分期，同名不同物 |
| `CONTRIBUTING.md` ※ | 分支/Tag 规约 | 开发 | 留（需入库） | **未入 git**。内容是 commit 规则的补充，建议并进规则 05 |
| `CODEOWNERS` ※ | 11 块审批人 | Git | 留（需入库） | **未入 git**。红线③的机械可读证据，应当入库 |
| `.gitignore` | 忽略规则 | git | 留 | 2026-10-28 已改：docs/tools/reports 转为默认入库 |
| `.vscode/extensions.json` | 推荐扩展 | 编辑器 | 留 | 1 行，无害 |

---

## 4. `.claude/`（40）

### 4.1 `rules/`（7）— 全部保留

起動時に自動ロードされる。**删任何一本都要同时改 CLAUDE.md §0 的表。**

| 文件 | 管什么 | 判定 |
|---|---|---|
| `00-project-global.md` | 工程横断 13 条（加密按案件、ROWID、野号、成果物两份、媒体契约…） | 留 |
| `01-security-redlines.md` | L3 机密 13 项 + 脱敏占位。**gate6 唯一豁免文件** | 留 |
| `02-requirements.md` | R/Q 发号 SOP、A/B/C 分类、回答接收、状态机、上流字段移送检查 | 留 |
| `03-design-coding.md` | `BaseCamelModel` 4 行、snake/camel 分区、SQL 白名单 | 留 |
| `04-testing.md` | TC 正3/边2/异3、`design_ids`、双向闭包 | 留 |
| `05-commit-messages.md` | commit 7 种 + Trace/AI/Review 三段 | 留 |
| `06-knowledge-flywheel.md` | 踩坑→规则化→加检查→全队免疫；**红线不加条**原则 | 留 |

> **唯一的结构问题**：CLAUDE.md 常时加载 ≈ 12KB，7 条规则 ≈ 105KB，加起来 **117KB 在每轮对话开头**。这是"AI 抓不住重点"的物理原因。断舍离时可以考虑：规则 02 已经 400+ 行，可以拆成"必读 30 行 + 附录"。

### 4.2 `skills/`（18）— 全部保留，但有一件要确认

| skill | 文件 | 何时启用 | 判定 |
|---|---|---|---|
| `trans-cosmos-ai-lifecycle-coach` | `SKILL.md` + `nodes/n01..n09`(9) + `references/node-worker-contract.md` + `templates/{case,node}.yml` = 13 | **8 工程的唯一推进入口** | 留 |
| `requirement-interrogator` | `SKILL.md` + `references/lenses.md` = 2 | 节点 1 的 51 视角审问 | 留 |
| `virtual-requirement-author` | `SKILL.md` | 节点 0 倒推（仅 migration） | 留 |
| `code-from-design-trans-cosmos-ai` | `SKILL.md` | 只有 R-101 系 / migration 的制造 | 留（**内容里写死 R-101，是待修项**） |
| `legacy-r60-navigator` | `SKILL.md` | 旧 R60 只读导航 | 留 |

> **要确认的一件事**：`code-from-design` 与 `legacy-navigator` 都**只对 R60 有意义**。如果这个骨架要卖给别的客户，这两个 skill 是"附赠 R60 资产"还是"核心能力"？——影响它们该不该留在主目录（见 §11 问题 4）。

### 4.3 `agents/`（14）— 全部保留

**注意：agent 是靠 `description` 自动匹配的，不是靠路径引用。所以"引用数 0"对 agent 是正常的，不能当死文件。**

| 文件 | 职责 | 判定 |
|---|---|---|
| `trans-cosmos-ai-node1-requirements` … `node8-release-ops`（8） | 每个节点一个执行体，独立上下文出初稿 | 留 |
| `trans-cosmos-ai-node9-change` | 变更环产出 | 留 |
| `spec-reviewer` | 独立审查（重跑命令，不信提交方的话） | 留 |
| `secret-auditor` | 机密扫描（只报文件行，不打印值） | 留 |
| `deliverable-reviewer` | 视图生成 + A/B/C 分类 + 确认请求书 | 留 |
| `drill-comparator` | 训练对比归因（不判合格） | 留 |
| `legacy-module-surveyor` | 旧模块选型普查 | 留（同上，R60 专属） |

### 4.4 `settings.json`（1）

| 内容 | 判定 |
|---|---|
| deny 5 条（机密文件/.env/密钥）+ 钩子 2 个（SessionStart 注入当前进度；Stop 重画 Excel 预览） | 留 |

---

## 5. `tools/`（41）— 全部保留

**这块是整个仓库最干净的部分。** 没有重复实现，没有孤岛，每个包都有入口。

| 包 / 文件 | 文件数 | 干什么 | 判定 |
|---|---|---|---|
| `trace_check/`（`__init__`/`__main__`/`aux_checks` ＋2 个 example json） | 5 | **6 道门** + seal + freeze | 留 |
| `trace_check.py` | 1 | 568 字节的启动器，等价于 `-m tools.trace_check` | 留 |
| `gen_view/`（`__main__`/`render`/`__init__`/README） | 4 | 机读源 → 人看 HTML | 留 |
| `gen_formal/`（`book`/`md_book`/`gen_excel`/`auto`/`__init__`/README） | 6 | 机读源 → 日文 Excel；`auto.py` 是 Stop 钩子 | 留 |
| `masking/`（`mask_demo`/`__init__`/example json） | 3 | 双向脱敏 | 留 |
| `ingest/`（6 模块 + `__main__` + `__init__`） | 8 | 旧案件取入（清单 → 扫描 → 秘密门 → 编号候选） | 留 |
| `legacy/`（`xlsx_text`/`selftest`/`__main__`/`__init__`） | 4 | 旧 Excel → 纯文本 | 留 |
| `rag/`（`loader`/`store`/`evaluate`/`__main__`/`__init__`） | 5 | 词法检索（纯标准库） | 留 |
| `registry.py` | 1 | 发号 / 阻塞 / 作废 | 留 |
| `impact.py` | 1 | 编号 → 上下游影响面 | 留 |
| `coach_brief.py` | 1 | 当前进度摘要（SessionStart 钩子） | 留 |
| `paths.py` | 1 | 路径解析共用件 | 留 |
| `__init__.py` | 1 | 包标记 | 留 |

> **一处卫生问题**：`tools/registry.py` 每次发号都会往 `docs/00_registry/_backup/` 写一个 `.bak`。
> 这些文件被提交进了 git（54 个，1.7MB）。**应当移出 git**，见 §7。

---

## 6. `docs/`（190）

### 6.1 `docs/00_plan/`（16）— 工程管理

| 文件 | 用途 | 判定 |
|---|---|---|
| `spec.md` | Trae 时代的规格书：6 条通用规则、约束、AC | 留 |
| `tasks.md`（438 行 48KB） | 16 个任务的计划 | **并** — 16 个任务**全部还是 `pending`**，实际早做完了。留着会让人以为没开工 |
| `review.md`（310 行） | 12 条受入基准 CP | 留（被 5 处机械检查引用） |
| `phase0-closure.md` | Phase 0 结项记录 | 留 |
| `coach/README.md` | 进度文件怎么读 | 留 |
| `coach/R60Login/case.yml` | 案件定义（模块/形态/团队） | 留 |
| `coach/R60Login/n01..n09.yml`（9） | **一个节点一个状态文件**——当前进度的真源 | 留 |
| `coach/R60Login/handoff.md` | 交接票（下一个会话先读这个） | 留 |

> `tasks.md` 的去向：要么把 16 个任务勾成 done 并加"已完成"抬头，要么并进 `phase0-closure.md`。
> **不改的代价**：任何新人打开都会以为项目没开始。

### 6.2 `docs/00_registry/`（58）→ 删 54

| 文件 | 用途 | 判定 |
|---|---|---|
| `ids.yml` | **全仓编号唯一发号口**（164 个：R2/Q0/F2/I77/D6/L10/E18/TC29/IT13/CR5/BUG2） | 留 |
| `traceability.yml` | 追踪矩阵（roots = R-101, R-201） | 留 |
| `glossary.yml` | 中日英三语术语表（50 词），正式 Excel 由它生成 | 留 |
| `ingest-manifest.yml` | 旧案件取入清单（`tools/ingest` 只读这个） | 留 |
| `_backup/ids.yml.*.bak` × **54** | `tools/registry.py` 每次发号自动写的备份 | **删**（1.7MB，可逆；git 历史里就有，且会自动再生成） |

> **这是全仓最划算的一刀**：54 个文件、1.7MB、零风险。
> 配套动作：`.gitignore` 加 `docs/00_registry/_backup/`，否则下次发号又会新增。

### 6.3 `docs/01_context/` ～ `docs/80_operation/`（22）

| 文件 | 用途 | 判定 |
|---|---|---|
| `01_context/case-profile-R60.yaml` | migration 的既有技术栈（**红线④的事实来源**） | 留 |
| `01_context/case-profile-sample-greenfield.yaml` | 新案件模板 | 留 |
| `01_context/R-101-R60Area.md` | R-101 的背景说明 | 留（※ 与 10_requirements 的 yaml 有重叠，可并） |
| `10_requirements/R-101-R60Area.yaml` | **见本**：需求书的机读形态 | 留 |
| `10_requirements/req-template.yaml` | 需求模板 | 留 |
| `20_basic_design/F-042-R60Area.yaml` | 见本：基本设计 | 留 |
| `20_basic_design/bd-template.yaml` | 模板 | 留 |
| `30_detail_design/D-043/L-014/L-015/E-001-E005`（4） | 见本：数据模型 / 检索 / 编辑 / 错误 | 留 |
| `30_detail_design/dd-template.yaml` | 模板 | 留 |
| `40_framework/framework-record.yaml` | 技术选型记录（人批准的栈写在这） | 留 |
| `50_unit_test/TC-001-TC-008-R60Area.yaml` | 见本：8 个用例（3/2/3） | 留 |
| `50_unit_test/tc-template.yaml` | 模板 | 留 |
| `60_integration_test/IT-001-R60Area-e2e.yaml` | 见本：e2e | 留 |
| `60_integration_test/integration-template.yaml` | 模板 | 留 |
| `70_release/release-template.md` | 发布模板 | 留 |
| `80_operation/impact-analysis-template.yaml` | 影响面模板 | 留 |
| `80_operation/impact-BUG-002.yaml` / `impact-CR-004.yaml` | 两个真实影响面 | 留 |
| `80_operation/operation-runbook.md` | 运行手册模板 | 留 |

> **这 22 个里，8 个是模板、14 个是 R-101 见本。**
> 问题：**见本与真实案件长在同一个目录里**，新人分不清哪个是"我该照着填的"、哪个是"别人填过的"。
> 建议加前缀（`_sample-R-101-...`）或移进 `docs/_samples/`（见 §11 问题 3）。

### 6.4 `docs/90_knowledge/`（94）

#### (a) 方法论与对应表（15）

| 文件 | 用途 | 判定 |
|---|---|---|
| `platform-map.md` | **7 层平台 × 实有资产**的唯一对应表 | 留（**核心**） |
| `ppt-deviation-register.md` | PPT 之外新增要素的登记簿（A-1〜A-31） | 留（**核心**） |
| `answer-engine.md` | 出处等级 E1〜E4 的唯一真源 | 留（**核心**） |
| `v1-platform-4layer.md` | 方案 v1 的 4 层 ↔ 落地篇 7 层 | 留 |
| `ai-dev-playbook.md` | 方法论 7 原则 | 留 |
| `dual-deliverable.md` | 机读源 ↔ 正式 Excel 的双份设计 | 留 |
| `reference-design-book.md` ※ | 参考设计书的体裁笔记 | 留 |
| `onboarding-checklist.md` | 新人 2 小时 Walkthrough | **并** → 与 `START_HERE` 重复，二者只留一 |
| `repo-inventory.md`（304 行） | 2026-10-26 的仓内清点 | **并** → 与本报告重复；本报告取代它，或它取代本报告 |
| `repo-inventory.zh.html` | 上面那本的中文视图 | **删**（同名 md 被并掉后就没有源了） |
| `requirement-review-capability.md` ※ | "要求书暗含论点读不出来"的能力设计 | 留（是 `requirement-interrogator` 的设计依据） |
| `ppt-coverage-assessment.md` ※ | PPT 各页实现到哪的评估（**已过期**：写着我方 0/8 承认，实际 8/8） | **并** → 结论已由本报告 §2 取代 |
| `ppt-example-walkthrough.md` | D1→D7 端到端实走记录 | 留（历史证据） |
| `agent-run-record.md` | 8 工程走破记录索引 | 留（历史证据） |
| `claude-code-migration-guide.md` | Trae → Claude Code 迁移记录 | 留（历史证据；一次性，但有用） |

#### (b) `internal/`（2）

`harmony-5gates.md`（5 道门的实绩）、`sds2-lessons.md`（幂等性/双重确认/客户指示优先）——
被规则 00 §13、规则 04 §9、规则 06 §7 引用。**留。**

#### (c) `legacy-r60/`（65）— R60 旧案件知识

| 组 | 文件 | 用途 | 判定 |
|---|---|---|---|
| 手引 10 本（`00-index`〜`09-ai-workflow`） | 10 | 源码地图 / 架构 / 惯例 / 共通部品 / DB / API / 追踪 / 差异 / AI 流程 | 留 |
| `chunks/*.jsonl` | 7 | **RAG 的语料**——`tools/rag/loader.py` 按目录读取 | 留 |
| `screens/` | 9 | 56 画面一览 + 8 张画面卡（`00-screen-index` 引用全部） | 留 |
| `modules/<7 模块>/*.yaml` | 36 | 每个模块的字段/API/逻辑/错误/测试/审查 | 留 |
| `module-selection.md` / `learning-plan-3modules.md` / `rag-usage.md` | 3 | 选型结论 / 教材计划 / RAG 用法 | 留 |

> **这 65 个是"附赠资产"**：只对有 R60 旧系统的案件有用。它们是 `legacy-r60-navigator` 和
> `virtual-requirement-author` 的数据源，删了这两个 skill 就空了。**建议整体移到独立的
> `knowledge/legacy-r60/`，让主目录变干净**（见 §11 问题 4）。

#### (d) `review_diff_assets/`（12）

| 组 | 文件 | 用途 | 判定 |
|---|---|---|---|
| `SOP-review-diff.md` | 1 | 审查前后差异的作业标准 | 留 |
| `_skeleton/review_comments.md` | 1 | **骨架自身踩过的坑（RC-SK-01〜03）**，规则 02/06 引用 | 留（**重要**） |
| `R60Area` `R60Code` `R60Item` × 3（`review_before/after README` + `review_comments`） | 9 | 三个真实模块的审查修正记录 | 留 |
| `R60Login/review_comments.md` | 1 | 演练模块的审查记录 | 留 |

---

## 7. `tutorial/R60Login/`（111）

**这是唯一的"跑通过一遍"的实证。** 结构本身没问题，问题在三个细节。

| 组 | 文件 | 用途 | 判定 |
|---|---|---|---|
| `README.md` + `.zh.html` | 2 | 685 行手顺书 | 留 |
| 节点 1（16） | 需求书、结构化表（md+yaml）、**回答接收核对 + 确认事项一览（都是 02_）**、确认请求书 AB（md+pdf）、技术课题 C（md+pdf）、承认版 | 留 |
| 节点 2（14） | 模板、输入、AI 产出、审查中/审查结果（都是 02_）、组内意见、改修版、承认版 | 留 |
| 节点 3（11） | 同上；**`03_` 缺号** | 留 |
| 节点 4（5） | 模板、AI 产出、承认版 | 留 |
| 节点 5（5 文档 + 38 代码） | `05_承認版_制造记录`、`06_設計との差異`、`backend/`（16 py+test）、`frontend/`（16 ts/vue/config） | 留，**删 `.coverage`** |
| 节点 6（5） | 用例集、承认版、**单测执行结果**、**覆盖率报告** | 留 |
| 节点 7（7） | 结合测试规格、承认版、`verification.md`（不做 A/B 的案件的记录处） | 留 |
| 节点 8（5） | 运用计划、承认版 | 留 |
| `.coverage` | 1 | pytest 跑完留下的二进制 | **删**（生成物，可逆） |

**三个细节问题**：

1. **节点内编号不齐**：节点 1 有两个 `02_`；节点 2 有两个 `01_`、两个 `02_`；节点 3 没有 `03_`；节点 4〜8 只有 `00/01/05`。
   每次都要问"03 在哪"。**改法**：`02a_` / `02b_` 两位编号，或统一成 `10_输入 / 20_AI产出 / 30_审查 / 40_承认`。
   **代价**：要同时改 9 个作业票、`nNN.yml` 的 artifacts、`使用手册` 的路径。**引用面很广，事故风险高。**
2. **`节点5_制造` 里有真代码（38 个文件）**，而 `reports/unit/R60Login/` 是它的运行结果。
   源码与结果分在两处，是对的。但 `.coverage` 这种二进制混进来了。
3. **38 个 `.zh.html` 里有 7 个已经过期**（md 比 html 新）：`节点3/05`、`节点5/05`、`节点6/05`、`节点7/05`、`节点8/01`、`节点8/05`、`drill/comparison`。
   **不是删，是重新生成。** 而且最好加一道检查：md 比 html 新就报错。

---

## 8. `reports/`（311）→ 删 266

| 组 | 文件 | 体积 | 用途 | 判定 |
|---|---|---|---|---|
| `module-survey/` | **234** | 2.9 MB | 13 个旧模块的设计书/测试书**原文抽取**＋选型打分 | **删**（结论已存 `legacy-r60/module-selection.md`）**需你点头** |
| `legacy-raw/` | 29 | 0.3 MB | R60Area 的设计书 + 单测书原文抽取 | **删**（`tools/legacy` 可再抽取）**需你点头** |
| `ingest/JET-R60/` | 7 | 0.35 MB | `tools/ingest` 的试跑结果（清单/证据/编号候选） | **删**（试跑过，可重跑）**需你点头** |
| `drill/R60Login/` | 16 | 0.36 MB | **训练测量记录**：README（7 个坑）、comparison（AI vs 人 归因）、answer-key、interrogation、requirement-defects、provenance、freeze | **留**（唯一证明"框架有用"的实证） |
| `unit/R60Login/` | 6 | 0.13 MB | 单测运行输出 + 覆盖率 json | 留 |
| `rag/eval-2026-10-19.json` | 1 | 0.08 MB | RAG 评测结果快照 | 留 |
| `survey/prj01-logistics-1026-inventory.md` + `.zh.html` | 2 | 0.06 MB | **另一个仓库**（`D:\AI_work_dev2\prj01-logistics`）的清点报告 | **待定** — 是外部参考，不属于本仓 |
| `audit/` | 4 | 0.1 MB | 本报告 + 规格书对照调查报告 + 一个 156 字节的门禁输出 + 上一轮阻塞项裁定案 | 留 |
| `AC-selfcheck.md` / `DELIVERY_MEMO.md` / `PHASE15-EXIT.md` | 3 | 0.03 MB | Phase 1 验收 / 交付备忘 / 出口记录 | 留（被 11 / 5 / 1 处引用） |
| `trace_R101.json` / `gate6_report.json` / `gen_formal_columns_R101.json` / `trace_aux.json` / `seal_before.json` | 5 | 0.03 MB | 过去的门禁原始输出 | 留（被 10 / 7 / 7 / 1 / 1 处引用） |
| `trace_w1.json` / `trace_tmp.json` / `trace_R60Plc.json` / `trace_node1_R60Login.json` | 4 | 0.02 MB | 临时/调试输出 | **删**（**0 处引用**，已实测） |

> **`reports/` 现在的乱，是"含义混杂"**：门禁证据、训练记录、一次性调查、别的仓库的报告、
> 临时 json 全在一个目录下。§11 问题 6 给了一个重组成 5 个子目录的方案。

---

## 9. `eval/`

| 文件 | 用途 | 判定 |
|---|---|---|
| `eval/gold-qa.yaml` | RAG 评测的 80 题金标（`tools/rag/evaluate.py` 读它） | 留 |

---

## 10. 可执行的删除清单

### 10.1 零风险（可逆，建议今天就做）

| # | 删什么 | 文件 | 体积 | 证据 |
|---|---|---|---|---|
| 1 | `docs/00_registry/_backup/*.bak` | 54 | 1.7 MB | 由 `registry.py` 自动生成；git 历史已有；删后发号会再生成（故须同时改 `.gitignore`） |
| 2 | `tutorial/R60Login/节点5_制造/backend/.coverage` | 1 | ~0.05 MB | pytest 生成物 |
| 3 | `reports/trace_w1.json` `trace_tmp.json` `trace_R60Plc.json` `trace_node1_R60Login.json` | 4 | 0.02 MB | 引用数实测 = 0 |
| **小计** | | **59** | **≈1.8 MB** | |

配套两行 `.gitignore`：

```text
docs/00_registry/_backup/
tutorial/**/backend/.coverage
```

### 10.2 需要你点头（先备份或先打 tag）

| # | 删什么 | 文件 | 体积 | 不可逆的部分 |
|---|---|---|---|---|
| 4 | `reports/module-survey/` | 234 | 2.9 MB | 要重跑 `tools/legacy` 对旧 Excel 再抽取才能得到 |
| 5 | `reports/legacy-raw/` | 29 | 0.3 MB | 同上 |
| 6 | `reports/ingest/JET-R60/` | 7 | 0.35 MB | 重跑 `tools/ingest` 即可 |
| **小计** | | **270** | **3.55 MB** | 结论性内容已存在 `legacy-r60/` 与 `module-selection.md` |

### 10.3 不删，但要重新生成

7 个过期的 `.zh.html`（清单见 §7）。
另外 `reports/audit/R60Login/gate-2026-10-27.txt` 的 `total_ids=162`，当前是 164 —— **是一条过时证据**，
留着会误导（说明当时和现在的编号数不同），建议删或改名加日期戳。

---

## 11. 需要你拍板的 6 件事

> 每一件都是"我给了建议，但改起来引面广或删了不可逆"。**其余全部事项我自己处理。**

### 问题 1：入口说明文 5 本，要合成几本？

现在：`CLAUDE.md`（AI 读）／`START_HERE.md`（新人）／`使用手册.md`（全功能）／`AGENTS.md`（角色）／规格书（目标）。

**我的建议**：留 **3 本**。`CLAUDE.md`（AI 的约束，不动）、`使用手册.md`（唯一的人读本，吸收 `START_HERE` 与 `AGENTS`）、规格书（目标态）。
`START_HERE.md` 缩成 `使用手册` 的前一页（保留文件名，内容只剩"打开这一本、然后说这句话"）。

**代价**：要改 `CLAUDE.md §0`（它写着"不熟悉的人从 START_HERE 开始"）和 3 处交叉引用。**改动量约 1 小时。**

### 问题 2：一次性调查产物 270 个文件、3.5MB，删不删？

这三批是旧系统普查的**原始抽取**，结论已经写进 `legacy-r60/module-selection.md` 和 7 个模块 YAML。

- **删**：仓库从 14MB 降到 10.5MB，`reports/` 从 311 文件降到 41 个。
- **不删**：以后要复查"当时为什么选这三个模块做教材"，原始抽取还在。

**我的建议**：**先打 tag 再删**（`git tag keep/module-survey-2026-10-28`），这样随时能捞回来。**这是可逆的。**

### 问题 3：R-101 见本要不要和真实案件分开？

`docs/10_requirements/` 等 8 个目录里，**模板和见本混放**。新人分不清哪个该照着填。

**我的建议**：只改名，不移动 —— 见本加前缀 `_sample-`（如 `_sample-R-101-R60Area.yaml`）。
**代价**：`traceability.yml`、`review.md`、`tasks.md`、`ids.yml` 的 `used_by` 都要跟着改（约 30 处正则替换）。
**风险**：中途漏改会导致门禁红。

### 问题 4：R60 专属资产（65 个知识文件 + 2 个 skill + 1 个 agent + 演练）是"附赠"还是"核心"？

这决定了它们该留在主目录，还是整体搬进 `knowledge/legacy-r60/`（给将来交付别的客户时能整块剥离）。

**我的建议**：**当成附赠品整体剥离**。主目录只留"任何客户都用得上"的东西。理由：你要做的是一个**给外包公司用的框架**，R60 是第一个客户，不是框架本身。

### 问题 5：`tasks.md` 16 个任务全是 `pending`，怎么处理？

实际全做完了，但文件写着没开始。任何新人打开都会得到错误印象。

**我的建议**：改成"已完成记录"，抬头写清"本表记录的是骨架自身的构建任务（2026-10 已完成）"。

### 问题 6：`reports/` 要不要按含义重分子目录？

现在是 311 个文件混装 5 种东西。**我的建议**：

```
reports/
├─ gate/     门禁原始输出（trace_*.json、gate6、seal）
├─ drill/    训练测量（已在，不动）
├─ audit/    调查报告（已在）
├─ legacy/   旧系统调查（module-survey + legacy-raw + ingest 合并）
├─ run/      跑出来的结果（unit、rag 评测）
└─ memo/     阶段记录（AC-selfcheck、DELIVERY_MEMO、PHASE15-EXIT）
```

**代价**：`spec.md`/`tasks.md`/`review.md` 里有 30+ 处路径引用要跟着改。

---

## 12. 判定依据的复算方法

```text
1. 文件全集       git -c core.quotepath=false ls-files            -> 701
2. 入向引用图     扫全仓 token，按 basename 与相对路径双向匹配      -> 见下
3. 体积分类       按类别汇总                                      -> §1
4. 过期视图       md -nt html 比较 38 个 .zh.html                 -> 7 个过期
5. 引用数实测     grep -rl <name> 排除自身                        -> §10 的 4 个 0 引用
```

**引用图的两个已知盲点**（所以不能只看数字判定死文件）：

- **Python 的 `from .x import` 不带 `.py`**，因此 `tools/legacy/xlsx_text.py` 显示 0 引用，
  实际被 `__main__.py` 和 `selftest.py` 导入。
- **按目录整批加载的文件**（`tools/rag/loader.py` 读 `chunks/*.jsonl`）不出现文件名，同样显示 0。

**agent 的引用数 0 是正常的**（靠 description 自动匹配），不可作为死文件判据。

### 引用数为 0 但确认「在用」的文件（避免误删）

```text
.claude/agents/*.md（8 个）                        -> description 自动匹配
docs/90_knowledge/legacy-r60/chunks/*.jsonl（7）    -> tools/rag/loader.py 按目录读取
tools/legacy/xlsx_text.py                          -> from .xlsx_text import
tools/legacy/selftest.py / tools/ingest/selftest.py -> from .selftest import
docs/90_knowledge/legacy-r60/screens/R60Maker.md   -> 8 张画面卡之一；00-screen-index.md 以
                                                      模块名列示（不写路径），故路径引用数 0
reports/drill 与 tutorial 的 .zh.html（多数）       -> 由同名 .md 生成，生成器不回写引用
```

> 这一栏是本报告最该被复核的地方：**引用数只能证明"没被路径提到"，不能证明"没人用"。**

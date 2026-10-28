# 规格书 × 仓库 实施现状审计

- 审计对象：`AI全链路软件工程平台_实施规格书.md`（1273 行，全文通读）
- 审计范围：`D:\AI_work_dev` 全部文件 + `D:\AI_platform\kb-platform`（全文通读）
- 审计日期：2026-10-27
- 审计方式：机器可查的一律跑命令取证（附录 A 存原样输出），只有"该不该"类判断留给人

> 本文件是**审计记录**，不是机读源，不参与 `trace_check`（`SCAN_BASES = docs/.claude/tutorial`，
> `reports/` 不在扫描范围）。它不定义任何业务字段（NFR-1 不受影响）。

---

## 0. 结论

**一句话**：骨架的"8 工程流程 + 门禁 + 追溯"这一层是真做完了、也真跑通了（R60Login 8/8 承认）；
缺的是**平台层的三个部件**（模型网关 / RAG / 评测治理）、**任意节点入口**、以及**去 R60Login 化**。

### 0.1 九条硬事实（都有取证，见附录 A）

| # | 事实 | 影响 |
|---|---|---|
| 1 | `trace_check` 的扫描根只有 `docs` / `.claude` / `tutorial`（`tools/trace_check/__init__.py:285`） | 规则 `01-security-redlines.md` 声称扫 `tools/**`、`reports/**`、根目录主要 md —— **实际不扫**。这是"扫描范围被悄悄收窄"，违反规则 06 §3 |
| 2 | ~~git 仓库存在，**0 个 commit**~~ → **已修（2026-10-28）**：首次提交 `26f23e9`，700 文件入库；`docs/ tools/ reports/` 已放开 | 红线⑥此后有对象可执行。遗留：`.github/` 与 4 份根目录辅助 md 仍在忽略外 |
| 3 | 工具层**没有任何一次程序化大模型调用**（`grep -rniE "anthropic\|openai\|chat/completions" tools/` → 0 行） | "模型网关"今天没有调用方。网关的真实用途是 ①RAG 的 embedding/rerank ②换模型供应商的移植缝 |
| 4 | `tools/rag` 是**纯标准库的词法检索**（hash n-gram + SQLite FTS，`tools/rag/store.py`） | 与规格书 §11.2 的"知识库（RAG）"同名但不是一回事；可作**默认 provider**，公司提供后换 adapter |
| 5 | kb-platform 的本体元数据是 `doc_id/scope/title/doc_type/version/status/conf_level/updated_at`（`kbkit/pipeline.py:16`） | 与骨架的 7 字段（`id/type/req_ids/status/sensitivity/owner/version`）**不兼容**，不能直接 ingest，必须过一层映射 |
| 6 | coach 不能从任意节点起跑：当前节点恒为"依赖已满足且未批准的**最小号**"，前置未批准即硬阻断（`SKILL.md:53`、`SKILL.md:183-184`）；`case.yml` 无 `start_node` 字段 | 用户要的"客户直接给基本设计书 → 从节点 3 开始"**目前没有机制**（详见 §8） |
| 7 | **进度声明三套并存且全错**：`phase0-closure.md:35-37` 写 0/8、`agent-run-record.md:84` 写 1/8、`ppt-coverage-assessment.md:132` 写"一次都没跑" | 实际 n01–n08 **全部 approved**（SE-001）。任何人读这三份都会得到相反印象 |
| 8 | **n09 用了未登记的编号**：`n09.yml` 的 `closed_changes` 含 `CR-201..CR-205`，而 `ids.yml` 只有 `CR-001..005` | 这是**野号**（红线①），且 `SKILL.md:318` 明文要求 `case_ref` 必须是台账已发号。门禁没拦住，因为 gate1 不扫 `docs/00_plan/` |
| 9 | **n04 的承认版在撒谎**：`tutorial/R60Login/节点4_框架构筑/05_承認版_框架构筑记录.md:5,8` 标 `status: baselined` / `v1.0.1`，但 `closeout.md:38-40` 说 **v1.0.1 从未被承认**（承认的是 v1.0.0，依赖表 17 vs package.json 10 未裁定） | 文件在声称一个没签过的基线 → 红线③的证迹被污染 |

### 0.2 实施度总账

| 层（规格书 §11.1 的 7 层） | 对应资产 | 状态 |
|---|---|---|
| 利用层 | `START_HERE.md` / `使用手册.md` / coach 卡片 | ✅ 可用（但入口文件重叠，见 §1.3） |
| 編成層 | `trans-cosmos-ai-lifecycle-coach` skill + 9 个 node agent | ✅ 8 工程全通，已跑完一遍 |
| 能力層 | 5 skill / 14 agent / `tools/*` | 🟡 设计→制造链可用；**网关、RAG、评测**三项是接口级 |
| 知識層 | `docs/90_knowledge/**` + `tools/rag` | 🟡 有内容、有词法检索；无向量、无公司知识库 |
| データ・コンテキスト層 | `docs/00_plan/coach/<module>/` + `ids.yml` | ✅（"コンテキストハブ"用状态文件+路径模拟，无独立组件） |
| 統制・ガバナンス層 | `tools/trace_check` 6 门 + `secret-auditor` + `spec-reviewer` | 🟡 门禁 6 道可用；**KPI 计量 0**；无鉴权 |
| 基盤層 | （无） | ❌ 依赖 Claude Code 本身；闭域网内无替代路径 |

**成熟度**：`docs/90_knowledge/platform-map.md:§0` 自评 L3。本次复核**同意 L3**，
但 L3 的"3"是**流程层**的 3；平台层（7 层里的后 3 层）实际在 L1～L2。

---

## 1. 这些文件是什么关系

### 1.1 五层：谁说的算 / 谁干活 / 谁留证

```
① 认知源（为什么这么做）      AI全链路软件工程平台_实施规格书.md  ← 唯一总纲
                              docs/90_knowledge/v1-platform-4layer.md（中文PPT的对应表）
                              docs/90_knowledge/ppt-deviation-register.md（对PPT的增补登记簿）
                                    │
② 规则（必须怎么做）          CLAUDE.md（常时约束·7红线·禁止5条·commit格式）
                              .claude/rules/00~06（7 份，起自动加载）
                                    │
③ 执行（谁去做）              .claude/skills/（5 个：1 个主入口 + 4 个专项）
                              .claude/agents/（14 个：9 执行 + 5 验证）
                              tools/（12 个模块：门禁/发号/影响面/生成/摄取/检索）
                                    │
④ 产物（做出什么）            docs/10~70_*/（实案件，机读源 .yaml/.md）
                              tutorial/<案>/节点N_*/（演练，8 节完整样例）
                                    │
⑤ 证据（做没做到）            docs/00_plan/coach/<module>/（进度状态 10 文件）
                              reports/（门禁原始输出、训练对比、审计）
                              docs/90_knowledge/repo-inventory.md（仓库总账）
```

**一句话记法**：①说**为什么**，②说**不许怎样**，③是**手脚**，④是**东西**，⑤是**证据**。
出问题时的排查顺序是 ⑤→④→③→②（先看证据，再怀疑产物，再怀疑执行，最后才怪规则）。

### 1.2 全量文件表（作用 + 现状）

#### 根目录

| 文件 | 作用 | 现状 |
|---|---|---|
| `AI全链路软件工程平台_实施规格书.md` | 两份 PPT 合成的实施总纲（20 节 + 附录） | ✅ 完整；**它是"目标态"，不是"现状说明"** |
| `CLAUDE.md` | 常时约束：工具构成、7 红线、禁止 5 条、commit 格式、attribution | ✅ 有效；⚠ §0 表格里"5 个 skills"等描述与实际一致 |
| `AGENTS.md` | 人侧角色定义（8 内部角色 + 日方），每角色启动 prompt | 🟡 可读；**Claude Code 不自动加载**（有 CLAUDE.md 时），只是人看的 |
| `START_HERE.md` | 新人唯一入口页（怎么用） | ✅ 最好的一份；⚠ 与 `使用手册.md` 大面积重叠 |
| `使用手册.md` + `.zh.html` | 1053 行完整手册 | 🟡 内容更细（含 §已知缺口），但与 START_HERE 口径需同步维护 |
| `ROADMAP_3PHASE.md` | 骨架自身三期计划（16/12/8 条） | 🟡 与规格书 §14 的 3 阶段**不是同一套划分**，同名不同物，容易误读 |
| `CONTRIBUTING.md` | 协作约定 | ✅ 在 gitignore 内（opt-in） |
| `.gitignore` | 默认忽略 `docs/ tools/ reports/ .github/`，`.claude/` 入库 | ⚠ 见事实 #2：这使"成果物入库"实际未发生 |
| `.github/workflows/ai-gate.yml` | CI 门禁 | ❌ **占位**：`\|\| echo "Phase1 local run only"`，失败也被吞掉 |

#### `.claude/`

| 资产 | 数量 | 作用 | 现状 |
|---|---|---|---|
| `rules/00-project-global.md` | 1 | 13 条全局硬约束（加密方式、NLS、snake/camel、机读源唯一、媒体二重化、PDF 化） | ✅ 有效，且是**最常被引用的真源** |
| `rules/01-security-redlines.md` | 1 | L3 禁止外投 13 条 + gitleaks 等价 keyword 表 | ✅ 定义完整；⚠ 声称的扫描范围与实现不符（事实 #1） |
| `rules/02-requirements.md` | 1 | 8 工程表、R/Q-ID SOP、front-matter 7 字段、状态机、A/B/C 字母表、上流位移检查 | ✅ **本仓质量最高的一份规则** |
| `rules/03-design-coding.md` | 1 | BaseCamelModel 4 行、R60Common 映射 13 函数、snake/camel 分区、SQL 白名单 | 🟡 §3 已限定 migration；但 `ALLOWED_SORT_FIELDS={CMP_CD,JIG_CD,ARA_CD}` 仍是 R60Area 专用值 |
| `rules/04-testing.md` | 1 | TC 3/2/3、design_ids、双方向闭ループ、观点 3 技法、A/B 报告位置 | ✅ 完整；⚠ `doc/03_AI/AB_Reports/` 是**死路径**（仓库只有 `docs/`） |
| `rules/05-commit-messages.md` | 1 | 7 种 commit + Trace/AI/Review 三段 + Tag 命名 | ✅ 完整；⚠ 与 CLAUDE.md §3 内容重复（双写，NFR-1 风险） |
| `rules/06-knowledge-flywheel.md` | 1 | 踩坑→规则化→加检查 5 段 + 5 问 + "扫描范围只能扩不能缩" | 🟡 规则有，**自动化没有**（`§6` 已诚实标注） |
| `skills/trans-cosmos-ai-lifecycle-coach` | 1 | 主入口：定位置、出卡片、派 agent、记承认、写交接 | ✅ 完整可跑；⚠ 硬编码 `tutorial/R60Login`（见 §4.1） |
| `skills/code-from-design-trans-cosmos-ai` | 1 | 设计→制造 4 步流水线 | ⚠ **只接受 R-101 / R60Area**（`SKILL.md:41,49`），换题材即拒 |
| `skills/legacy-r60-navigator` | 1 | 历史案件只读导航 | ✅ R60 专用（设计如此）；`§6` 给了换案件复用流程 |
| `skills/requirement-interrogator` | 1 | 要求书审査：177 件 QA 票提炼的 51 观点 | ✅ **复用性最好**，无案件名 |
| `skills/virtual-requirement-author` | 1 | 节点 0：从既有资产倒推节点 1 的输入并冻结 | ✅ migration 专用，明确"8 工程之外" |
| `agents/trans-cosmos-ai-node1..8` | 8 | 各工程产出体（独立上下文，只回报 15 行） | ✅ 契约统一（`node-worker-contract.md`）；⚠ node3/node5 口径与作业票冲突（§4.4） |
| `agents/trans-cosmos-ai-node9-change` | 1 | 变更·指摘环的影响面草案 | ✅ 已跑过一例（BUG-002） |
| `agents/spec-reviewer` `secret-auditor` `deliverable-reviewer` `drill-comparator` `legacy-module-surveyor` | 5 | 验证系 | ✅ 可用；`drill-comparator` 明确不做合格判定（红线③） |
| `settings.json` | 1 | 6 条 deny + 2 个 hook（SessionStart 播报 / Stop 自动重画 Excel） | ✅ **没有一条自动批准**；设计正确 |

#### `tools/`

| 模块 | 作用 | 现状 |
|---|---|---|
| `trace_check/` | 6 道门：野号 / 双方向追溯 / front-matter 7 字段 / 生成物一致 / snake-camel 分区 / 机密 | ✅ 6 门可跑（本次实测全 PASS） |
| `registry.py` | 发号 / 状态 / 阻塞 / 失效标记（`alloc` `set-status` `answer` `blockers` `mark-stale`） | ✅ 可用 |
| `coach_brief.py` | SessionStart 播报（读状态文件算当前位置） | ✅ 可用，异常一律 exit 0 |
| `impact.py` | 影响面反查 | ✅ 可用（BUG-002 的 impact 报告实存） |
| `gen_view/` | 机读源 → 中文 `.zh.html` 阅读视图 | ✅ 可用（`--self-test`） |
| `gen_formal/` | 机读源 → 日文正式 Excel | 🟡 **Phase1 只有 dry-run**；`book` 拒绝输出到 `docs/`；`gen_excel` 硬编码 R-101 |
| `masking/` | L3 脱敏占位 | 🟡 用的是 `[[KEY]]` 风格，与规则的 `PWD_1/IP_1` 占位体系**不一致** |
| `ingest/` | 外部材料摄取（仅 migration） | 🟡 `id-apply` 明确"不写"，只出建议 |
| `legacy/` | 旧 xlsx 抽取 | 🟡 硬编码 `D:/AI_work` |
| `rag/` | 本地词法检索 + 评测 + 上下文打包 | 🟡 见事实 #4 |

#### `docs/`

| 目录 | 作用 | 现状 |
|---|---|---|
| `00_registry/ids.yml` | **唯一发号口**（**164 条**：R2 / Q0 / F2 / I77 / D6 / L10 / E18 / TC29 / **IT13** / CR5 / BUG2；baselined 115、open 48、void 1） | ✅；⚠ `repo-inventory.md:145` 仍写 124 且漏 `IT`，`review.md:108` 仍写 79 |
| `00_plan/` | spec / tasks / review + `coach/<module>/` 状态 10 文件 | ✅；⚠ `tasks.md` 全为未完成态（陈旧） |
| `01_context/` | 案件档案（`case-profile-*.yaml`） | 🟡 只有 R60 一份 |
| `10~70_*` | 按工程序号排的实案件产物 | 🟡 R101 一条线做完了，其余空间 |
| `80_operation/` | 变更·影响面 | ✅ impact-BUG-002 实存 |
| `90_knowledge/` | 18 份知识文档 | 🟡 内容多但**彼此有陈旧冲突**（见 §4.4） |

#### `tutorial/R60Login/`

| 位置 | 作用 | 现状 |
|---|---|---|
| `节点1_需求 … 节点8_发布运维` | 8 节完整样例（输入模板 + 初稿 + 承认版 + 中文视图） | ✅ 全套在；这是**唯一一份"从头到尾长什么样"的实物** |
| `README.md` + `.zh.html` | 演练手册 | ✅ |

### 1.3 四份入口文件的重叠（先说结论：新人只开 `START_HERE.md`）

| 文件 | 写给谁 | 与其它三份的关系 |
|---|---|---|
| `START_HERE.md` | **第一次上手的人** | 唯一入口。286 行，三句话能记住 |
| `使用手册.md` | 想查细节的人 | START_HERE 的加长版，**有重叠**（`repo-inventory.md:§12` 已记为问题） |
| `AGENTS.md` | 定角色/分工的人 | 与 CLAUDE.md 的"工具构成"重叠，但读者不同（人 vs AI） |
| `CLAUDE.md` | AI 与治理 | **不是给人看的入门材料**，是常时约束 |

**建议**（不在本次执行）：`使用手册.md` 降为"附录"，只留 START_HERE 一个入口；或把 `使用手册.md`
最后一节"已知缺口"移进 `repo-inventory.md`，避免两份都在维护同一份缺口清单。

### 1.4 真正"活"的链条（谁调用谁）

```
用户
 └─▶ trans-cosmos-ai-lifecycle-coach（唯一推进器）
       ├─▶ tools/coach_brief          定位置（也由 SessionStart hook 自动跑）
       ├─▶ 9 × trans-cosmos-ai-nodeN  产出一个节点的初稿（独立上下文）
       ├─▶ 5 × 验证 agent             审 / 查机密 / 做视图 / 训练对比
       ├─▶ requirement-interrogator   节点1 必过（Skill，不是 agent ← 现文档写错，见 §4.4）
       ├─▶ virtual-requirement-author 节点1 无输入书时（节点 0）
       ├─▶ code-from-design           仅实案件/migration 的节点5
       └─▶ tools/{registry,impact,trace_check,gen_view,gen_formal}
```

---

## 2. 规格书逐节实施清单

图例：✅ 完全实现 ／ 🟡 部分实现 ／ ❌ 未实现 ／ — 论述性内容（无"实现"一说）

| 规格书节 | 内容 | 对应资产 | 实施度 | 怎么用 / 缺什么 |
|---|---|---|---|---|
| §1 | 现状与痛点 | — | — | 论述。§1.2 的四大痛点在 `START_HERE` 有中文解释 |
| §2 | 三大认知突破 | — | — | 论述。已落为 `rules/00 §11`（机读源唯一）、`answer-engine.md`（答案在资产里） |
| §3 | 四个思维升级 | — | — | 论述 |
| §4.1 | 8 工程全链路架构 | `rules/02 §2` + coach 8 节点 + 9 agent | ✅ | `/trans-cosmos-ai-lifecycle-coach` 走 |
| §4.2 | 各阶段 AI 典型生成物 | `tutorial/R60Login/节点1~8` | ✅ | 看实物即可 |
| §4.3 | 三层支撑体系（纵向贯通） | 上下文枢纽=coach 状态+上游产物路径；ID 贯穿=`ids.yml`；知识沉淀=`90_knowledge` | 🟡 | 三层里"上下文枢纽"是**用约定模拟的**，没有独立组件/接口 |
| §4.4 | 两种划分视角（8 工程 / 7 章） | `rules/02 §2` 的注释 | ✅ | 已把"7 工程"的由来写清，防混淆 |
| §5.1–5.8 | 8 个工程详细作业方式 | `.claude/skills/.../nodes/n01..n08.md`（作业票） | ✅ | 每节点 4–5 步，卡片的正文来自这里 |
| §6 | 端到端走查 D1–D7 | `tutorial/R60Login` 实际走了一遍 | 🟡 | 走过，但 D1–D7 的编号**没有落到任何产物**，只是叙事 |
| §7 | RACI 人机分工 | `rules/02 §8` + `AGENTS.md` | ✅ | 人=A/I，AI=R/C，已机械化为 `approved_by` 必填人 ID |
| §8 | 团队角色重构 | `AGENTS.md` | 🟡 | 角色写了，但 `case.yml.team` 只有 `["SE-001"]` 一人，多人协作未验证 |
| §8.1 | 四役割パターン（spec-engineer/developer/rule-maker/scenario-walkthrough） | 无 | ❌ | **未落地到任何资产**。要补：在 `AGENTS.md` 增一节，或在 coach 卡片里标"本步是哪个役割" |
| §9.1 | 全链路成果物マップ | `docs/10~70_*` 目录 + `tutorial/节点N` | ✅ | 目录序号 = 工程序号 |
| §9.2 | 成果物六大原则 | `CLAUDE.md` + `rules/02 §5` + `trace_check` gate1/3/5 | ✅ | **这是全仓做得最实的一块** |
| §9.3 | 二重化架构（机读源 + 人向视图） | `.md`(日) + `.zh.html`(中)；`gen_view`；`gen_formal` | 🟡 | 视图链路 ✅；**日文正式 Excel 只到 dry-run**；Word 无；客户模板回流 ❌ |
| §9.4/9.5/9.6 | 基本/详细/测试仕様书结构示例 | `tutorial/节点2/3/6` 承认版 | ✅ | 结构示例即实物 |
| §10.1 | コンテキストハブ中心辐射 | coach 状态目录 + 上游产物绝对路径 | 🟡 | 有"枢纽"的效果（下游只读上游承认版），无组件、无 API |
| §10.2 | 六大连携机制 | ID 贯穿✅ / 追溯✅ / 门禁✅ / 变更环✅ / 知识沉淀🟡 / 上下文传递🟡 | 🟡 | 缺的是"知识沉淀"的自动化回流 |
| §10.2.1 | **差分検証パターン** | `drill-comparator`（事后 A/B，训练用） | 🟡 | 只用于**训练对比**；日常开发里"改前 vs 改后差分"没有工具 |
| §10.3 | 要件 ID 贯穿全链路 | `ids.yml` + `trace_check` | ✅ | `--strict` 全 PASS（本次实测） |
| §10.4 | 平台能力持続進化（大飞轮） | `rules/06`（5 段 + 5 问） | 🟡 | 规则在，**无人自动建单、无自动加检查、无周次启动**（`rules/06 §6` 已诚实标注） |
| §11.1 | 7 层平台架构 | `platform-map.md` | 🟡 | 映射表在；实际只实现 4 层（见 §0.2） |
| §11.1.1 | 4 层 ↔ 7 层对应 | `platform-map.md` | ✅ | 有图有表 |
| §11.2 | 六大核心组件 | 见下 | 🟡 | 逐项见 §2.1 |
| §11.3 | 4 层知识モデル（入口/规则/执行/验证） | `platform-map.md §` | 🟡 | 概念清晰；"验证层"只有 6 门，没有 KPI |
| §11.4 | Prompt 模板库 | 无独立资产（散在 skill/agent 的 md 里） | ❌ | 需要抽成可版本化、可 A/B 的模板目录，否则"模板"无法单独演进 |
| §12 | 技术选型指南 | `rules/03` + 节点4 | 🟡 | 选型放在节点4 由人批准（红线④）；但 node3 agent 又把 Oracle 写死，逻辑倒置 |
| §13 | KPI 六大维度 | 无 | ❌ | `ROADMAP_3PHASE.md` 里 6 个公式全是"1 个月后更新"的占位 |
| §14.2–14.4 | 落地三阶段 | `ROADMAP_3PHASE.md`（另一套口径） | 🟡 | 同名不同物，建议在 ROADMAP 开头注明与 §14 的对应关系 |
| §14.1 | 三种导入模型（轻量/标准/全活用） | 无 | ❌ | 未落地。它决定"客户只给设计书时用哪一档"，与 §8 的任意入口强相关 |
| §15 | 落地优先级 | — | — | 论述 |
| §16 | 案例（Kavak/Harmony/JET） | `docs/90_knowledge/internal/*` | — | 已提炼为规则（`rules/04 §9`、`rules/06`、`rules/00 §13`） |
| §17 | 新旧对比 | — | — | 论述 |
| §18 | 实施 Checklist | 部分可在 `reports/AC-selfcheck.md` 看到 | 🟡 | 没有逐条勾选记录 |
| §19 | 目录结构参考 | `docs/10~70_*` | ✅ | 序号一致（规格书写 `01_requirements`，实现是 `10_requirements`，无碍） |
| §20 | 总结 | — | — | 论述 |
| 附录A | 5 步快速开始 | `START_HERE.md` | ✅ | 三句话可走 |

### 2.1 §11.2 六大核心组件 逐项

| 组件 | 规格书要求 | 现状 | 缺什么 |
|---|---|---|---|
| モデルゲートウェイ | 统一模型接入、按用途路由、成本/限流/审计 | ❌ **完全没有** | 见 §5（本次给接口方案） |
| 工程別 Agent | 8 个工程各一个执行体 | ✅ 9 个（含 n09 旁路环） | 去 R60 化（§4.1） |
| コンテキストハブ | 统一的上下文装配与分发 | 🟡 用"状态文件 + 上游产物路径"模拟 | 无接口、无版本、无裁剪策略（token 预算） |
| ナレッジベース（RAG） | 向量检索 + 引用 | 🟡 `tools/rag` 词法版 | 见 §6（本次给接口方案） |
| 評価・ガバナンス | 质量度量、KPI、成熟度评估 | 🟡 6 门 + `--strict`；**KPI 0** | 见 §4.2 P1 |
| セキュリティ | 机密分级、脱敏、外投管控 | 🟡 gate6 + masking + 6 条 deny | 无鉴权、无审计日志；masking 占位风格不一致 |

---

## 3. 已实现：怎么用

### 3.1 走一遍 8 工程（唯一入口）

```
/trans-cosmos-ai-lifecycle-coach
```

它做四件事：**读盘定位 → 出一张卡 → 派 agent 出初稿 → 记你的承认**。
状态在 `docs/00_plan/coach/<module>/{case.yml,n01..n09.yml}`，承认必须写人 ID（`SE-001`）。
一次只出一张卡；一个节点承认即会话边界（写 `handoff.md` 后结束）。

**当前实况**：R60Login 8/8 已由 `SE-001` 承认；`n09` 有 1 件未闭合变更 `BUG-002`
（`state: fixing`, `reenter_node: 3`），影响面报告在 `docs/80_operation/impact-BUG-002.yaml`。

**但"承认"不等于"验证过了"**（`reports/drill/R60Login/closeout.md:44-48` 自己写明）：
- 节点 7 的 **IT-201..IT-212 共 12 本，一本都没执行**；
- 节点 6 的 TC-201..221 执行过但**未判定合格**；覆盖率 96.6% / 82.95%；
- 节点 8 **没有 GO/NO-GO 判定**；
- 节点 1–8 的 `open_questions` 字面"未回答 0 件"，但其中 **6 条答案是 `drill-deferred`（延期，不是决定）**。

→ 所以这套东西目前证明的是"**流程能走通**"，不是"**产物是对的**"。

### 3.2 门禁（commit / 交付前）

```bash
py -3 -m tools.trace_check --strict              # 6 门，Exit 0 才可继续
py -3 -m tools.trace_check --strict --report reports/trace.json   # 失败时要这个，--strict 默认输出不含原因文件
```

| 门 | 查什么 | 会拦下什么 |
|---|---|---|
| gate1 | 野号（未登记 ID） | 自己编的 `R-999` |
| gate2 | 双方向追溯 | 有 TC 无 design_ids |
| gate3 | front-matter 7 字段 | 缺 `sensitivity` |
| gate4 | 生成物一致（I-ID 数 == Excel 列数） | 设计改了没重生成 |
| gate5 | snake/camel 分区 | 定义层写 `cmpCd` |
| gate6 | 机密（L3 13 条） | 真 IP / 真密码 / 真社員コード |

⚠ **`--skip` 不存在**（`rules/00 §9`、`CLAUDE.md 禁④` 提到它，但实现里没有这个参数）。
⚠ **gate6 只扫 `docs/ .claude/ tutorial/`**，扫不到 `tools/`、`reports/` 和根目录 md（事实 #1）。

### 3.3 规则怎么生效

`.claude/rules/*.md` 是**自动加载**的——不需要"记住要守规矩"，文件在就会进上下文。
所以改规则的敌人不是"没人遵守"，是"规则越写越长、AI 抓不住重点"。
判定标准：**一条规则如果机器能查，就不该靠 AI 读**（应下沉到 `trace_check`）。

### 3.4 变更环（n09）

说 `指摘` → 起票（`tools.registry alloc`）→ `tools.impact <ID>` 出影响面 → **人裁定回到哪个节点**
（`reenter_node`）→ `registry mark-stale` 标记下游失效 → 从该节点重做 → 回归 → 再交付 → 知识沉淀。
**发号、回退裁定、失效记录、再批准四项都是人的**，AI 只出草案。

---

## 4. 未实现 / 半实现：清单与补法

### 4.1 P0 —— 真实案件上直接不能用

| # | 缺口 | 证据 | 补法 | 量级 |
|---|---|---|---|---|
| P0-1 | **任意节点入口**（客户给基本设计书→从节点3 起） | `SKILL.md:53,183-184`；`case.yml` 无 `start_node` | 见 §8 完整设计 | 中（1 skill + 1 agent + schema 3 键） |
| P0-2 | **案件硬编码**：`tutorial/R60Login` 写死在 coach 卡片与 8 份作业票 | `.claude/**/*.md` 里 165 处 `R60Login`、120 处 `tutorial/R60Login` | 路径参数化：卡片正文改用 `{{case_dir}}`，由 `case.yml.case` 注入；先把 8 份 nodes/*.md 的 12 处路径抽成变量 | 中（文本替换 + 1 处渲染逻辑） |
| P0-3 | `code-from-design` **只认 R-101** | `SKILL.md:41,49` 明确拒收未登记外 R-ID | 把"R60Area 专用段"显式标为 `migration/R60 专用`，另开一段 greenfield 通用流程（设计→代码只看 D/L/E，不看表名） | 中 |
| P0-4 | **门禁扫描范围与规则不符** | 事实 #1；违反 `rules/06 §3`"只能扩不能缩" | 把 `SCAN_BASES` 扩到 `("docs",".claude","tutorial","tools","reports")`，并给 `reports/**` 加白名单（traces json 里有大量 ID 字样，需先跑一遍看误报） | 小（但要先评估误报） |
| P0-5 | **git 0 commit** | 事实 #2 | 先 `git add .claude/ CLAUDE.md START_HERE.md` 等入库项做首个 commit；`docs/ tools/ reports/` 的 opt-in 策略要重新决定（否则交付物永远不在版本里） | 决策 > 工作量 |
| P0-6 | node3 agent 把 **Oracle/RR-MM-DD/ROWID/ALLOWED_SORT_FIELDS** 写成无条件 | `.claude/agents/trans-cosmos-ai-node3-detail-design.md` 末段 vs `nodes/n03:36-41`（栈在节点4 才定） | node3 agent 改为"读 `docs/40_framework/` 选定栈；未定则只用栈无关描述" | 小 |
| P0-7 | **n09 用野号** `CR-201..CR-205`（事实 #8） | `n09.yml` vs `ids.yml` | 要么补登进 `ids.yml`，要么改回已发号；并把 `docs/00_plan/coach/**` 的 `case_ref` 纳入 gate1 | 小 |
| P0-8 | **n04 承认版标了未签的版本**（事实 #9） | 节点4 `05:5,8` vs `closeout.md:38-40` | 版本降回 v1.0.0 或由人重签 v1.0.1；加一条检查：`05_承認版_*` 的 version 必须与 `nNN.yml` 记录一致 | 小 |
| P0-9 | **教学号段的 Q 号 0 登记** → `registry blockers` 恒空 | `ids.yml` Q 前缀 0 条，而 Q-201..Q-238 被引用 301 次 | 已知设计（`reports/drill/R60Login/README.md` 坑1，2026-10-19 已决"机制不改"）。**但代价是"未回答 0 件"是假象**——n06/n07/n08 共 6 条的答案是 `drill-deferred`（延期，不是决定）。建议：至少把 `drill-deferred` 在卡片上显示为"未决" | 小 |

### 4.2 P1 —— 骨架可信度问题

| # | 缺口 | 补法 |
|---|---|---|
| P1-1 | **KPI 计量 0**（§13 六维度） | `tools/kpi.py`：从 `reports/*.json` + `coach/*.yml` 算 6 个指标（追溯完备率、一次通过率、返工次数、门禁失败率、人工介入时长、文档陈旧天数），输出 `reports/kpi/<date>.json`。**先只算能自动算的 3 个**，其余留人工 |
| P1-2 | **差分検証パターン**（§10.2.1） | `tools/diffcheck.py <before> <after>`：对同一 ID 集合做结构差分（字段增删/值域变化/依赖变化），输出人读表。日常改造与 n09 回归都用得上 |
| P1-3 | **Prompt 模板库**（§11.4） | 新建 `.claude/prompts/`，把 9 个 node agent 里"要 AI 干什么"的段落抽成模板 + 变量（`{{case}}`/`{{node}}`/`{{upstream}}`）。agent md 只留"读哪些文件、写哪、禁什么" |
| P1-4 | **正式 Excel / 客户模板回流**（§9.3） | `gen_formal` 去 R-101 化（列来自设计，不写死）；加"指摘シート"导出（`rules/00 §11` 的受控回流），Phase2 再做客户模板对接 |
| P1-5 | **evaluation 治理** | `eval/gold-qa.yaml`（80 题）已有，但没有 runner 产出趋势。加 `tools/rag eval --baseline` 存档 + 对比 |
| P1-6 | **占位符风格统一** | `tools/masking` 的 `[[KEY]]` 与规则的 `PWD_1/IP_1` 二选一（建议保留 `PWD_1` 体系，masking 加 `--style=p_underscore`） |
| P1-7 | **`docs/**` 下 0 个中文视图** | 媒体二重化只在 `tutorial/` 和 `reports/` 执行了；`docs/` 59 本 md 对应 0 本 `.zh.html`。若想让中方同事读实案件产物，需要一条批量生成命令（且生成物不手改） |
| P1-8 | **7 个 `.zh.html` 已过期** | `closeout.md:58-70` 自认；实测正好 7 个（节点3/5/6/7 的 `05`、节点8 的 `01`/`05`、`comparison.md`）。需要"机读源比视图新就报错"的检查，否则视图会悄悄落后 |

### 4.3 P2 —— 平台化后才需要

| # | 缺口 | 说明 |
|---|---|---|
| P2-1 | G2–G5 门禁（build / console / smoke / 截图对比） | `rules/04 §9.1` 已诚实说明"本骨架不是守"动起来的应用"的装置"。**不建议现在做** |
| P2-2 | anomaly 自动建单、检查自动追加、周次提醒 | `rules/06 §6` 已列"未实现"；依赖 issue tracker，非本仓能力 |
| P2-3 | 多人协作（team > 1） | `case.yml.team` 现在是单元素；`handoff.md` 机制在，但没有并发写保护 |
| P2-4 | 鉴权与审计日志 | 骨架是本地工具，无多租户；若上平台由平台层承担 |

### 4.4 文档与实现不一致（会误导人，**建议优先修**，都是小改）

| # | 位置 | 文档说 | 实际 |
|---|---|---|---|
| D-1 | `rules/00 §9`、`CLAUDE.md 禁④` | 有 `--skip` 选项，禁止用它跳门 | **参数不存在**（`trace_check` 无 `--skip`） |
| D-2 | `rules/01` 走査対象 | 扫 `tools/**`、`reports/**`、根目录 md | 只扫 `docs/.claude/tutorial` |
| D-3 | `rules/04 §7`、`nodes/n07:162` | A/B 报告放 `doc/03_AI/AB_Reports/` | 死路径（仓库是 `docs/`） |
| D-4 | `SKILL.md:525` | `requirement-interrogator` 列在"使う agent" | 它是 **Skill**，`.claude/agents/` 里没有 |
| D-5 | `nodes/n03` | 步骤 1/4、2/4、3/5、4/5、5/5 | 编号错乱 |
| D-6 | `agents/node5` | Phase1 不动 `src/`、`app/routers`（无条件） | 作业票写的是"`migration` 案件では" |
| D-7 | `docs/90_knowledge/ppt-coverage-assessment.md`（2026-10-14） | RAG ❌、0/8 承认 | 已过时（RAG 工具存在、8/8 承认）——**需标注"历史快照"或更新** |
| D-8 | `使用手册.md §已知缺口` | "git 不是仓库" | 已是仓库（0 commit） |
| D-9 | `rules/03 §5`、`agents/node3` | `ALLOWED_SORT_FIELDS = {CMP_CD,JIG_CD,ARA_CD}` | 这是 R60Area 业务列，不是通用约束 |
| D-10 | `docs/00_plan/tasks.md` | 22 条全部 pending | 文件自己声明"以 AC-selfcheck 为准"，但读者看到的是"啥都没做" |
| D-11 | `phase0-closure.md:35-42`、`agent-run-record.md:84`、`ppt-coverage-assessment.md:132` | 0/8、1/8、"一次没跑" | 实际 8/8（事实 #7） |
| D-12 | `repo-inventory.md:145`、`review.md:108`、`CLAUDE.md:122`、`spec.md:100` | 124 件 / 79 件 / `field_count=56` | 实测 164 件 / `field_count=77` |
| D-13 | `ids.yml:676-677` | CR-005 `status: open` 但 description 写"已 closed" | 自相矛盾 |
| D-14 | `CLAUDE.md:69`、`rules/00:53` | R60Common **54** 函数 / r60util **31** クラス | 知识库实测 **60**（54 sync+6 async）/ **19**（`legacy-r60/04-common-parts.md:23-25`） |
| D-15 | `phase0-closure.md:38,120`、`legacy-r60/00-index.md:112` | 画面卡 1/56 | 实测 8 张 |
| D-16 | `coach/R60Login/case.yml` notes | "教学号段不登记 ids.yml" | 2026-10-26 已批量登记（`ids.yml:697-705`） |
| D-17 | `coach/R60Login/handoff.md` 的环表 | 只列 CR-002/003/004 | n09 实有 CR-002/003/004/005 + CR-201..205 |

---

## 5. 实施方案 A：モデルゲートウェイ（仅接口）

### 5.1 先说清楚：为什么现在做"接口"就够

- 今天的执行体是 Claude Code 本身，**工具层 0 处程序化模型调用**（事实 #3）。
- 真正需要网关的只有两处：
  1. **RAG 的 embedding / rerank**——检索必然要算向量；
  2. **换供应商的移植缝**——闭域网内 Claude Code 不可用，届时模型换成公司提供的服务。
- 因此接口按这两处设计，**不做通用抽象**（做通用抽象等于给未来的自己挖坑）。

### 5.2 目录与契约

```
docs/01_context/gateway.yaml          # 配置（不含密钥，只写环境变量名）
docs/40_framework/gateway-contract.md # 给公司/供应商的接口契约（一页）
tools/gateway/__init__.py             # 门面：get_gateway()
tools/gateway/base.py                 # Protocol: chat() / embed() / health()
tools/gateway/providers/openai_compat.py
tools/gateway/providers/stub.py       # 离线桩：固定回复 + 固定向量
tools/gateway/__main__.py             # CLI: ping / chat --json / embed --json
```

```python
# tools/gateway/base.py（形状，非最终代码）
class Gateway(Protocol):
    def chat(self, req: ChatRequest) -> ChatResponse: ...
    def embed(self, texts: list[str], *, model: str | None = None) -> list[list[float]]: ...
    def health(self) -> dict: ...

@dataclass(frozen=True)
class ChatRequest:
    messages: list[dict]          # role/content
    model_tier: str = "standard"  # fast / standard / deep → 由配置映射到真实模型名
    purpose: str = ""             # 审计用：node3.sql / rag.rerank / translate
    temperature: float = 0.0
    max_tokens: int = 4096
    trace_id: str = ""            # 关联到 R/F/D/L 或 case/node
```

### 5.3 三条硬约束（写进代码，不靠自觉）

1. **外投必过脱敏**：`chat()` 在发送前强制走 `tools.masking`，开关 `redact: true` 不可关闭；
   关闭需在配置里显式写 `allow_unmasked: true` 且 CI 报错提醒（红线⑦）。
2. **密钥只从环境变量取**：配置里写 `api_key_env: COMPANY_GW_KEY`，绝不写值。
3. **每次调用落审计**：`reports/gateway/<yyyymmdd>.jsonl`，记 `purpose/trace_id/模型/耗时/token/是否脱敏`，
   **不记正文**（正文可能含 L3）。

### 5.4 给公司的接口契约（一页，§5.2 的 `gateway-contract.md` 内容）

| 方法 | 路径 | 入参 | 出参 | 必需 |
|---|---|---|---|---|
| GET | `/healthz` | — | `{status, models[]}` | ✅ |
| POST | `/v1/chat/completions` | OpenAI 兼容 | OpenAI 兼容 | ✅ |
| POST | `/v1/embeddings` | `{input[], model}` | `{data:[{embedding[]}]}` | ✅（RAG 用） |
| GET | `/v1/models` | — | `{data:[{id, context_length}]}` | 可选 |

**只要求 OpenAI 兼容**——因为公司现有平台大概率就是这个形状，适配层 0 成本；
若公司给的是私有协议，**只改 `providers/` 一个文件**，上层不动。

### 5.5 验收

```bash
py -3 -m tools.gateway ping --json        # 无网络时应优雅失败并提示"用 stub"
py -3 -m tools.gateway chat --purpose smoke --json
py -3 -m tools.gateway embed --json "测试一句"
```

Exit 0 + JSON 输出即算接通；`stub` provider 必须能在**完全离线**下让整条链路跑通。

---

## 6. 实施方案 B：RAG 本地知识库（仅接口）

### 6.1 现状盘点（`tools/rag`）

| 能力 | 现状 |
|---|---|
| 切块 | 已固化在 `docs/90_knowledge/legacy-r60/chunks/*.jsonl`，12 个必填字段：`chunk_id/module/artifact_type/ids/title/source_path/source_locator/sensitivity/corpus_scope/text/sha256/version` |
| 检索 | 词法（hash n-gram + SQLite FTS），**不是向量** |
| 评测 | `eval/gold-qa.yaml` 80 题，有 recall@k / MRR |
| 语料作用域 | `corpus_scope` = `teaching` / `holdout` |

**这个 chunk schema 设计得比大多数 RAG 项目好**——`source_path` + `source_locator` + `ids`
天然支持"引用到行/节 + 追到 ID"。**不要推翻它**，接口就以它为准。

### 6.2 门面接口（新增 `tools/rag/api.py`）

```python
class Retriever(Protocol):
    def search(self, query: str, *, scope="teaching", top_k=5,
               filters: dict | None = None) -> list[Hit]: ...
    def stats(self, scope="teaching") -> dict: ...
    def health(self) -> dict: ...

@dataclass
class Hit:
    chunk_id: str
    text: str
    score: float
    source_path: str
    source_locator: str   # 例如 "L-014-R60Area-search.yaml#§3.2"
    ids: list[str]        # 引用可追到 R/F/D/L
    sensitivity: str
    provider: str         # local-lexical / kb-platform / company
```

**契约三条**（换 provider 也不能变，否则引用会碎）：
1. 每条命中必须能拼出 **`file#locator`** 形式的人类可核对的出处；
2. 每条命中必须带 `ids`，能落到 `ids.yml` 的某个 ID（这正好接红线⑤）；
3. `score` 只用于排序，**不允许跨 provider 比较绝对值**（不同算法尺度不同）。

### 6.3 Provider 三层

| provider | 何时用 | 实现 |
|---|---|---|
| `local-lexical` | 现在默认；离线、零依赖 | 把现有 `store.search()` 包一层 |
| `kb-platform` | 有 kb-platform 时（见 §7） | HTTP `/kb/search` 或 CLI `--json` |
| `company` | 公司提供 RAG 服务后 | 同上形状，换 base_url |
| `stub` | CI 与单测 | 固定返回 3 条，保证确定性 |

配置：`docs/01_context/rag.yaml` → `provider: local-lexical` / `base_url` / `scope_map`。

### 6.4 语料的生产链路（这是真正的难点，不是检索）

现在 chunk 是**手工/一次性生成**的。要变成常态，需要 `tools/rag/build_from_docs`：

```
docs/10~70_*/**.yaml|md（机读源，7 字段）
   → 切块（沿用 kb-platform 的规则：700 字、表格一行一块、无重叠）
   → 补齐 chunk 12 字段（source_locator 用文件内标题路径，ids 从 front-matter 抽）
   → 写 docs/90_knowledge/<module>/chunks/*.jsonl（**生成物，不手改**）
   → build 索引
   → eval 对 gold 集回归（recall@5 不降才入库）
```

**关键约束**：chunk 文件是**生成物**，和 `.zh.html` 同级待遇（`rules/00 §11`：生成物不手改）。
现在没有生成器，等于每加一个案件都要手工做语料——这是不可持续的。

### 6.5 验收

```bash
py -3 -m tools.rag stats --json
py -3 -m tools.rag query "排他制御の不一致" --top-k 5 --json
py -3 -m tools.rag eval --json      # recall@5 ≥ 0.85
```

---

## 7. kb-platform 接入方案

### 7.1 它是什么（与骨架的分工）

| | 骨架 `tools/rag` | kb-platform |
|---|---|---|
| 定位 | 训练/演示用的**词法检索** | 生产级**知识库平台**（分块/摄取/混合检索/评测/HTTP 服务） |
| 依赖 | 纯标准库 | numpy + FastAPI |
| 检索 | hash n-gram + FTS | dense(hash 或 bge-m3) + sparse(bigram IDF) + **RRF(k=60)** + rerank |
| 元数据 | 12 字段 chunk | 8 字段 front-matter（`doc_id/scope/title/doc_type/version/status/conf_level/updated_at`） |
| 准入 | — | `conf_level` 10/20/30/40 + `doc_type` 枚举 + `scope` company/project |
| 接口 | CLI + Python 函数 | HTTP `POST /kb/search`、`GET /kb/stats`；CLI `lint/ingest/search/eval/stats` |

**分工建议**：骨架负责"**生产**机读源"（8 工程、ID、追溯、门禁），kb-platform 负责"**检索**"。
骨架不重写 chunker/embedder/rerank——那是重复建设。

### 7.2 接入方式（推荐组合，不是三选一）

| 用途 | 方式 | 理由 |
|---|---|---|
| **读**（检索） | CLI `run.py search --json` 包成 `KBPlatformProvider` | 不需要把 numpy/FastAPI 装进骨架环境；进程隔离，崩了不影响门禁 |
| **写**（入库） | 骨架产 md → **暂存目录** → `run.py lint` → `run.py ingest` | lint 是唯一能挡住"元数据不合法"的闸门，**不能跳过** |
| **服务态**（若公司要提供 HTTP） | `api.py:build_router()` 挂到公司网关 | 骨架侧只换成 `HTTPProvider` |

**为什么不选 `import kbkit`**：会把 numpy 变成骨架的硬依赖，`trace_check` 这些纯标准库工具
从此要装科学计算栈——为了检索牺牲门禁的可移植性，不划算。

### 7.3 元数据映射层（**这是接入的真正工作量**）

两套 front-matter 不兼容（事实 #5）。做一个**单向生成器**，不写回机读源：

```yaml
# 骨架 7 字段                      # → kb-platform 8 字段
id: L-014                          doc_id: L-014
type: detail-design                doc_type: design-detail        # 枚举映射表
req_ids: [R-101]                   （放进正文的 ids: 行，hint 用）
status: baselined                  status: baselined
sensitivity: internal              （kb 无此字段 → 进 sensitivity 目录策略）
owner: AI-SE                       （kb 无此字段）
version: 0.3.0                     version: 0.3.0
（新算）                            scope: project | company
（新算）                            project_id: R60Login
（新算）                            conf_level: 40/30/20/10
（新算）                            updated_at: <文件 mtime 或 git 日期>
```

**`conf_level` 映射规则**（建议，需你确认）：
`40` = baselined 且人已承认的承认版；`30` = baselined；`20` = draft/open；
`10` = 教学/虚拟/倒推产出（`tutorial/**`、`virtual-requirement-author` 的产物）。
→ 这样"倒推的虚拟需求书"天然低于真案件文档，不会被当成事实引用。

**落点**：`build/kb-staging/<case>/`（已 gitignore）。骨架 `docs/**` 不被写入任何 kb 元数据。

### 7.4 三个必须先解决的问题（来自 kb-platform 自身的风险清单）

| 风险 | 现象 | 骨架侧对策 |
|---|---|---|
| **embedder 不一致静默出错** | 用 `--embedder hash` 建库、用 `bge` 查询（或反之），结果全错但不报错 | 配置写死 `embedder`，`stats` 里存 embedder 名；查询前比对，不符**直接报错** |
| **无鉴权 + `user_level` 从请求体取** | 任何进程都能查 `conf_level=40` 的内部文档 | 只在本机/内网跑；若要给多人用，level 必须由服务端按身份注入，不信请求体 |
| **`init_schema` 每请求执行** | 并发下性能差 | 只影响服务态；我们用 CLI 方式则无此问题 |

---

## 8. 任意节点入口（核心设计）

### 8.1 你的诉求与原机制的冲突点

你要的是：**客户直接给了一本基本设计书 → 从节点 3 开始**。

现有机制挡在两处：

1. 当前节点 = "依赖已满足且未批准的**最小号**"（`SKILL.md:53`）→ 永远从节点 1 找起；
2. 前置未批准 → **不起动**，且写明"例外を認めない"（`SKILL.md:183-184`）。

子代理的报告里提到一种"手工绕过"（把外部设计书塞进 `节点2_基本设计/05_承認版…` 再把 `n01/n02`
手工改成 approved）。**这条路必须明确禁止**——它是**伪造承认证据**，直接违反红线③，
而且框架不校验承认来源，等于把最硬的一条红线变成一句空话。

**所以正确做法不是"绕过"，是"把这种情况变成合法的一种"。**

### 8.2 引入一个与"承认"并列的新概念：受入（intake）

| 概念 | 含义 | 谁签 | 是否等于"我方认可其正确" |
|---|---|---|---|
| **承认**（approved） | 我方生成、并经人审查通过 | 我方评审人 | 是 |
| **受入**（adopted） | **不是我方生成**，是外部给定（客户/上游供应商）的既有文档，我方仅**登记、补元数据、评估缺口**后接收 | 我方责任人 + 记录提供方 | **否**——只表示"我们按这个做，且知道它缺什么" |

二者在下游**等效可用**（都用其产物作为输入），但在证据上**必须可区分**——
这样出问题时能回答"错在我方还是错在来件"。

**新增状态值**：节点 `state` 增加 `adopted`（与 `approved` 并列，不替代）。
`approved_by` 之外增加 `adopted_from`（提供方 + 文件 + sha256 + 日期 + 签收人）。

### 8.3 `case.yml` 增加 3 个键

```yaml
start_node: 3                 # 本案件从哪个节点起跑（默认 1）
entry_mode: intake            # self（默认，全自产） | intake（含外部受入）
intake:                       # 仅 entry_mode=intake 时存在
  - node: 2
    source: "客户提供_基本设计书_v1.2.pdf"      # 原始来件
    adapted_to: "docs/20_basic_design/"         # 适配后落点
    sha256: "…"
    provided_by: "客户 SE 部"
    adopted_by: "SE-001"                        # 必须是人
    adopted_at: "2026-10-27"
    gaps: "docs/00_plan/coach/<module>/intake-n02-gaps.md"
```

`n01.yml`/`n02.yml` 相应写 `state: adopted` + `adopted_from`。

### 8.4 入口流程（6 步，可固化成 `tools/intake`）

```
① 登记      把来件原样放进 docs/01_context/intake/<case>/（只读，不改）
            记 sha256、提供方、日期 → case.yml.intake[]
② 体检      requirement-interrogator 的 51 观点扫这本设计书
            → 输出「这本设计书没说清什么」= gaps.md（A 类问题给客户，B 类给提案）
③ 适配      抽 F/I（或 L/D/E）→ 用 tools.registry alloc 在 ids.yml 发号
            产出我方的机读源（YAML，7 字段）+ 一张「外部编号 ↔ 我方编号」对照表
④ 缺口裁决  人看 gaps.md：哪些必须问客户后才开工（block），哪些可以带着走（记录）
⑤ 签收      state: adopted，adopted_by=人，gaps 挂到 nNN.yml.open_questions
⑥ 起跑      coach 从 start_node 出第一张卡（节点 3）
```

**关键点**：第 ③ 步是**必须的**，不能省。外部文档几乎不可能自带 `R/F/I/D/L/E` 编号、
`req_ids` 和追溯链。不做适配就直接用，等于让 `trace_check` 从第一天起就是红的，
或者逼人跳过门禁（红线⑥）。

### 8.5 依赖检查怎么改（一处，改两个字）

```diff
- 前置节点若未 approved → 不起动，直接告知（例外を認めない）
+ 前置节点若未 approved 且未 adopted → 不起动，直接告知
```

铁则 10（`SKILL.md` §7）同步这一句。**这是唯一的机制改动**，其余不动。

### 8.6 三种入口模式的完整矩阵

| 客户给了什么 | entry_mode | start_node | 机制 |
|---|---|---|---|
| 只有需求书（常规） | `self` | 1 | 现状，不变 |
| 需求书 + 基本设计书 | `intake` | 3 | n01/n02 受入；n03 起自产 |
| 只有既有系统代码（改造案件） | `self` + 节点0 | 1 | `virtual-requirement-author` 倒推需求书（已有） |
| 只有详细设计书 | `intake` | 4/5 | n01~n03 受入 |
| 什么都不给 | — | — | 拒绝：无输入不能开工（`n01` 前置检查） |

### 8.7 与红线的关系（必须写清，否则会被当成"跳过红线"）

| 红线 | 受入模式下的处理 |
|---|---|
| ① 野号禁止 | **不放松**。外部编号必须先 `registry alloc` 换成我方号，对照表留档 |
| ② 设计なき製造禁止 | **不放松**。从节点 5 起跑 = 前 4 个节点全部受入，每份都要有 gaps 清单；缺关键项则 block |
| ③ 无承认不进下一节点 | **语义扩展**：`adopted` 也需人签收（`adopted_by` 必须是人的 ID）。**AI 不得自签** |
| ④ 栈无断变更禁止 | 受入的设计书隐含技术栈 → 节点 4 受入时**必须**记录"栈来自来件"，否则节点 5 无据可依 |
| ⑤ TC 必须有出典 | **不放松**。受入模式下若设计书无 E-ID，节点 6 会缺 design_ids → 由 ③ 的适配补出 |
| ⑥ 无 trace_check 不 commit | **不放松** |
| ⑦ 未脱敏不外投 | **不放松**；外部来件本身可能含真实值 → 第 ① 步入库前先过 masking |

**一句话**：受入改变的是"**谁产出**"，不改变"**要有出处、要有人签、要能追溯**"。

### 8.8 工作量与验收

- 新增：`case.yml` 3 键 + `state: adopted` + 一处依赖检查改造 + `tools/intake`（登记/体检/适配/签收）
- 复用：`requirement-interrogator`（体检）、`registry alloc`（适配发号）、`trace_check`（验收）
- 验收：拿一本真实的外部设计书（脱敏后）走一遍 → 节点 3 能出第一张卡，且 `trace_check --strict` 仍 Exit 0

---

## 9. 已拍板的四件事（2026-10-28）

> 出典：2026-10-28 本会话中用户的直接选定（不是 AI 推断，也不是"某日的口头裁定"）。
> 这四条会改变后续所有做法，故在此登记；改动实现后须回到本节核对。

| # | 议题 | 决定 | 影响 |
|---|---|---|---|
| 1 | 任意节点入口的方式 | **受入（intake）**：外部文档登记为我方上游产物，人签收后从 `start_node` 起跑；上游标 `adopted`（不是 `approved`） | 采用 §8 全案；**不做倒推**（`virtual-requirement-author` 保持只用于"只有现有代码"的改造案件） |
| 2 | 实案件的产物根目录 | **沿用 `docs/10~70_*`**，不改成 `节点N_*` 结构 | 需改写 8 份作业票与 coach 卡片里的路径（改为由 `case.yml.case` 注入）；规则 02 §2 的 8 工程表不变 |
| 3 | 修复顺序 | **入口机制与去 R60Login 化一起做**（它们是同一件事的两半） | 第一批 = 路径参数化 + `adopted` 状态 + `tools/intake`；文档不一致与门禁扩范围排第二批 |
| 4 | git 入库 | **`docs/ tools/ reports/` 全部入库** | 先做首次 commit 作为安全网（当前 0 commit，任何大改都不可回退）；红线⑥此后才有对象可执行 |

**未决（不在本次四个问题内，后续再议）**：`conf_level` 具体映射（§7.3 给了建议值）、
`--skip` 是补实现还是删文档、`docs/**` 的中文视图要不要批量生成。

---

## 10. 第一批的实施步骤（已按拍板结果排好）

> 顺序原则：**先给安全网，再动结构**。没有 commit 之前不做批量改写。

| 步 | 做什么 | 动到的文件 | 验收 |
|---|---|---|---|
| 0 | ~~调 `.gitignore` → 首次 commit~~ **✅ 已完成（2026-10-28）**。附带发现并处理：`tools/trace_check/aux.py` 是 Windows 保留设备名（AUX），git 无法 `open()`；改用 `update-index --cacheinfo` 只能硬塞进去，之后 `git status` 永久报假修改、`git add -A` 与 `git diff` 全部失败。经用户同意改名 `aux_checks.py`（`921f706`），`SKILL.md:520` 原本就写 `aux_checks`，改名反而让文档与实体一致 | `.gitignore`、`tools/trace_check/` | `git log --oneline` 2 条；`git status --short` 0 行 |
| 1 | 路径参数化：8 份作业票 + coach 卡片正文的 `tutorial/R60Login/节点N_*` 改为 `{{case_dir}}`，由 `case.yml.case` 注入；实案件注入 `docs/` 下的工程目录 | `skills/.../nodes/n01..n08.md`、`SKILL.md:132-139` | 新案件 `case.yml` 只改 `case:` 一处，8 个节点卡片路径全对 |
| 2 | `case.yml` 增 `start_node` / `entry_mode` / `intake[]`；`nNN.yml` 允许 `state: adopted` + `adopted_from` | `templates/case.yml`、`templates/node.yml` | 模板校验通过；旧案件向后兼容（缺键按默认 1/self） |
| 3 | 依赖检查改一处：`未 approved` → `未 approved 且未 adopted` | `SKILL.md §3.1`、铁则 10、`tools/coach_brief.py:72-79` | 构造一个 `n01/n02 adopted` 的假案件，coach 能出节点 3 的卡 |
| 4 | `tools/intake` 六步：登记 → 体检 → 适配发号 → 缺口裁决 → 签收 → 起跑 | 新增 `tools/intake/`；复用 `requirement-interrogator`、`registry alloc`、`masking` | 拿一份脱敏的外部设计书走通，`trace_check --strict` 仍 Exit 0 |
| 5 | 回归：R60Login 原流程不受影响（它 `entry_mode: self`、`start_node: 1`） | — | `coach_brief R60Login` 输出与今天一致 |

---

## 附录 A：本次执行的关键命令与原样输出

```text
$ grep -n "SCAN_BASES" -A2 tools/trace_check/__init__.py
285:    SCAN_BASES = ("docs", ".claude", "tutorial")

$ grep -rniE "anthropic|openai|api_key|chat/completions|requests\.post" tools/ --include=*.py
（0 行）

$ grep -nE "^def |^class " tools/rag/loader.py
REQUIRED_KEYS = {chunk_id, module, artifact_type, ids, title, source_path,
                 source_locator, sensitivity, corpus_scope, text, sha256, version}

$ grep -nE "REQUIRED|conf_level|doc_type" /d/AI_platform/kb-platform/kbkit/pipeline.py
16: REQUIRED_KEYS = ["doc_id","scope","title","doc_type","version","status","conf_level","updated_at"]
20: SCOPES = {"company","project"}

$ grep -nE "add_argument" /d/AI_platform/kb-platform/run.py
--json 仅出现在 search(157) 与 eval(166)；lint/ingest/stats 无 --json

$ for f in docs/00_plan/coach/R60Login/n0*.yml; do grep -E "^(node|state):" "$f"; done
n01..n08: state: approved（approved_by: - SE-001）
n09: open_changes: [BUG-002 state=fixing reenter_node=3]; closed: CR-002..005 + CR-201..205

$ git log --oneline            → fatal: your current branch 'main' does not have any commits yet
$ git ls-files | wc -l         → 0

$ grep -n "CR-20[1-5]" docs/00_plan/coach/R60Login/n09.yml | wc -l   → 5（ids.yml 无此 5 号）
$ grep -c "^Q-" docs/00_registry/ids.yml                              → 0

$ grep -n "status" docs/00_registry/ids.yml（CR-005 段）
676:  status: open
677:  description: "... 2026-10-23 已 closed"   ← 自相矛盾
```

（`trace_check --strict` 本次实测：6 门全 PASS，`total_ids=164`、`orphans=0`。）

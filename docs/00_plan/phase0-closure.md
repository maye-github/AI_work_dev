---
id: PLAN-PHASE0-CLOSURE
type: plan
req_ids: []
status: draft
sensitivity: internal
owner: AI-SE
version: 0.1.0
---

# Phase 0 收口记录（2026-10-19）

> **本文件的作用**：把"继续扩写框架文档"这条线**停住**，把现状钉成事实，
> 并把下一阶段的入口指向 **3 模块学习 → RAG → R60Login 练习**。
> 本文件**不是新框架**，不新增红线、不新增模板、不扩写 8 工程规则。

---

## 1. 一句话结论

**当前骨架是一套"文档治理 + 追溯门禁"，不是领导 PPT 所说的"统一 AI 平台"。**
它能检查"文档写得是否合规"，但**没有验证过 AI 能否端到端产出可运行的东西**。
因此下一阶段不以"再补文档"为主，而以"**用 3 个真实模块训练出可检索的知识，再让 AI 拿这份知识去解题**"为主。

---

## 2. 现状事实（可复核）

> **★ この表は 2026-10-19 時点のスナップショットである。** その後の進行で 1〜3 は解消した
> （2026-10-26 時点で 8 工程すべて `approved`。`py -3 -m tools.coach_brief` が現在地を出す）。
> 履歴として残すため、下の値は**当時のまま**書き換えない。

| # | 事実（2026-10-19 時点） | 証拠 |
|---|------|------|
| 1 | 8 工程 **0/8 承认** | `docs/00_plan/coach/R60Login/n01.yml`〜`n08.yml` 均为 `not_started` |
| 2 | 节点 1 跑过多次，**从未承认** | `tools/kb-platform/repo/projects/P-R60-001/knowledge/agent-run-record.md` §1 |
| 3 | 节点 2〜8 **一次也没跑过** | 同上 |
| 4 | 画面卡 **1/56** | `tools/kb-platform/repo/projects/P-R60-001/screens/` 仅有 `R60Login.md` |
| 5 | RAG / 模型网关 / 评测 / 成本台账 **均未实现** | `tools/kb-platform/repo/company/standards/ppt-coverage.md` §4 |
| 6 | 6 道门存在，但**没能拦住 2026-10-14 的 `build_mode` 误改** | `review_diff_assets/_skeleton/review_comments.md` RC-SK-03 |
| 7 | R60Login 的虚拟需求书**部分来自实现** | `reports/drill/R60Login/provenance.yaml` 中多条 `source_kind: 実測` |
| 8 | `spec.md` Non-Goals 明确写了"不造平台"，而 PPT 要的正是平台能力 | `docs/00_plan/spec.md` Non-Goals 第 2 条 |

> **第 8 条是"看上去根本不行"的根因**：不是执行不力，而是**目标被写小了**。
> 本收口把目标改回 PPT 的方向，但**不推倒已有追溯门禁**——门禁保留，作为后续流水线的质量闸。

---

## 3. 冻结点（从此不再做）

1. **不再新增框架规则、红线、模板**。红线仍是 7 条（`CLAUDE.md` §1），不增不减。
2. **不再扩写 8 工程说明文档**。已有 `spec.md` / `tasks.md` / `review.md` 保持原样。
3. **不再把 R60 专属内容写进全局规则**。`migration`、`R60Common.ts`、`BaseCamelModel`、
   "Phase1 不触生产代码"等，都属于 R60 历史项目，不是默认骨架。
4. **不再把"文档写完"当作"能力具备"**。能力是否具备，只看**能否跑出可复核的产物**。
5. **不再用 R60Login 当教材**。Login 是考题；教材是 R60Area / R60Code / R60Item。
6. **不再以 `D:\AI_work` 的任何文件为写入目标**（永久只读）。

---

## 4. 隔离决定（先记录，改动需人批准）

以下条目**当前位于全局层**，但只对 `build_mode: migration` 成立。**默认 `greenfield` 不应加载它们。**

| 位置 | 条目 | 现状 | 后续处理（待批准） |
|------|------|------|--------------------|
| `CLAUDE.md` §2 禁① | 不改 `R60Common.ts` | 全局 | 下沉到 R60 profile |
| `CLAUDE.md` §2 禁② | 不改 `BaseCamelModel.model_config` | 全局 | 下沉到 R60 profile |
| `.claude/rules/00-project-global.md` §8 | parallel 新版禁止 | 已标注 migration 固有 | 保持标注，移出默认加载集 |
| `.claude/rules/00-project-global.md` §10 | Phase1 不触生产代码 | 已标注 migration 固有 | 保持标注，移出默认加载集 |
| `.claude/rules/03-design-coding.md` §3 | R60Common 13 函数映射表 | 已标注 migration 固有 | 移入 R60 profile |
| `.claude/skills/code-from-design-trans-cosmos-ai/SKILL.md` | description 写死 migration-only | migration-only | 保留；greenfield 制造不走此 skill |
| `AGENTS.md` | 角色定义含 R60 内容 | 混合 | 拆分 |

> **红线③④**：改全局规则、改技术选型都必须**人批准**。
> 因此本表只是**登记**，本轮**不动任何 `.claude/rules/` 与 `CLAUDE.md` 条文**。
> 待 3 模块学习完成后，连同"是否保留 migration 变种"一并提请裁定。

---

## 5. 教材 / 考题的分界

| 角色 | 模块 | 允许 AI 读什么 | 用途 |
|------|------|----------------|------|
| **教材** | `R60Area`（简单） | 设计书、单测仕様、前后端实现、AB 报告 | 学会"一个画面从需求到测试长什么样" |
| **教材** | `R60Code` + `R60CodeMes`（中等） | 同上 | 学会"主从表、两画面联动" |
| **教材** | `R60Item` + `R60ItemMulti` + `R60ItemSup`（复杂） | 同上 | 学会"多行、上传、输入支援、164 字段" |
| **考题** | `R60Login` | **仅设计书与单测仕様；实现侧在练习期间不可读** | 检验 AI 能否独立复现 |

> **R60Login 现有资产已被污染**（画面卡与虚拟需求书在读过实现之后才写）。
> 若要用它做**盲测**，必须：
> 1. 只从**设计书（文書）**重建需求书，删除 `provenance.yaml` 中所有 `source_kind: 実測`；
> 2. 练习期间**不把 `R60Login.vue` / `R60LoginController.py` 放进检索语料**；
> 3. 对比只在节点 8 之后由 `drill-comparator` 读实现。
>
> 若做不到以上 3 点，Login 只能作为"流程演练"，**不得作为能力测量样本**。

---

## 6. n09（变更环）决定

**暂停启用。** 主链（n01〜n08）尚未跑通一次，变更环没有可变更的对象。
待 3 模块知识库建成、Login 练习跑完一轮后，再评估是否启用。

---

## 7. 本阶段的完成判据

- [ ] 本文件落盘，且未改动 `.claude/rules/` 与 `CLAUDE.md`
- [ ] `tools/kb-platform/repo/projects/P-R60-001/learning-plan-3modules.md` 落盘
- [ ] 明确 3 模块资产路径与抽取目标
- [ ] 明确 RAG 语料格式、评测指标、防答案泄漏规则
- [ ] `py -3 -m tools.trace_check --strict` 退出码为 0

---

## 8. 下一步

按 `tools/kb-platform/repo/projects/P-R60-001/learning-plan-3modules.md` 执行 **Week 1：R60Area 抽取**。
不先建模型网关，不先建流水线，不先补其余 55 张画面卡。

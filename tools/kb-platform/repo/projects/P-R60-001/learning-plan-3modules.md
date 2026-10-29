---
id: KNOW-LEGACY-R60-LEARNING-PLAN-3MODULES
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-learning-plan-3modules
scope: project
project_id: P-R60-001
title: 3 模块学习计划 — R60Area / R60Code / R60Item
doc_type: decision
conf_level: 30
updated_at: '2026-10-28'
---

# 3 模块学习计划 — R60Area / R60Code / R60Item

> **本文件是 Phase 0 收口后的第一份执行清单**（收口记录：`docs/00_plan/phase0-closure.md`）。
>
> **目标**：从 R60 历史案件中**学 3 个代表模块**（简单 / 中等 / 复杂），把学到的知识做成
> **可检索、可引用、可评测的 RAG 知识库**；然后用 `R60Login` 做**真正的练习**（考题）。
>
> **不是**：照抄 R60 的代码，不是重写这 3 个模块，不是继续扩写框架文档。
>
> **红线**：`D:\AI_work` **永久只读**。所有产物只写 `D:\AI_work_dev`。
> 需要读取实现代码时，只读、只摘录结论，不复制整段源码进语料。

---

## 1. 为什么是这 3 个模块（选型证据）

| | `R60Area`（简单） | `R60Code` 家族（中等） | `R60Item` 家族（复杂） |
|---|---|---|---|
| 画面 | 1 画面 | 2 画面（Code + CodeMes） | 3 画面（Item + ItemMulti + ItemSup） |
| 设计书 | 1 册（980 KB） | 2 册（399 KB + 414 KB） | 3 册（1.7 MB + 6.6 MB + 257 KB） |
| 单测仕様 | 1 册 | 2 册 | 3 册（含"複数行、アップロード"） |
| 前端行数 | 1,485 + 54（service） | 1,715 + 1,318 + 2 service | 3,778 + 9,752 + 715 + 3 service |
| 后端行数 | 2,915 | 3,137 + 2,645 | 8,715 + 11,861 + 797 |
| AB 报告 | `reports/R60Area/`（7 文件） | `reports/R60Code/`、`R60CodeMes/` | `reports/R60Item/`、`R60ItemMulti/` |
| 核心难度 | 3 键主表、搜索分页、排他、被参照、重複 | 主从表（1:N）、`simKbn` 模拟切换、排序 | 164 字段、多行网格、CSV 上传、输入支援、全 POST |

**复杂度梯度是真实的**，不是人为划分：

- `R60Area` = **单表 CRUD 的完整闭环**，适合先建立"一张画面卡应该长什么样"的模板。
- `R60Code` = **主表 + 明细表**，多一个画面、多一层父子关系，适合学"跨画面 ID 链"。
- `R60Item` = **一个业务对象的三种形态**（单品 / 多行上传 / 输入支援），
  单文件近 1 万行，**必须拆成子单元**才能进入上下文——这正是 PPT 说的"复杂功能要分割"。

> `spec.md` Non-Goals 早已写明这三档；本计划只是把它从"ID 贯通示例"升级为"学习 + RAG 语料"。

---

## 2. 每个模块要学什么（7 类产物）

每个模块**不是写一份总结**，而是产出 7 类**结构化、可检索**的卡片。
卡片一律放在 `tools/kb-platform/repo/projects/P-R60-001/modules/<module>/`，画面卡沿用 `screens/` 的 12 节格式。

| # | 产物 | 文件 | 回答什么问题 | 主要来源 |
|---|------|------|--------------|----------|
| 1 | **画面卡** | `screens/<Module>.md` | 这个画面由哪些项目、事件、迁移组成？ | 设计书 `画面概要` / `画面項目内容` / `イベント一覧` |
| 2 | **字段词典** | `modules/<module>/01-fields.yaml` | 每个字段的日文名、snake/camel、DB 列、型、桁、必須、初期値 | 设计书 `画面項目内容` + DB 定義書 |
| 3 | **API 契约** | `modules/<module>/02-api.yaml` | 有哪些端点、actionId、请求/响应字段、分页与排序 | 设计书 `業務処理説明` + controller |
| 4 | **逻辑卡** | `modules/<module>/03-logic.yaml` | 搜索/编辑/排他/被参照/重複/状态判定的分支与边界 | 设计书 `業務処理説明` + controller |
| 5 | **错误卡** | `modules/<module>/04-errors.yaml` | 什么条件触发什么消息、能否恢复、对应哪个测试 | 设计书 + 单测仕様 |
| 6 | **测试观点** | `modules/<module>/05-tests.yaml` | 正常/边界/异常各测什么，用了哪种技法 | 单测仕様 |
| 7 | **差异/评审** | `modules/<module>/06-review.yaml` | 骨架规则与实物的差异、AB 报告的失败说明了什么 | `08-deviations.md` + `doc/03_AI/AB_Reports/` |

**所有卡片必须带出处**：`source_path` + `source_locator`（sheet/row 或 file:line）。
没有出处的结论不写进卡片——它是聊天，不是知识。

---

## 3. 模块一：`R60Area`（简单）— 先立模板

### 3.1 资产清单（已实测存在）

| 类别 | 路径 |
|------|------|
| 设计书 | `D:/AI_work/doc/02_INPUT/50.設計書/画面設計書/基刷_調達生産_マスタ_基本設計書(画面編)_05_R60Area_エリアマスタメンテナンス_v1.0.xlsx` |
| 单测仕様 | `D:/AI_work/doc/02_INPUT/60.単体テスト/2-041-F_単体テスト仕様兼チェックリスト(画面編)_05_R60Area_エリアマスタメンテナンス.xlsx` |
| 前端 view | `D:/AI_work/Front-end/src/views/R60Area.vue`（1,485 行） |
| 前端 service | `D:/AI_work/Front-end/src/service/R60AreaService.ts`（54 行） |
| 前端 components | `R60AreaCreate.vue` / `R60AreaEdit.vue` / `R60AreaCopy.vue` |
| 后端 | `D:/AI_work/api/fastapi_oracle_pjt/app/routers/R60AreaController.py`（2,915 行） |
| AB 报告 | `D:/AI_work/doc/03_AI/AB_Reports/reports/R60Area/`（head / init / detail / new / modify / download / summary） |

### 3.2 学习重点

1. **3 键主表**：`cmpCd` / `jigCd` / `araCd` 是唯一键；55〜56 字段如何组织。
2. **搜索**：`COUNT` + 分页；`ALLOWED_SORT_FIELDS` 白名单；白名单外回退 `JIG_HYJ_SEQ` + `ROWID`。
3. **编辑**：排他（`KSN_DAT` / `REV_NO`）、被参照检查、重複检查、ロケーション確認、`REG_STS` 判定、緊急配信。
4. **错误**：E-001〜E-008 的触发条件与消息。
5. **测试**：正常 3 / 境界 2 / 異常 3 是如何落到具体 TC 的。

### 3.3 完成判据

- [ ] `screens/R60Area.md` 12 节齐全，§12"未确认事项"非空
- [ ] `01-fields.yaml` 覆盖设计书"画面項目内容"全部行
- [ ] `02-api.yaml` 的 actionId 与单测仕様的 action 一一对应
- [ ] `03-logic.yaml` 至少覆盖 search / edit 两条主逻辑
- [ ] `04-errors.yaml` 覆盖 E-001〜E-008（或实测对应错误）
- [ ] `05-tests.yaml` 能映射到单测仕様的具体 sheet/row
- [ ] 每条知识有出处；**没有一段是整段复制的源码**

> Area 已是骨架 R-101 / F-042 / D-043 / L-014 / L-015 的示例。
> 本轮要做的是**核对既有示例是否来自设计书**；若发现它来自实现，登记到 `06-review.yaml`。

---

## 4. 模块二：`R60Code` 家族（中等）— 学主从表

### 4.1 资产清单

| 类别 | `R60Code` | `R60CodeMes` |
|------|-----------|--------------|
| 设计书 | `..._34_R60Code_コード値マスタメンテナンス_v1.0.xlsx` | `..._35_R60CodeMes_コード値明細マスタメンテナンス_v1.0.xlsx` |
| 单测仕様 | `2-041-F_..._34_R60Code_...xlsx` | `2-041-F_..._35_R60CodeMes_...xlsx` |
| 前端 view | `views/R60Code.vue`（1,715 行） | `views/R60CodeMes.vue`（1,318 行） |
| 前端 service | `service/R60CodeService.ts`（61 行） | `service/R60CodeMesService.ts` |
| 前端 components | `R60CodeCreate.vue` / `R60CodeEdit.vue` | `R60CodeMesCopy.vue` / `Create` / `Edit` |
| 后端 | `routers/R60CodeController.py`（3,137 行） | `routers/R60CodeMesController.py`（2,645 行） |
| AB 报告 | `reports/R60Code/` | `reports/R60CodeMes/` |

### 4.2 学习重点

1. **主从关系**：`R60Code`（コード值）与 `R60CodeMes`（コード值明細）如何关联、如何级联。
2. **`simKbn` 模拟切换**：同一画面在模拟模式下走什么分支。
3. **排序**：`sortField=JOH_ID`；分页参数命名 `currentPage` / `pageLimit` 与 Area 的 `current_page` / `page_limit` 不同——**命名不统一是真实情况，要记录，不要抹平**。
4. **`datainit`**：初期数据装载动作的语义与调用时机。
5. **AB 报告的 404**：`reports/R60Code/summary.md` 显示所有端点 404，但 controller 存在。
   **这条本身就是知识**：AB 报告的失败不等于功能缺失，可能是路径/参数/环境不一致。

### 4.3 完成判据

- [ ] 两张画面卡齐全，且**主从关系有一张单独的关联图或表**
- [ ] `02-api.yaml` 能解释 AB 报告 404 的原因（实测 controller 的路径/参数）
- [ ] `06-review.yaml` 记录至少 3 条"骨架命名假设 vs 实物"的差异

---

## 5. 模块三：`R60Item` 家族（复杂）— 必须拆分

### 5.1 资产清单

| 类别 | `R60Item` | `R60ItemMulti` | `R60ItemSup` |
|------|-----------|----------------|--------------|
| 设计书 | `..._06_R60Item_アイテムマスタメンテナンス_v1.0.xlsx`（1.7 MB） | `..._06_R60Item_...（複数行、アップロード）_v1.0.xlsx`（6.6 MB） | `..._S01_R60ItemSup_アイテム入力支援_v1.0.xlsx` |
| 单测仕様 | 同名 `_06_R60Item_...xlsx` | 同名 `_06_R60Item_...（複数行、アップロード）.xlsx` | 同名 `_S01_R60ItemSup_...xlsx` |
| 前端 | `views/R60Item.vue`（3,778 行） | `views/R60ItemMulti.vue`（9,752 行） | `components/R60ItemSup.vue`（715 行） |
| service | `R60ItemService.ts`（106 行） | `R60ItemMultiService.ts` | `R60ItemSupService.ts` |
| 后端 | `R60ItemController.py`（8,715 行） | `R60ItemMultiController.py`（11,861 行） | `R60ItemSupController.py`（797 行） |
| AB 报告 | `reports/R60Item/` | `reports/R60ItemMulti/` | 无独立目录 |

### 5.2 学习重点（按子单元拆）

**子单元 A：`R60Item` 单品维护**
- 164 个字段的组织方式；分组、必填、联动。
- `detail` / `copy` / `search`（itemCd / 全件）/ `datainit` / `modify`。
- 排他与被参照。

**子单元 B：`R60ItemMulti` 多行 + 上传**
- 多行网格的增删改、行内校验、批量提交。
- CSV 上传：模板、编码、校验、错误行回显。
- 上传样例：`doc/02_INPUT/60.単体テスト/Uploadサンプルファイル/R60_アイテム.csv`。

**子单元 C：`R60ItemSup` 输入支援**
- 作为**部品**被 `R60Item` 调用；参数、返回值、选择结果如何回填。
- 支援画面不是独立画面，**不能单独重做**。

> **复杂度警告**：`R60ItemMulti.vue` 9,752 行 + controller 11,861 行。
> 一次投入必然超上下文。**按子单元 A/B/C 分开抽取**，每个子单元单独完成、单独验收。

### 5.3 完成判据

- [ ] A/B/C 三张卡齐全，且互相有链接
- [ ] `01-fields.yaml` 至少覆盖 164 字段（可分文件）
- [ ] `03-logic.yaml` 覆盖：单品编辑、多行批量、CSV 校验三条主逻辑
- [ ] `05-tests.yaml` 能对应到"複数行、アップロード"单测仕様
- [ ] `06-review.yaml` 记录"复杂功能必须拆分"的实测证据（行数、失败点）

---

## 6. RAG 语料与索引设计

### 6.1 目录

```
D:\AI_work_dev\
  tools\rag\                 # 构建/查询 CLI（新写，纯 stdlib 优先）
    __init__.py
    __main__.py
    chunker.py               # 卡片 → chunk
    build_index.py           # chunk → SQLite FTS5
    query.py                 # 检索 + 引用
  docs\90_knowledge\legacy-r60\
    modules\
      R60Area\  R60Code\  R60Item\
    chunks\                  # 生成的 JSONL（机读，可审查）
  eval\
    gold-qa.yaml             # 50〜100 条金标问答
  reports\rag\
    eval-<date>.json         # 检索评测结果
  build\rag\r60.sqlite       # 索引（gitignore）
```

### 6.2 chunk 单位（按语义切，不按文件切）

| `artifact_type` | 切分单位 | 例子 |
|-----------------|----------|------|
| `screen` | 1 个画面 | `R60Area` 画面概要 |
| `field` | 1 个字段或 1 个字段组 | `araCd` 的定义 |
| `api` | 1 个 actionId / 端点 | `search` 请求参数 |
| `logic` | 1 条业务规则或 1 个分支 | 排他检查 |
| `error` | 1 个错误 | E-002 |
| `test` | 1 个 TC / 1 个测试观点 | 境界値：0 件 |
| `convention` | 1 条规约条款 | 命名规则 |
| `review` | 1 条差异/评审意见 | D-xx |

> **一条 chunk 只讲一件事**。跨文档的综合结论放在卡片里，不塞进单个 chunk。

### 6.3 chunk schema（固定字段）

```yaml
chunk_id: R60Area:logic:edit:exclusive
module: R60Area
artifact_type: logic
ids: [L-015, D-043]          # 可为空，但能对上就必须写
title: "編集時の排他チェック（KSN_DAT / REV_NO）"
source_path: "D:/AI_work/doc/02_INPUT/50.設計書/...05_R60Area....xlsx"
source_locator: "sheet=業務処理説明; row=42"
sensitivity: internal
corpus_scope: teaching       # teaching=教材 / holdout=考题，绝不混用
text: "..."
sha256: "..."
version: 0.1.0
```

### 6.4 索引技术选择

**第一版：SQLite FTS5 + `tokenize='trigram'` + BM25。**

理由：
- 纯标准库（`sqlite3`），无外部依赖，可在专线环境运行（规则 00 §13）。
- **确定性**：同样语料每次构建结果一致（规则 03 §7.1）。
- **可审查**：每条结果都能回指 `chunk_id` 与 `source_path`。
- 中日文用 **trigram** 分词，避免依赖词典分词器。

**第二版（评测通过后再做）**：混合检索 = BM25 + embedding。
只有在 BM25 的 recall@5 不达标时才引入；不先上向量库。

### 6.5 防答案泄漏（最重要的一条）

`R60Login` 作为考题时，**实现侧绝不能进入检索语料**。做法：

1. 语料按 `corpus_scope` 分区：`teaching`（3 模块）/ `holdout`（Login）。
2. **构建两个独立索引**：`build/rag/r60-teaching.sqlite`、`build/rag/r60-holdout.sqlite`。
3. 练习期只允许查询 `teaching` 索引；`holdout` 索引在节点 8 之后才由 `drill-comparator` 打开。
4. Login 的**设计书**可以进 `teaching`（它是输入，不是答案）；**`.vue` / `.py` 实现**只能进 `holdout`。

> 这条规则的实质：**RAG 不能把答案喂给考生**。
> 如果做不到，Login 练习的对比结论作废（参见 `phase0-closure.md` §5）。

---

## 7. 金标问答与评测

### 7.1 题目配比（目标 80 题）

| 模块 | 题数 | 题型 |
|------|------|------|
| `R60Area` | 20 | 事实型（字段/端点/错误）+ 规则型（排他/排序） |
| `R60Code` | 25 | 主从关系、`simKbn`、AB 404 解释 |
| `R60Item` | 35 | 字段群、多行上传、输入支援、拆分策略 |

**题型三类**：
1. **事实型**：答案在一处，能直接引用。
2. **规则型**：答案在"業務処理説明"里，需要读懂条件。
3. **跨文档型**：需要同时引用设计书 + 单测仕様 + 差异登记。

### 7.2 金标格式

```yaml
- qid: GQ-AREA-001
  module: R60Area
  type: fact
  question: "エリアマスタの検索で許可されるソート項目は？"
  expected_chunk_ids: [R60Area:logic:search:sort]
  expected_answer: "CMP_CD / JIG_CD / ARA_CD の 3 項目。外は JIG_HYJ_SEQ + ROWID にフォールバック。"
  must_cite: true
```

### 7.3 验收阈值

| 指标 | 阈值 | 说明 |
|------|------|------|
| **recall@5** | **≥ 80%** | 正确 chunk 出现在前 5 条 |
| **citation accuracy** | **≥ 90%** | 回答引用的 chunk 确实支持该回答 |
| **unsupported answer rate** | **= 0** | 检索不到时必须说"知识库中没有"，不得编造 |
| **per-module recall@5** | 每模块 ≥ 75% | 防止某个模块被平均分掩盖 |

评测命令（计划）：

```bash
py -3 -m tools.rag build --scope teaching
py -3 -m tools.rag eval --gold eval/gold-qa.yaml --report reports/rag/eval-2026-10-19.json
```

---

## 8. RAG 如何接回 8 工程

| 节点 | 检索什么 | 用途 |
|------|----------|------|
| n01 要件理解 | 业务术语、画面概要、同类模块的既有要求 | 把客户语言映射到业务对象 |
| n02 基本設計 | 画面卡、字段词典、画面规约 | 生成 F/I，避免漏项 |
| n03 詳細設計 | 逻辑卡、错误卡、DB 定義 | 生成 L/D/E，补齐边界 |
| n04 框架構築 | 共通部品、技术规约 | 选型与复用 |
| n05 製造 | **仅 `teaching` 索引中的同类实现模式** | 生成代码；不得检索同画面答案 |
| n06 単体テスト | 测试观点卡、单测仕様 | 生成 TC |
| n07 結合テスト | API 契约卡、AB 报告 | 设计 API 序列与对比 |
| n08 リリース | 差异卡、运行规约 | 写已知限制与运维注意事项 |

**上下文注入方式**：每节点产出一个 `context_bundle.json`：

```json
{
  "node": "n03",
  "module": "R60Area",
  "query": "編集時の排他チェック",
  "chunks": [{"chunk_id": "...", "text": "...", "source": "..."}],
  "token_estimate": 3200
}
```

**不把整个知识库塞进提示词**。只注入检索命中的 5〜10 条 chunk，并保留出处。

---

## 9. 与领导 PPT 四层的对应

| PPT 层 | 本计划中的落点 | 本轮是否做 |
|--------|----------------|------------|
| 接入层（Prompt 模板 / 权限 / 审计） | 节点 prompt 模板 + `context_bundle` + 检索日志 | ✅ 节点模板复用现有 |
| 能力编排层（Agent 工作流） | 现有 node1〜node8 agents | ✅ 复用，不改 |
| 知识库层（RAG） | `tools/rag` + `modules/` + `chunks/` | ✅ **本轮核心** |
| 模型网关层（路由 / 脱敏 / 成本 / 质检） | `tools/gateway` 薄封装 | ⏳ RAG 评测通过后 |
| KPI | recall@5 / citation / 返工率 | ✅ 本轮先测前两项 |

> **顺序不可颠倒**：先有知识库并证明检索有效，再谈网关和编排。
> 没有语料就建网关，只会得到一个"能调用模型但不知道喂什么"的空壳。

---

## 10. 执行排期（8 周，按可交付物而非按文档页数）

| 周 | 交付物 | 验收 |
|----|--------|------|
| W1 | `R60Area` 7 类卡片 + chunk schema 定稿 | Area 卡片齐全，chunk 可生成 |
| W2 | `R60Code` 家族卡片 | 主从关系表 + 404 解释 |
| W3 | `R60Item` 子单元 A（单品） | 164 字段词典 |
| W4 | `R60Item` 子单元 B/C（多行、支援） | 上传校验链 + 支援回填 |
| W5 | `tools/rag` 构建 + 索引 + 80 题金标 | recall@5 ≥ 80% |
| W6 | `context_bundle` + 节点 1〜3 试跑 | 产物可复核，不靠闲聊 |
| W7 | 节点 4〜8 试跑 + 修复检索缺口 | 至少一轮完整链路 |
| W8 | `R60Login` 考题（实现隐藏） | 需求只从设计书重建 |

> W6〜W8 是"用起来"的阶段，不是"再写文档"的阶段。
> 每周的验收物必须是**可执行的命令输出或可引用的卡片**，不是"已完成"三个字。

---

## 11. 明确不做

1. **不重写** R60Area / R60Code / R60Item 的代码。
2. **不把实现代码整段搬进语料**；只摘结论 + 出处。
3. **不把 `migration` 写进默认骨架**；R60 专属规则留待单独裁定。
4. **不先建模型网关、不先建向量库、不先铺 55 张画面卡**。
5. **不生成 `.xlsx`**（Phase 1 约束不变）。
6. **不修改 `D:\AI_work` 的任何文件**。

---

## 12. 完成判据（本计划整体）

- [ ] 3 个模块 × 7 类卡片齐全，均有出处
- [ ] chunk 总数约 250〜350（Area ~40 / Code ~80 / Item ~150）
- [ ] 80 题金标问答完成
- [ ] recall@5 ≥ 80%，citation accuracy ≥ 90%，unsupported = 0
- [ ] `teaching` / `holdout` 两个索引物理隔离
- [ ] 至少一次 n01〜n08 试跑记录（不要求全部承认，但要求有可复核产物）
- [ ] `py -3 -m tools.trace_check --strict` 退出码 0
- [ ] `D:\AI_work` 无任何写入（可用文件时间戳核对）

---

## 13. 下一步（本周）

**只做 W1：`R60Area`。**

1. `py -3 -m tools.legacy "<Area 设计书>" --list` → 确认 sheet 与规模
2. 逐 sheet 抽取：`画面概要` / `画面項目内容` / `イベント一覧` / `業務処理説明`
3. 对照单测仕様，抽取测试观点
4. 产出 `screens/R60Area.md` 与 `modules/R60Area/*.yaml`
5. 用这 7 类产物试写第一批 chunk（约 40 条）
6. 停下来给人看，**不自动进入 R60Code**

> 停下来的理由：卡片格式如果在 Area 没定对，后面两个模块会把它放大 3 倍。
> 人的一次确认，比 AI 多写 3 份模板便宜。

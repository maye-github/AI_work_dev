# 知识库构建指南（公司级／项目级）

> 面向对日受托开发的 AI 全链路导入，知识库构建的手顺说明。
> 以 1 个新项目为起点，用 4 周时间做出「实际能检索出结果的**最小可用系统**」，
> 项目结束时通过「升格」将其培育为公司级知识。

---

## 目录

0. [本指南的定位](#0-本指南的定位)
1. [设计全景](#1-设计全景)
2. [公司级知识库](#2-公司级知识库)
3. [项目级知识库](#3-项目级知识库)
4. [实现](#4-实现)
5. [以新项目为起点的构建手顺](#5-以新项目为起点的构建手顺)
6. [日程安排](#6-日程安排)
7. [运用（日常・每周・结案）](#7-运用日常每周结案)
8. [反模式](#8-反模式)
9. [附录](#9-附录)

---

## 0. 本指南的定位

| 项目 | 内容 |
|---|---|
| 对象 | 对日受托开发项目的 SE 组长、品质管理负责人、AI 推进负责人 |
| 前提 | 成果物以 AI 生成为前提，采用「机器可读的结构化源」制作（成果物二重化） |
| 到达点 | 在基本设计阶段，AI 能引用项目 KB 中的类似设计输出初稿 |
| 期间 | 基盘构建 4 周（与项目 kickoff 并行） |

---

## 1. 设计全景

### 1.1 基本原则

**以 Git 作为唯一真实源（source of truth），向量索引视为随时可以重建的派生数据。**

这样一来，以下能力无需额外开发即可获得。

- 版本管理・差分评审（Pull Request）
- 权限控制（仓库／目录单位）
- 审计日志（提交历史・审批历史）
- 索引重建（更换模型时只需全量重新 embed）

### 1.2 两层结构

公司级与项目级**不是两套系统，而是同一基盘上的 2 个作用域（namespace）**。

| 观点 | 公司级（company） | 项目级（project） |
|---|---|---|
| 目的 | 可在其他项目复用的资产 | 项目固有的上下文・成果物 |
| 内容 | 规约・术语词典・设计模式・共通组件・模板・实绩值 | 需求・设计・测试・会议纪要・ADR・项目术语 |
| 更新 | 治理后的时机（半年度盘点・升格时） | 成果物每次提交时（即时） |
| 责任人 | KB 责任人（公司级） | 项目 KB 担当（通常为 SE 组长） |
| 品质基准 | 匿名化・通用性・无重复 | 机密区分的准确性・完整性 |
| 寿命 | 永久（版本管理） | 项目结束后 read-only 归档 |

### 1.3 升格流水线

```text
项目级（即时入库・项目闭域）
      │  结案评审 ＋ 匿名化 ＋ 抽象化 ＋ owner 审批
      ▼
公司级（治理・版本管理・评审）
      │  检索（作用域路由）
      ▼
新项目（从公司级开始，逐步积累项目级）
```

> **没有这条流水线，公司级永远是空的。没有匿名化，公司级就会变成信息泄露源。**

---

## 2. 公司级知识库

### 2.1 收录内容

| 类别 | 具体例子 | 粒度 |
|---|---|---|
| 规约・标准 | 编码规约、设计规约、评审观点、测试观点目录 | 条文单位 |
| 术语・领域 | 行业术语词典、日英对照、业务流程类型 | 词单位 |
| 设计模式 | 画面模式、报表模式、I/O 设计雏形、架构类型 | 模式单位 |
| 资产 | 共通组件、CI 配置、成果物模板（机读源＋日文正式版） | 模块单位 |
| 实绩数据 | 估算实绩、工时实绩、品质实绩（按工程） | 汇总值 |

### 2.2 入库基准（品质门禁）

1. **已匿名化** — 不再残留客户名・个人名・固有业务名・金额
2. **通用性** — 已抽象化到可在其他项目复用的形态
3. **无重复** — 与既有资产不重复
4. **有出处** — 在 `source_project` 中记录原项目 ID
5. **已获 owner 审批** — 已在 PR 评审中通过

### 2.3 治理

| 项目 | 内容 |
|---|---|
| owner | 按 `doc_type` 各设 1 名（规约＝品质管理、模式＝架构担当…） |
| 盘点 | 每半年一次。删除或更新已陈旧的内容 |
| 版本管理 | 更新 front matter 的 `version`，通过 PR 管理差分 |
| 禁止事项 | 直接投放客户固有信息（匿名化前的会议纪要等） |

> 没有 owner 的公司级 KB 半年就会陈旧化。必须指定专人。

---

## 3. 项目级知识库

### 3.1 收录内容

| 成果物 | 内容 |
|---|---|
| 需求 | 需求结构化表、待确认事项清单、术语词典 |
| 设计 | 基本设计书・详细设计书（机读源）、项目定义、SQL 清单 |
| 测试 | 测试规格书、测试结果、覆盖率 |
| 判断记录 | ADR（设计判断的记录） |
| 外部输入 | 会议纪要・邮件（**匿名化之后**再投放） |

### 3.2 即时入库

**不是事后整理，而是在生成时点就入库。**

由于成果物二重化，AI 的输出本来就是结构化源（Markdown/YAML＋ID），因此无需重新解析即可直接索引化。揽取流水线需要另行处理的只有外部输入（会议纪要・邮件・日方发来的 Excel）。

### 3.3 元数据

`项目ID / 工程 / 文档种别 / 需求ID / 机密区分 / 版本 / 作成日` 为必填。由此才能成立作用域路由与可追溯性。

---

## 4. 实现

### 4.1 仓库结构

```text
kb/
├── company/                      # scope: company（最初可以为空）
│   ├── standards/coding/general.md
│   ├── glossary/terms.yaml
│   ├── patterns/screen/list-search.md
│   └── templates/basic-design/
├── projects/
│   └── P-2026-001/               # scope: project
│       ├── README.md             # 项目概要・客户・机密区分
│       ├── requirements/         # REQ-*.md
│       ├── design/basic/         # BS-*.md
│       ├── design/detail/        # DS-*.md
│       ├── test/                 # TC-*.md
│       ├── adr/                  # ADR-*.md
│       └── glossary/             # 项目固有用语
├── templates/                    # 成果物模板
├── eval/golden.yaml              # 评估用问题集
└── .kbci/                        # 入库脚本
```

**规则**：1 个项目 = 1 个目录。项目编码遵循既有编号规则（`P-YYYY-NNN`）。成果物必须放在本仓库中。

### 4.2 文档格式（front matter 必填）

```yaml
---
doc_id: BS-001
scope: project
project_id: P-2026-001
phase: basic_design
doc_type: design
confidentiality: internal
req_ids: [R-101, R-102]
version: 1
owner: tanaka
lang: ja
updated: 2026-10-20
---
```

**CI lint 规则**（未填写则不可 merge）

- `doc_id` 必填・仓库内唯一
- `scope` 必填（`company` 时禁止填写 `project_id`）
- `confidentiality` 必填
- `doc_type` 为固定 enum
- 正文不能为空

`doc_type` 的 enum：

```text
requirement | design | test | meeting | adr | standard | pattern | template
```

`phase` 的 enum：

```text
requirements | basic_design | detail_design | framework | coding | unit_test | integration_test | release
```

### 4.3 DB Schema

```sql
CREATE TABLE KB_DOC (
  DOC_ID       VARCHAR2(64) PRIMARY KEY,
  SCOPE        VARCHAR2(10) NOT NULL,      -- company | project
  PROJECT_ID   VARCHAR2(32),
  PHASE        VARCHAR2(32),
  DOC_TYPE     VARCHAR2(32),
  CONF_LEVEL   NUMBER(1)    NOT NULL,      -- 1=public 2=internal 3=confidential 4=client_only
  VERSION_NO   NUMBER(6),
  OWNER_ID     VARCHAR2(32),
  REPO_PATH    VARCHAR2(512),
  CONTENT_HASH VARCHAR2(64),               -- 用于无变更跳过
  UPDATED_AT   DATE
);

CREATE TABLE KB_CHUNK (
  CHUNK_ID     VARCHAR2(64) PRIMARY KEY,
  DOC_ID       VARCHAR2(64) NOT NULL,
  SECTION_PATH VARCHAR2(512),
  ORD_NO       NUMBER(6),
  CONTENT      CLOB NOT NULL,
  EMBEDDING    VECTOR(1024, FLOAT32),      -- Oracle 23ai 的情况
  UPDATED_AT   DATE
);

CREATE INDEX IX_CHUNK_DOC ON KB_CHUNK(DOC_ID);
```

**向量存储的选型判断**

| 环境 | 选择 | 理由 |
|---|---|---|
| Oracle 23ai 及以后 | `VECTOR` 型 ＋ `VECTOR_DISTANCE` | 无需额外中间件 |
| Oracle 19c 及以前 | **用 Qdrant 做 sidecar 部署** | 不要在 19c 上自己实现向量检索 |

### 4.4 入库流水线

```text
1. 用 git diff --name-only 抽出被修改的 .md
2. 解析 front matter
3. 按 doc_type 切分 chunk
4. 每 32〜64 条批量 embed
5. 按 doc_id 单位 DELETE → INSERT（幂等）
6. CONTENT_HASH 相同则跳过
```

- **幂等性必须保证**：先 `DELETE FROM KB_CHUNK WHERE DOC_ID=:doc_id` 再插入。漏掉这一步，每编辑一次文档 chunk 就会重复一份。
- **首次投放**用 `--all` 模式全量，之后只做差分。

### 4.5 Chunk 切分规则

| doc_type | 切分单位 | 备注 |
|---|---|---|
| standard / design（正文） | `##` / `###` 标题 | 在 metadata 中保留 `section_path` |
| design（项目定义表） | **1 行 = 1 chunk** | 不要跨表切分 |
| design（处理流程） | `logic_id` 单位 | |
| test | 测试 ID 单位 | |
| meeting | 议题单位 | 议题标题放入 metadata |

大小 500〜800 token，overlap 10%。

> 表格类文档是最大的失败诱因。把整张表做成 1 个 chunk，就无法回答「类型为 NUMBER(9,0) 的项目有哪些？」这类提问。

> **设计书 Excel 不要重复解析。** 先把既有 `code-from-design-excel` 的解析结果写成 Markdown，再入库（解析品质统一，避免二重实现）。

### 4.6 检索

```python
@router.post("/kb/search")
def search(req, conn=Depends(get_engine_conn)):
    # 权限・作用域下推到 SQL（禁止后置过滤）
    where, params = build_filter(req.user, req.scopes, req.project_id)

    dense = conn.execute(text(f"""
        SELECT c.CHUNK_ID, c.DOC_ID, c.SECTION_PATH, c.CONTENT,
               1 - VECTOR_DISTANCE(c.EMBEDDING, :qv, COSINE) AS score
        FROM KB_CHUNK c JOIN KB_DOC d ON d.DOC_ID = c.DOC_ID
        WHERE {where}
        ORDER BY VECTOR_DISTANCE(c.EMBEDDING, :qv, COSINE)
        FETCH FIRST 50 ROWS ONLY
    """), {"qv": embed(req.text), **params}).fetchall()

    # dense + sparse 做 RRF 融合 → rerank → 带引用返回
    top = rerank(req.text, rrf(dense, sparse), 8)
    return [{"text": t.content, "doc_id": t.doc_id,
             "section": t.section_path} for t in top]
```

**必须做到 3 点**

1. **权限过滤下推到 SQL 内部** — 检索后再过滤会同时造成泄露和 recall 下降
2. **作用域路由** — 型号・规约类 query → company，项目固有用语 → project，无法判断时两边做加权融合
3. **必须 rerank** — 向量 top50 中取前 5 条的精度大致只有 60%。经 rerank 可改善到 85% 以上

### 4.7 权限

| 规则 | 内容 |
|---|---|
| 公司级 | `CONF_LEVEL <= 用户等级` |
| 项目级 | 上述条件 **并且** `PROJECT_ID IN (用户所属项目)` |
| `confidential` / `client_only` | 仅限项目成员 |
| `client_only` | **生成对外提交物时不允许引用**（用标记抑制） |

### 4.8 评估（golden set）

`eval/golden.yaml` 中约 30 题。

```yaml
- q: "在庫引当で在庫不足のときのエラーコードは？"
  expect_doc: DS-001
  expect_section: "エラー処理一覧"
- q: "数値項目の最大桁数の規約は？"
  expect_doc: STD-CODING-001
```

- 指标：以 **recall@5 ≥ 0.85** 为合格线
- 执行时机：变更 chunk 策略・embedding 模型・rerank 时
- 记录日志：`query / 命中的 doc / 是否采纳 / 错误报告`

> 没有 golden set 的 KB 无法判断是否在改善。构建第一天就要准备。

### 4.9 技术选型

| 组件 | 推荐 | 理由 |
|---|---|---|
| 嵌入模型 | **bge-m3** | 日/中/英 一个模型全包。可同时输出 dense + sparse，无需另挂 BM25 |
| 向量存储 | Oracle 23ai VECTOR / Qdrant | 数十万 chunk 规模下上述方案足够 |
| rerank | bge-reranker-v2-m3 | 多语言，CPU 也能跑 |
| 全文检索 | bge-m3 sparse 或 Elasticsearch + kuromoji | **Postgres/Oracle 标准的 FTS 对日语很弱** |

> ⚠️ 用标准 FTS 实现日语全文检索出不了精度。用 bge-m3 的 sparse 向量替代，或者并用带 kuromoji 的检索引擎。

---

## 5. 以新项目为起点的构建手顺

### STEP 0｜确定体制与规则（kickoff 前・1 天）

| 需要决定的事 | 内容 | 成果物 |
|---|---|---|
| KB 责任人（公司级） | 升格可否的最终判断、盘点的主持 | 任命 |
| 项目 KB 担当 | 项目内的入库・品质管理（通常为 SE 组长） | 任命 |
| **机密区分** | `1=public / 2=internal / 3=confidential / 4=client_only` 的定义 | 机密区分表 |
| **KB 对象成果物清单** | 放入什么。**先决定「不放什么」** | 对象清单 |
| 技术选型 | 嵌入模型・向量存储 | 选型备忘 |

> 最先要决定的是「不放什么」。会议纪要里很容易混入客户名・个人名・估算金额。没有排除基准，之后就得全量重新筛查。

**完成条件**：2 名责任人已确定，机密区分表与对象清单已文档化。

### STEP 1｜创建仓库与目录（0.5 天）

按 4.1 的构成创建。

**完成条件**：`kb/projects/P-YYYY-NNN/` 已创建，README 中已有项目概要。

### STEP 2｜固定文档格式（0.5 天）

准备 4.2 的 front matter 模板与 CI lint。

**完成条件**：把没有 front matter 的文件提 PR 时 CI 会失败。

### STEP 3｜创建 DB Schema（1 天）

应用 4.3 的 DDL，确定向量存储。

**完成条件**：针对 `KB_DOC` / `KB_CHUNK` 的 insert / delete / vector search 能正常工作。

### STEP 4｜创建入库流水线（3 天）

实现 4.4・4.5。

**完成条件**：`--all` 能全量投放，同一文件跑两次 chunk 数不会增加。

### STEP 5｜编入 CI（0.5 天）

| 时机 | 要做的事 |
|---|---|
| 创建 PR 时 | 只做 front matter lint（**不 embed**） |
| merge 到 main | 差分入库 |
| 每周 | 全量整合检查（doc_id 重复・孤儿 chunk） |

> 若在 PR 时 embed，评审前的草案就会进入索引成为噪声。

### STEP 6｜创建检索 API（2 天）

实现 4.6。

**完成条件**：对 golden set 的 query，期望 doc 能进入 top5。

### STEP 7｜实现权限（1 天）

实现 4.7。

**完成条件**：通过测试确认权限外的项目 chunk 完全不会出现在检索结果中。

### STEP 8｜创建 golden set（1 天）

整备 4.8，确认 **recall@5 ≥ 0.85**。

### STEP 9｜项目 kickoff 时的手顺（每个项目・0.5 天）

新项目启动时，必须执行以下 7 项。

1. 分配项目编码并创建 `projects/<code>/`
2. 在 `README.md` 中填写客户・期间・机密区分
3. 在 KB 中登记 `project_id`（项目主数据）
4. 把项目固有用语登记到 `glossary/`
5. 从 `templates/` 复制成果物模板
6. 确定客户固有的机密区分（从默认 `3=confidential` 开始）
7. 确定首次投放对象（已有的需求定义书・会议纪要）

### STEP 10｜按工程的持续作业

| 工程 | 投放内容 | 时机 |
|---|---|---|
| 需求理解 | 需求结构化表、待确认事项清单 | 成果物确定时 |
| 基本设计 | `BS-*.md`（机读源） | PR merge 时 |
| 详细设计 | `DS-*.md`、项目定义 | PR merge 时 |
| 制造 | 源码（建议另建索引） | merge 时 |
| 测试 | `TC-*.md`、结果报告 | merge 时 |
| 全工程 | ADR（设计判断的记录） | 每次判断时 |

> **铁则：与成果物的提交放在同一个 PR 里。** 往后拖一定会堆积。

### STEP 11｜日常・每周运用

| 频率 | 作业 | 耗时 |
|---|---|---|
| 每日 | 确认入库错误（CI 通知） | 5 分钟 |
| 每周 | 检测未提交成果物、处理错误报告、golden set 回归 | 30 分钟 |
| 每月 | 命中率・采纳率的评审 | 1 小时 |

### STEP 12｜结案与升格到 company（项目结束时・2 周）

1. **结案评审会**（1 小时）：抽出有复用价值的设计判断・模式・术语
2. **匿名化・抽象化**：把客户名・固有业务名一般化
   （例：`A公司的受注处理` → `受注处理的共通模式`）
3. **owner 评审**：KB 责任人在 PR 中审批
4. **升格**：`git mv projects/<code>/... company/...` 并把 front matter 改为 `scope: company`
5. **项目库转为 read-only**：作为归档处理，之后只读

**升格检查**

| 条件 | 确认内容 |
|---|---|
| 匿名化 | 不再残留客户名・个人名・金额 |
| 通用性 | 已成其他项目可用的形态 |
| 重复 | 与既有 company 资产不重复 |
| 出处 | 在 `source_project` 中保留原项目 ID |

---

## 6. 日程安排

| 周 | 作业 |
|---|---|
| 第 1 周 | STEP 0〜2、STEP 4 的设计 |
| 第 2 周 | STEP 3〜5（到首次投放为止） |
| 第 3 周 | STEP 6〜7（检索 API・权限） |
| 第 4 周 | STEP 8（golden set）＋ 试点验证 |

**整体完成条件**：在基本设计阶段，AI 能引用项目 KB 中的类似设计输出初稿。

---

## 7. 运用（日常・每周・结案）

### 7.1 日常

- 确认 CI 的入库失败通知（5 分钟）
- 失败的典型原因：front matter 不完整、表格崩坏、embedding API 限流

### 7.2 每周

- 检测未提交成果物：成果物是否被创建在仓库之外
- 处理错误报告：受理「AI 引用了旧设计」等报告
- golden set 回归：动过 chunk 策略的那一周必须执行

### 7.3 每月

- 命中率・采纳率的评审
- 抽出低命中的 query，定位术语词典的不足与 chunk 切分的问题

### 7.4 结案

执行 STEP 12。项目库作为 read-only 归档保留。

---

## 8. 反模式

| # | 反模式 | 结果 |
|---|---|---|
| 1 | 把过去所有项目一次性投放 | 噪声导致精度下降，无法评估 |
| 2 | 整篇原样 embed | 大段落被反复返回。必须 chunk |
| 3 | 检索后才过滤权限 | 泄露且 recall 下降 |
| 4 | 没有 front matter 就入库 | 出处和权限都无从追溯 |
| 5 | 没有 owner 的 company 库 | 半年就陈旧化 |
| 6 | 未匿名化就升格客户固有信息 | 向其他项目泄露信息 |
| 7 | 每次都全量解析设计书 Excel | 解析品质参差・二重实现 |
| 8 | 用标准功能实现日语 FTS | 出不了检索精度 |

---

## 9. 附录

### 9.1 front matter 模板

```markdown
---
doc_id:
scope: project              # company | project
project_id:                 # scope=company 时不填写
phase:                      # requirements | basic_design | detail_design | framework | coding | unit_test | integration_test | release
doc_type:                   # requirement | design | test | meeting | adr | standard | pattern | template
confidentiality: internal   # public | internal | confidential | client_only
req_ids: []
version: 1
owner:
lang: ja
updated:
source_project:             # 升格时记录原项目 ID
---

# （标题）

## 1. 概要
## 2. 详细
```

### 9.2 项目 kickoff 检查清单

- [ ] 已分配项目编码
- [ ] 已创建 `projects/<code>/`
- [ ] README 中已填写客户・期间・机密区分
- [ ] `project_id` 已登记到项目主数据
- [ ] 项目固有用语已登记到 `glossary/`
- [ ] 已复制成果物模板
- [ ] 已确定机密区分
- [ ] 已确定首次投放对象
- [ ] 已任命项目 KB 担当

### 9.3 结案检查清单

- [ ] 已实施结案评审会
- [ ] 已抽出升格候选
- [ ] 已完成匿名化・抽象化
- [ ] 已获 KB 责任人审批
- [ ] 已用 `git mv` 移动到 company 下
- [ ] 已把 front matter 改为 `scope: company`
- [ ] 已记录 `source_project`
- [ ] 已把项目库设为 read-only

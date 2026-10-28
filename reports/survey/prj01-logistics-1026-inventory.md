# PRJ01 Logistics — 全部内容与层级关系说明

> **测点**：`D:\AI_work_dev2\prj01-logistics-main-1026`，2026-10-26 实测。
> **190 个文件 / 1.8MB**。本文只读不改——那个文件夹一个字节都没动。
> 结构照 `docs/90_knowledge/repo-inventory.md`（AI_work_dev 的同类文档），便于并排比较。

---

## 1. 这是什么

README 自述：**「对日开发全 AI 链路的可行性验证项目」**。
一条对日 SI 的**七阶段流水线**（要件定義 → 基本設計 → 詳細設計 → 製造 → 単体テスト → 結合テスト → リリース/保守），
以 **13 个 Claude Code Skill** 实现，配 6 个 Python 脚本。

业务对象：**メーカーマスタメンテ（R60Maker）的检索画面**——一个单画面、后端 4 个接口规模的实装。

两条自述的硬约束：

1. **推进只能靠人敲命令。** 11 个 skill 设了 `disable-model-invocation: true`，AI 无法自动进下一阶段。
2. **`requirements/raw/` 与 `registry/MASK_MAP.yaml` 不入库**（日方机密原文 / 脱敏对照表），`.gitignore` 已排除。

---

## 2. 一张图

```
prj01-logistics-main-1026/
├── README.md            1.3KB  入口（「先读使用手册」）
├── 使用手册.md          45KB   13 个 skill 的用法 + 六条通用规则 + 已知缺口
├── AGENTS.md            4.3KB  ID 规则・人工卡点・禁止事项（规则的真源）
├── .gitignore           1.0KB  机密排除 + 生成物排除
│
├── .claude/             284KB
│   ├── settings.json           allow 清单（很长）+ PostToolUse hook + additionalDirectories
│   ├── hooks/check_artifact.py PostToolUse：写完成果物自动跑 checkrefs（不阻断）
│   └── skills/ ×13           每个阶段一个 skill，各带 references/（schema + rules）
│
├── requirements/        124KB  ★阶段的机读成果物（5 个 YAML）
│   ├── REQ-要件定义.yaml        46 条要件
│   ├── QST-日方确认事项.yaml    24 条
│   ├── ASM-前提假设.yaml        8 条
│   ├── ISS-未决事项.yaml        6 条
│   └── CHG-变更一览.yaml        1 条
│
├── designs/             332KB
│   ├── basic/  FLD/FNC/IF/SCR/TBL 五个一览（汇总）+ fnc/PRJ01-FNC-0001..0016（单功能设计）
│   └── detail/ DSN×2 + LGC×7 + ERR/IF/TBL物理/TC单测观 四个一览（共 13）
│
├── registry/ID_REGISTRY.yaml   72KB  3184 行，186 个 ID（脚本唯一写入口）
│
├── src/                 264KB  ★代码与两个"管理文档"
│   ├── TECH_STACK.yaml        技术栈声明（FastAPI + Vue3 + PostgreSQL16）
│   ├── TRACEABILITY.yaml      设计ID→逻辑ID→源码文件 的对照表
│   ├── backend/   FastAPI 32 个 py，1832 行
│   └── frontend/  Vue3 + TS + Element Plus + Pinia，16 个文件，339 行
│
├── tests/unit/backend/  81KB   21 个 py，1530 行（pytest，含 Fake 仓储）
│
├── scripts/             188KB  6 个脚本 3661 行 + README
│   registry / checkrefs / impact / checkmanual / mask / export
│
├── samples/             384KB  ★21 个 Excel/Word（对外日文正式版的样例）
├── release/             0      只有 .gitkeep（阶段 7 未开始）
└── requirements/raw/    ——     **不存在**（gitignore 且当前副本没有）
```

---

## 3. 件数与容量

| 领域 | 文件数 | 容量 | 性质 |
|---|---|---|---|
| 根目录文档 | 4（README/使用手册/AGENTS/.gitignore） | 51KB | 人读 + 规则 |
| `.claude/skills` | 36 | 272KB | 13 个 skill（SKILL.md ＋ references ＋ 少量脚本） |
| `.claude` 其他 | 2（settings.json、hooks/check_artifact.py） | 12KB | 权限・钩子 |
| `requirements/` | 6（5 YAML ＋ .gitkeep） | 124KB | 要件阶段的机读成果物 |
| `designs/basic/` | 21（5 汇总 ＋ 16 单功能） | 188KB | 基本设计成果物 |
| `designs/detail/` | 13（2 DSN ＋ 7 LGC ＋ 4 汇总） | 144KB | 详细设计成果物 |
| `registry/` | 1 | 72KB | **ID 台账（唯一发号口）** |
| `src/` | 51（含 pyproject/package.json 等） | 264KB | 源码 ＋ TECH_STACK ＋ TRACEABILITY |
| `tests/` | 21 | 81KB | 单测代码 |
| `scripts/` | 7（6 py ＋ README） | 188KB | 支援工具 |
| `samples/` | 21（xlsx/docx） | 384KB | 对外成果物样例 |
| `release/` | 1（.gitkeep） | 0 | 空 |

---

## 4. 当前进度（用他们自己的脚本实测，只读）

```
╔══════════════════════════════════════════════════════════════════╗
  阶段            命令                     状态          成果物
  0 需求取込       /prj01-intake           ⏸ 未开始       —
  1 要件理解       /prj01-requirement      ✅ confirmed   REQ 46 / QST 24 / ASM 8 / ISS 6
  2 基本设计       /prj01-basic-design     ✅ confirmed   FNC 16 / SCR 2 / FLD 26 / IF 21 / TBL 1
  3 详细设计       /prj01-detail-design    ✅ confirmed   DSN 2 / LGC 7 / ERR 4 / TC观 41
  4 编码           /prj01-coding           ▶ 进行中       后端 32 / 前端 16 / 单测代码 21
  5 单体测试       /prj01-unit-test        ⏸ 未开始       —
  6 结合测试       /prj01-integration-test ⏸ 未开始       —
  7 发布运维       /prj01-release          ⏸ 未开始       —

  阻塞项：无
  脱敏：未初始化（原始素材 0 个文件）
  门禁：⏸ 尚未开始 —— requirements/raw/ 是空的
╚══════════════════════════════════════════════════════════════════╝
```

> **注意这个自相矛盾**：阶段 0 显示「未开始」，但阶段 1〜3 显示「confirmed」。
> 原因是 **`requirements/raw/` 不在这个副本里**（`.gitignore` 排除，且没被复制过来）。
> 接手的人看到的第一个画面会是「从头开始」，而实际上下游已经做完三段。见 §12-1。

---

## 5. `.claude/` —— 13 个 skill

**结构统一**：每个 skill 一个目录，`SKILL.md` ＋ `references/`（该阶段的输出 schema、规则清单），
个别带 `scripts/`。**11 个设了 `disable-model-invocation: true`**，只有 `pipeline` 和 `knowledge` 允许 AI 自动调用。

### 5.1 阶段 skill（7 个）

| # | skill | 干什么 | 输入 → 输出 |
|---|---|---|---|
| 0 | `prj01-intake` | 需求取込。把 docx/xlsx/pdf/png/txt/口头 归一 | 素材 → `requirements/raw/raw_requirements.md`（带来源锚点） |
| 1 | `prj01-requirement` | 要件定义 | 归一后的原始需求 → `requirements/{REQ,QST,ASM,ISS}.yaml` |
| 2 | `prj01-basic-design` | 基本设计 | 要件 YAML → `designs/basic/`（5 个一览 ＋ `fnc/` 16 个单功能） |
| 3 | `prj01-detail-design` | 详细设计 | 基本设计 → `designs/detail/`（DSN/LGC/ERR/IF/TBL物理/TC观） |
| 4 | `prj01-coding` | 编码 | DSN → `src/` ＋ `tests/` ＋ `src/TRACEABILITY.yaml` |
| 5 | `prj01-unit-test` | 单体测试 | DSN → 测试仕样书 → 执行 → 回填实测与覆盖率，NG 登记障害 |
| 6 | `prj01-integration-test` | 结合测试 | 业务场景 → 结合测试仕样书 ＋ 受入条件对照表 |
| 7 | `prj01-release` | 发布运维 | 版本 → Release Note・运维手册・障害对应手册 ＋ 对外日文脱敏 |

### 5.2 横切 skill（6 个）

| skill | 干什么 | 为什么单独存在 |
|---|---|---|
| `prj01-pipeline` | **流程总控（只读）**：扫成果物与台账，判定进度、列阻塞、给下一步命令 | 唯一「可以随便问」的入口 |
| `prj01-approve` | **阶段承认**：汇总统计与疑点 → 人确认 → 批量把 status 改 confirmed 并同步台账 | 把「承认」这个人的动作做成一个可审计的批量操作 |
| `prj01-change` | **变更管理**：登记变更 → 顺追溯链算受影响的下游 → 标失效 → 定向重做 | 把「返工」从口头变成有 ID 的记录 |
| `prj01-registry-check` | **台账校验**：跑 checkrefs 23 条规则 ＋ 脱敏检查，ERROR 为 0 才能冻结 | 阶段冻结前的闸门 |
| `prj01-knowledge` | **对日行业知识库**：术语对照・常见事故点・日文书写法・SI 惯例 | 各阶段产出前读它；**是行业经验，不是日方规格**（冲突时以日方资料为准） |
| `prj01-intake` 的 `scripts/extract.py` | 文档抽取（docx/xlsx/pdf/png） | 阶段 0 的机械部分 |

### 5.3 `settings.json` 与钩子

- `permissions.allow`：一长串（约 60 条）。**大部分是开发过程中一次性命令被逐条批准后累积下来的**，
  其中还残留真实路径（`D:\AI_New_Work\PRJ01-logistics`、`D:\JET\資料\...`、具体客户文件名的 cp/extract 命令）。
  → 见 §12-9。
- `additionalDirectories` 指向上述两个外部目录（开发时需要跨目录读）。
- `hooks.PostToolUse`（matcher `Write|Edit|NotebookEdit`）→ `.claude/hooks/check_artifact.py`：
  写完成果物后自动跑 `scripts/checkrefs.py`，**故意始终 exit 0**（先写成果物、后登记台账是正常顺序，
  阻断会让人没法干活）。真正的闸门在 `/prj01-registry-check` 和 `/prj01-approve`。

---

## 6. 成果物的解剖（所有 YAML 都一样）

每个成果物 YAML 是**两个 YAML 文档**，用一个 `---` 分隔：

```yaml
---                                    ← 第 1 文档：front matter
id: PRJ01-LGC-0001
type: LGC
title: メーカー検索条件の組立 ロジック
status: confirmed                      ← draft / reviewed / confirmed / frozen / deprecated
version: v0.1
related_ids: [ ... 25 个 ... ]         ← 追溯的载体（影响分析靠它）
owner: liyingming
created_at: 2026-10-15
updated_at: 2026-10-15
human_review_required: true            ← 人工卡点的机械标记
basic_design_ref: designs/basic/fnc/PRJ01-FNC-0002.yaml
---
logic:                                 ← 第 2 文档：正文
  ...
```

> **与 AI_work_dev 的关键差异**：AI_work_dev 的规则 02 §5.1 明令「`.yaml` 只能有开头 1 个 `---`，
> 收尾不许再写」（否则 `yaml.safe_load` 报 ComposerError）。本项目**故意用双文档**，
> 因此所有脚本必须用 `safe_load_all`，且不能用 `safe_load` 读这些文件。
> 两个骨架在这一点的约定相反——**不能直接互相搬运。**

---

## 7. `requirements/` 与 `designs/` 的对应关系

```
REQ 46 ─┬─ QST 24（日方确认事项，挂在具体 REQ 上）
        ├─ ASM  8（前提假设）
        └─ ISS  6（未决事项，block: true 的会挡住下一阶段）
                │
                ▼
        FNC 16（机能一览）× 16 个「单功能设计」  ← fnc/PRJ01-FNC-0001..0016.yaml
        SCR  2（画面一览）
        FLD 26（项目定义：画面项目 + 表项目）
        IF  21（接口一览：`code: IF-01..IF-21`，**没有独立 ID**）
        TBL  1（表定义）
                │
                ▼
        DSN 2（详细设计：初期表示 / メーカー検索 / 仕掛表示検索 分册）
        LGC 7（处理逻辑：检索条件组立・分页・权限・格式检查…）
        ERR 4（消息一览）
        IF（接口项目定义：逐个接口的字段）
        TBL（物理设计）
        TC观 41（单测观点）
                │
                ▼
        src/backend（logic 7 个文件 ← LGC）+ src/frontend + tests/
                │
                ▼
        src/TRACEABILITY.yaml（design_id → logic_ids → test_viewpoints → source_files）
```

---

## 8. `registry/ID_REGISTRY.yaml`（3184 行）

| 项 | 实测 |
|---|---|
| 登记 ID 总数 | **186**（confirmed 177 / draft 9） |
| 按类型 | REQ 46・QST 24・FLD 26・TC 41・FNC 16・ASM 8・LGC 8・ISS 6・DSN 4・ERR 4・SCR 2・CHG 1 |
| 未发放 | BUG 0・REL 0（`sequences.next` 仍是 1） |
| 结构 | `meta`（含 `management_docs`：TECH_STACK・TRACEABILITY）/ `sequences`（各类型的下一个号）/ `ids[]` / `freezes[]` |
| 写入口 | **`scripts/registry.py` 独占**。文件头明写「手工编辑会破坏序号一致性」 |

ID 规格：`PRJ01-<类型码>-<4位序号>`，14 个类型码，**永不复用**，废弃标 `deprecated`。

---

## 9. `src/` —— 真实代码

| 部位 | 规模 | 内容 |
|---|---|---|
| `backend/` | 32 个 py・1832 行 | `api/routers/maker_master.py`（99 行）、`service/`（init 121 行・maker_search 182 行）、`logic/` 7 个（67/39/99/52/46/21/89 行）、`repository/` 3 个、`core/`（config/errors/messages/response）、`schemas/` |
| `frontend/` | 16 个・339 行（src 下） | `views/MakerSearchView.vue` 214 行、`api/`（http.ts・makerMaster.ts）、`stores/makerSearch.ts` 61 行、`types/`、`utils/message.ts`＋`.test.ts` |
| `TECH_STACK.yaml` | 管理文档 | FastAPI + SQLAlchemy 2 + Pydantic v2 + Alembic / Vue3 + Element Plus + Pinia + Vite / **PostgreSQL 16、时区 Asia/Tokyo** |
| `TRACEABILITY.yaml` | 管理文档（229 行，status: draft） | 3 个功能的 design_id → logic_ids → test_viewpoints → source_files；含 `unimplemented`・`extra` 两栏（**主动记录「设计了但没写」和「写了但没设计」**） |

> **`TECH_STACK` 与 `TRACEABILITY` 不占业务 ID 号段**，登记在 `ID_REGISTRY.yaml` 的 `meta.management_docs` 里。
> 这是本项目一个值得学的设计：**「管理文档」不是成果物，不该吃 ID。**

---

## 10. `tests/`

21 个 py・1530 行。`tests/unit/backend/app/` 下按层镜像 `src/`（api / logic / repository / service），
另有 `conftest.py` 与 `test_maker_search_service_pending.py`（**差分设计的单测**：验证 `pending_only=true`
在件数检查与本检索两处都生效）。

> **没有 `tests/integration/`。** 结合测试阶段未开始，此目录尚不存在（使用手册把它列为将来位置）。

---

## 11. `scripts/` —— 6 个脚本 3661 行

| 脚本 | 行数 | 职责 | 分类 |
|---|---|---|---|
| `registry.py` | 896 | **ID 台账唯一写入口**：原子分配・幂等・批量改状态・废弃・冻结・校验 | 流程骨架 |
| `checkrefs.py` | 326 | 成果物 ↔ 台账 交叉校验（**23 条规则**），已被 PostToolUse hook 自动调用 | 流程骨架 |
| `impact.py` | 328 | 变更影响分析：顺追溯链算下游 | 流程骨架 |
| `checkmanual.py` | 372 | 文档一致性检查（防「正文改了、边角没跟上」） | 工程自检 |
| `mask.py` | 561 | 脱敏：识别 / 代号化 / 还原 / 泄漏检查（`registry/MASK_MAP.yaml`） | 交付物支撑 |
| `export.py` | 1178 | 成果物 → 对外日文 Excel / Word（`export/`，已 gitignore） | 交付物支撑 |

**共同约定**：默认 dry-run，`--write` 才落盘；`python -I -X utf8` 执行（隔离模式 + 强制 UTF-8）。

---

## 12. 现状问题（清点结果）

| # | 问题 | 实测 | 影响 |
|---|---|---|---|
| 1 | **阶段 0 显示未开始，但 1〜3 已 confirmed** | `requirements/raw/` 不存在（gitignore ＋ 未随副本复制） | 接手的人第一眼以为从头开始；门禁也判「尚未开始」 |
| 2 | **16 个文件的 `id` 不在文件名里** | 汇总文件借用本类型首个 ID（`REQ-要件定义.yaml → PRJ01-REQ-0001` 等） | 按 ID 找文件时找错 |
| 3 | **3 个 ID 被多个文件共用** | `FLD-0001` 出现在 3 个文件（项目定义/表定义/表物理设计）；`FNC-0001` 3 个；`FNC-0002` 2 个 | 台账里 1 个 ID 对应多份成果物，追溯与影响分析会含糊 |
| 4 | **DSN 文件名与内含 ID 不对应且对调** | `DSN/PRJ01-FNC-0001.yaml` → `id: PRJ01-DSN-0002`；`…FNC-0002.yaml` → `DSN-0001` | 极易搞反 |
| 5 | **接口没有 ID 类型码** | `IF-01..IF-21` 只是文件内 `code`，且复用所属功能的 ID（21 条分布在 7 个功能 ID 上） | 接口无法单独追溯、无法单独变更 |
| 6 | **`samples/` 是孤儿** | 21 个 xlsx/docx，全仓 0 处引用 | 不知是样例、是产物、还是客户给的；且会让人误以为是对外正式交付物 |
| 7 | **5 个 `.gitkeep` 与真实文件并存** | designs/ release/ requirements/ src/ tests/ | 只是噪音（release/ 确实需要） |
| 8 | **构建产物未排除** | `src/frontend/tsconfig.tsbuildinfo` | 不该入库 |
| 9 | **`settings.json` 残留真实环境信息** | allow 清单里约 60 条一次性命令，含 `D:\JET\資料\…` 真实客户路径与文件名、`D:\AI_New_Work\…`、`additionalDirectories` 指向外部目录 | **属机密面**。这份文件若外发/入库，等于泄露客户资料结构 |
| 10 | **使用手册自述的 4 条已知缺口** | ①日文术语一致性无检查 ②3 个产物（`designs/basic/fnc/*`、`IF-接口项目定义`、`tests/integration/TR`）声明了产出但无 schema，导不出 Excel/Word ③端到端没跑过真实数据 ④`related_ids` 靠人记，`impact.py` 只能靠正文引用兜底 | 前两条会直接影响 §11 的 `export.py` |
| 11 | **两个 `---` 的 YAML** | 全部 41 个成果物文件都是双文档（requirements 5 ＋ designs 34 ＋ src 2） | 与 AI_work_dev 的规则相反（§6），互相搬运会炸 |

---

## 13. 与 `D:\AI_work_dev`（你的骨架）的对照

| 观察角 | AI_work_dev | prj01-logistics |
|---|---|---|
| 阶段 | 8 工程 ＋ 旁路环 n09 | 7 阶段（0 需求取込 起算共 8 个） |
| 阶段驱动 | 1 个 coach skill（`trans-cosmos-ai-lifecycle-coach`）＋ 9 个 node 执行体 agent | **13 个阶段 skill**，无 agent 层 |
| 谁能推进 | coach 派发 agent，人承认 | **11 个 skill 锁死 `disable-model-invocation`**，只有人能敲命令 |
| 进度状态 | `docs/00_plan/coach/<module>/nNN.yml`（1 节点 1 文件） | **成果物 front matter 的 `status` ＋ 台账**，由 `stage_status.py` 现算 |
| 人承认 | `approved_by` 写人 | `/prj01-approve` 批量改 `status: confirmed` ＋ 同步台账 |
| ID | `R/F/I/D/L/E/TC` ＋ `CR/BUG`，格式 `R-101` | `PRJ01-<14 种类型码>-0001` |
| 门禁 | `trace_check` 6 道 ＋ seal ＋ freeze | `checkrefs` 23 条规则 ＋ `registry verify` ＋ `checkmanual`（写盘后 hook 自动跑） |
| 对外成果物 | `gen_formal` 出 xlsx（限 `reports/`） | `export.py` 出 Excel/Word（`export/`）＋ `samples/` 样例 |
| 机密 | `masking` ＋ gate6 ＋ `.claude/rules/01` | `mask.py` ＋ `MASK_MAP.yaml` ＋ `raw/` gitignore |
| 文档语言 | 日文 `.md` ＋中文 `.zh.html` | **中文 Markdown** ＋日文 schema／标题（`要件定义`・`機能一覧`） |
| 模板/样例 | `docs/10〜80` 的 `*-template` ＋ R-101 见本 | `samples/` 的 21 个 xlsx/docx |
| 现状 | 8/8 承认（演练走完） | 阶段 1〜3 confirmed，阶段 4 进行中 |

**两边最值得互补的三点**

1. prj01 的 **`disable-model-invocation`**：「人不敲命令，AI 推不动」被写进机制，比 AI_work_dev 的「文档约定＋coach 自律」更硬。
2. prj01 的 **`management_docs`**：管理文档不占 ID 号段——AI_work_dev 的 TECH_STACK/TRACEABILITY 等还没有这层区分。
3. AI_work_dev 的 **`node` 执行体（独立上下文）＋ 承认版文档**：prj01 没有 agent 层，长流程时上下文压力会全落在一个 skill 上。

---

## 14. 相关文件

- `D:\AI_work_dev2\prj01-logistics-main-1026\README.md` — 入口
- `D:\AI_work_dev2\prj01-logistics-main-1026\使用手册.md` — 13 个 skill 逐个说明 ＋ 已知缺口
- `D:\AI_work_dev2\prj01-logistics-main-1026\AGENTS.md` — ID 规则・卡点・禁止事项
- `docs/90_knowledge/repo-inventory.md`（本仓库） — AI_work_dev 的同类清点，可并排比较

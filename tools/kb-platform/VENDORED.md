# 这份代码是从哪儿来的

**来源**：`D:\AI_platform\kb-platform`（社内知识库基盤，Phase 0）
**复制日期**：2026-10-28
**原因**：本骨架要往知识库里灌 R60 的知识，但写到 `D:\AI_platform` 是改别的项目，撤不回来。
所以复制一份到本项目里，在本项目内完成接入。

## 复制时做了什么

- **没有复制** `data/kb.sqlite3`（372KB）。那是索引，`ingest` 一条命令就能重建。
- **没有复制** `__pycache__/`、`*.pyc`。
- 其余原样（`kbkit/`、`run.py`、`api.py`、`repo/` 的 7 篇示例、两份构建指南）。

## 这里的代码不是我们写的

**不要按本项目的规矩改它**（commit 7 种格式、7 字段 front matter 等都不适用）。
要改就回到上游 `D:\AI_platform\kb-platform` 改，再同步过来。
**上游是正，这份是抄本。**

## 怎么用

**`repo/projects/P-R60-001/` 就是知识正本，直接编辑，然后建索引。**
2026-10-29 之前链的是另一个方向（`docs/95_legacy/r60/` 为正本、`repo/` 是导出物），
那个方向的导出器 `tools/kb_export` **已停止使用**（运行即返回 2 并说明原因，留作映射规则的参考）。

```bash
# 1. 重建派生物：模块卡的 .md 视图（36 篇）＋ 检索摘要（7 篇）
#    幂等；正本没变时输出一模一样
py -3 -m tools.kb_migrate --apply

# 2. 建索引（差分，没变的不重建）
py -3 tools/kb-platform/run.py ingest --repo tools/kb-platform/repo

# 3. 查
py -3 tools/kb-platform/run.py search "エリアマスタ 排他制御" --repo tools/kb-platform/repo --project P-R60-001 --top-k 5

# 4. 状态 / 评测
py -3 tools/kb-platform/run.py stats --repo tools/kb-platform/repo
py -3 tools/kb-platform/run.py eval  --repo tools/kb-platform/repo
```

检索返回哪些状态，由下面「偏离 1」的 `DEFAULT_RETRIEVABLE` 决定（`active,open,baselined,changed,done`）。
**`draft` 与 `void` 检索不到，这是有意的**——未定稿和作废的知识不该被当成答案。

## 在规格书里是哪一个组件

`AI全链路软件工程平台_实施规格书.md` §11.2 の **组件④「ナレッジベース（RAG）」** 就是它。
按 §11.1 的七层，它同时占 **知識層（内容）** 和 **データ・コンテキスト層（索引）** 两层（§11.1.1 的对应表）。

**检索入口只有这一个。** `tools/rag` 不是第二个知识库，它是这套检索的**回归测试尺**
（§11.2 ⑤「評価・ガバナンス」、§13 KPI⑥「RAG検索のヒット率」），不往里加知识 → `tools/rag/README.md`。

## 依赖

上游声明只依赖 `numpy`。本机原来没装，为跑 `ingest` 装了：

```bash
py -3 -m pip install numpy     # 装的是全局 Python 3.14.3 环境
```

不想要了：`py -3 -m pip uninstall numpy`。但卸载后 `ingest` / `search` 跑不了（`lint` 也跑不了）。

---

## 本抄本对上游的两处偏离（2026-10-29）

上游 `D:\AI_platform` 是正，本文件是抄本。**抄本改了的地方必须记在这里**，否则同步上游时会静默丢失。

### 偏离 1: 可检索状态从固定 `active` 改为可配置

- 改了什么: `kbkit/retrieval.py` 的 `DEFAULT_RETRIEVABLE`（`active,open,baselined,changed,done`，可用环境变量 `KB_RETRIEVABLE_STATUSES` 覆盖）；`kbkit/pipeline.py` 的 `STATUSES` 追加骨架词表。
- 为什么: 旧案件知识搬进本库后，文档的 `status` 用的是骨架状态机（`.claude/rules/02` §6）。上游只认 `active`，直接搬进来会「索引得进、一条也搜不到」；反过来写 `active` 又会让骨架的 `trace_check` gate3 判为「status 値不正」。
- 影响面: 只有本抄本。上游若采纳，改动约 20 行，可原样作为 PR 提交。

### 偏离 2: `repo/projects/P-R60-001/` 是**正本**，不是派生物

- 上游模型: `repo/` 是知识正本，索引是派生物。
- 本抄本: 这一点**与上游一致**。但此前 `docs/95_legacy/r60/` 是正本、`repo/` 是导出物，2026-10-29 已反转——现在 `repo/projects/P-R60-001/` 是唯一正本，**要提交进 git**。
- 已在 `CLAUDE.md` 与 `使用手册.md` 同步。

### 偏离 3: `search()` / `eval` 增加 `module` 与 `scope` 两个筛选口（2026-10-29）

- 改了什么: `kbkit/retrieval.py` 新增 `_filter_candidates()`，`search()` 末尾加 `module=None, scope=None`；
  `run.py` 的 `search` 子命令加 `--module` / `--scope`；`kbkit/eval.py` 把用例里的
  `module` / `scope` 透传给 `search`。
- 为什么: 案件知识集中在一个 `project_id` 下后，`R60User` 的提问会被 `R60SesModel`
  的同型章节抢走（实测 80 题中 3 件是模块串味）。调用方**知道**问的是哪个模块，却**没有口子**告诉检索器。
  公司共通条目（§11.3 会社层）与案件条目也混在一个池里，`STD-TEST-RATIO-001` 会被案件正文挤到 7〜9 位。
- 影响面: **向后兼容**（默认 `None` = 不筛）。上游若采纳，可原样 PR；两个参数不改变任何默认排序。
- 注意: `module` 是 `doc_id` 与 `title` 的**部分一致**。语干相同的别的模块出现时，要补对应表。

### 偏离 4: `kbkit/eval.py` 增加节级判定 `expect_heading`（2026-10-29）

- 改了什么: 用例可选 `expect_heading`，命中结果里 `doc_id` 在 `expect` 内、且 `heading` 部分一致，
  记 `section_hit` / `section_rank`；汇总增加 `section_cases` / `section_recall`，报告打 `§OK(rank=n)` / `§MISS`。
- 为什么: **doc 级判定看不见「模块对了、节错了」。** 实测 12 个带节期望的用例里，
  2 件答案是 `doc` 命中但节在第 8 / 12 位（`top_k=5` 之外），而 doc 级指标仍是 `recall@5=1.000`。
  不修指标就会一直显示「满分」。
- 影响面: 只有本抄本；不加 `expect_heading` 的用例行为完全不变。

### 偏离 5: 目录页不进索引（`company-README.md` / `projects-README.md` 放在 `repo/` 之外）

- 改了什么: 两份说明文件放在 `tools/kb-platform/` 根下，而不是 `repo/company/` 与 `repo/projects/`。
- 为什么: `kbkit/pipeline.py` 的 `collect_docs()` 收 `repo/` 下**全部** `.md`，**没有 README 排除**。
  实测把目录页放进 `repo/company/` 后，它因为列了全部 `doc_id` 与主题词，
  在「テストケースの最低件数」「A/B/C 分類」「出典等級」三问上都排到第 1 位，
  真正写了答案的条目掉出前 5。目录页的职责是指路，不该和它指的内容抢位置。
- 影响面: 只有本抄本的数据组织方式。上游若也想排除目录页，最省事的做法是给 `collect_docs()`
  加一行 `if p.name.upper() == "README.MD": continue`——但**这是行为变更**，需上游自己决定。
- 位置记录: `reports/audit/kb-integration/04_残留问题清单_2026-10-29.md` §1.2。

### 偏离 6: 生成物在 front matter 里自带 `generated_by`（2026-10-29）

- 改了什么: `tools/kb_migrate.py` 的 `merged_fm()` 输出 `generated_by: tools/kb_migrate.py`；
  移设元已消失时，`stamp_existing()` 给既存 `.md` 补这个键（只补键，正文不动）。
- 为什么: `repo/projects/P-R60-001/` 下 79 篇 `.md` 全是派生物，但此前**没有任何标记**，
  看起来像可以手改的正文。手改会在下次 `--apply` 时被静默覆盖。
- 幂等: 2026-10-29 实测连续两次 `--apply`，79 篇的 SHA-256 完全一致。
- 影响面: 只有本抄本。这是**生成器**的改动，不在 `kbkit/` 里。

### 顺带修正: `repo/eval/golden.yaml` 的上游 demo 12 问缺 `project`

上流 demo 的 12 个用例没有 `project:` 字段，检索时只搜 company scope，导致 `eval` 恒为 `recall@5=0.333`。
补上 `project: P-DEMO-001` 后为 `1.000`。**这是上游文件的缺陷，不是我们的知识质量**。

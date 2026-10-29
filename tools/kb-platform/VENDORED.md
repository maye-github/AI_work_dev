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

### 顺带修正: `repo/eval/golden.yaml` 的上游 demo 12 问缺 `project`

上流 demo 的 12 个用例没有 `project:` 字段，检索时只搜 company scope，导致 `eval` 恒为 `recall@5=0.333`。
补上 `project: P-DEMO-001` 后为 `1.000`。**这是上游文件的缺陷，不是我们的知识质量**。

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

```bash
# 1. 把本项目的知识导出成 kb-platform 的格式（会删改 repo/projects/P-R60-001/ 这一棵子树）
py -3 -m tools.kb_export --out tools/kb-platform/repo --promote --check --kb tools/kb-platform

# 2. 建索引（差分，没变的不重建）
py -3 tools/kb-platform/run.py ingest

# 3. 查
py -3 tools/kb-platform/run.py search "エリアマスタ 排他制御" --project P-R60-001 --top-k 5

# 4. 状态
py -3 tools/kb-platform/run.py stats
```

`--promote` 的作用见 `reports/kb-export/README.md`：
kb-platform 的检索**只返回 `status=active` 的文档**，不加这个参数，22 篇都索引得进去但一条也搜不出来。

## 依赖

上游声明只依赖 `numpy`。本机原来没装，为跑 `ingest` 装了：

```bash
py -3 -m pip install numpy     # 装的是全局 Python 3.14.3 环境
```

不想要了：`py -3 -m pip uninstall numpy`。但卸载后 `ingest` / `search` 跑不了（`lint` 也跑不了）。

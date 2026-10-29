# tools/rag —— 检索质量的尺子（不是第二个知识库）

## 它是什么

一个只用 Python 标准库实现的小检索器：读预先切好的摘要 JSONL（`chunk_id / title / text / sha256` 等 12 个字段），
建 SQLite 索引（FTS5 trigram ＋ 字符 n-gram），提供 `build / query / eval / stats / bundle`。

## 它在规格书里的位置

**不是**平台组件。`AI全链路软件工程平台_实施规格书.md` §11.2 の「ナレッジベース（RAG）」是 `tools/kb-platform`；
本工具落在 §11.2 ⑤「評価・ガバナンス」和 §13 KPI⑥「RAG検索のヒット率」那一格——
**用来测检索好不好，不用来存知识。**

| | `tools/kb-platform` | `tools/rag` |
|---|---|---|
| 规格书位置 | §11.2 组件④（本体） | §11.2 ⑤ 評価・ガバナンス（尺子） |
| 装什么 | company / project 两层，带 scope・conf_level・status・doc_type | 只有摘要语料，没有层级和治理 |
| 谁可以加知识 | 是唯一入口 | **不加**。语料正本已经搬到 kb 里了 |
| 检索入口 | 对 AI 和人 | 只对评测脚本 |

## 语料在哪儿

**不在这里。** 正本在 `tools/kb-platform/repo/projects/P-R60-001/chunks/raw/*.jsonl`，
`tools/rag` 只是直接读那个目录（`loader.py` 的 `DEFAULT_CHUNKS_DIR`）。

2026-10-29 之前的方向是"`docs/95_legacy/r60/` 为正本、kb 是导出物"，已经反过来了；
所以**不要在这里新增语料或改摘要文本**，改那边，然后重跑 `ingest`。

## 什么时候用它

1. **改动检索相关的东西之后**（分词、切片、摘要重写），跑一次 `eval` 看有没有退化。
2. 需要**按模块过滤**的对照数据时（`query --module`），它比 kb 的命令行多这一个开关。

```bash
py -3 -m tools.rag build --scope all          # 建索引（build/rag/，gitignore 区）
py -3 -m tools.rag query "排他制御 いつ" -k 5  # 检索
py -3 -m tools.rag eval                        # 80 题金标
```

## 当前基线（2026-10-29 实测）

| 口径 | recall@5 | MRR |
|---|---:|---:|
| 按模块过滤（`--module`，等于告诉它答案是哪个模块） | 1.000 | 0.901 |
| 不过滤（真实使用方式） | 0.863 | 0.645 |

**这两个数要一起读。** 过滤口径的 1.000 是因为已经告诉它模块了，不代表它能从所有模块里挑对；
不过滤的 0.863 才是它作为检索器的真实水平。对比数据见 `reports/kb-export/P3-收敛记录.md`。

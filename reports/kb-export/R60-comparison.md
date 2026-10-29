# R60 检索对照：`tools/rag` vs `tools/kb-platform`（P1 验收）

| 项目 | 内容 |
|---|---|
| 日期 | 2026-10-29 |
| 目的 | 知识搬到 `tools/kb-platform/repo/projects/P-R60-001/` 之后，判断能不能退役 `tools/rag`（拍板第 3 项：先留，看对照再定） |
| 方法 | 同一组 10 个问题，两套引擎各取 top-3，比较第 1 名的落点 |
| 结论 | **两套都能用，但落点粒度不同；不建议现在退役 `tools/rag`** |

---

## 1. 执行记录（命令 + 实际输出）

```text
py -3 -m tools.rag build
  → built teaching chunks=341 -> build\rag\r60-teaching.sqlite

py -3 tools/kb-platform/run.py ingest --repo tools/kb-platform/repo
  → 追加=83 更新=0 スキップ=0 チャンク=5963
    （draft→open 修正後）追加=0 更新=76 スキップ=7

py -3 tools/kb-platform/run.py eval --repo tools/kb-platform/repo
  → cases=24 top_k=5 recall@5=1.000 MRR=0.938  しきい値 recall@5 >= 0.85: PASS
```

> `tools.rag build` が **341**、元の JSONL は **344** 行。差 3 は取り込み時の schema 検証で落ちた行である
> （既存の挙動。今回の移設で増えた差ではない）。

---

## 2. 10 問の第 1 位比較

| # | 問い | `tools/rag` 第 1 位 | `tools/kb-platform` 第 1 位 | 判定 |
|---|---|---|---|---|
| RQ001 | R60Ssk の前提条件と操作範囲 | `R60Ssk:screen:overview`（期待通り） | `chunks-r60ssk` §画面概要・前提条件 | 同等 |
| RQ002 | R60Ssk 検索画面の実項目数 | `R60Ssk:screen:search-items`（期待通り） | `chunks-r60ssk` §廃止_画面項目内容 | 同等 |
| RQ003 | R60User の位置づけ・テーブル・モード | `USR-SCR-001` | `chunks-r60user` §位置づけと規模 | 同等 |
| RQ004 | R60User 検索画面の項目数・ソート列 | `USR-SCR-002` | `chunks-r60user` §画面項目数 | 同等 |
| RQ005 | R60Plc の位置づけ・テーブル・API | `PLC-SCR-001` | `screens-r60plc` 本文 | 同等 |
| RQ006 | R60Plc 検索画面の項目数・ソート列 | `USR-SCR-002`（**誤モジュール**） | `chunks-r60plc` §一覧 31 列とソート可能列（正解） | **KB 優位** |
| RQ007 | R60Maker の前提条件・排他・画面区分 | `R60Ssk:screen:overview`（**誤モジュール**） | `chunks-r60maker` §画面概要・権限 | **KB 優位** |
| RQ008 | R60Maker 検索画面の項目数・条件 | `R60Ssk:screen:search-items`（**誤モジュール**） | `chunks-r60ssk` §廃止_…（**同じく誤**） | 両方誤 |
| RQ009 | R60SesModel の構成 | `SES-SCR-008` | `chunks-r60sesmodel` §構成 | 同等 |
| RQ010 | R60SesModel 検索一覧の項目数 | `SES-SCR-002` | `screens-r60sesmodel` 本文 | 同等 |

**集計**: 同等 6 / KB 優位 2 / RAG 優位 0 / 両方誤 1 / （RQ008 を含めると KB 正解 7、RAG 正解 6）

---

## 3. 观察到的差别（不是打分，是性质）

| 维度 | `tools/rag` | `tools/kb-platform` |
|---|---|---|
| 落点粒度 | **预先切好的 chunk**（`R60Ssk:screen:overview`），直接命中答案段 | **文档 + 章节**，常常落到整篇摘要的某一节 |
| 摘要的价值 | 344 条摘要是**人/AI 写好的**，措辞贴近问法 | 摘要现在也进库了（`chunks/*.md`），所以这部分价值被继承 |
| 模块区分 | 弱：4 个问题落到了别的模块（RQ006/RQ007/RQ008） | 也弱，但比 rag 好（RQ008 同样串了） |
| 覆盖面 | 只有摘要，没有字段表/API/错误 | **字段表、API 契约、错误、测试**都在（这次新增的 36 篇） |
| 维护 | 自建，只在摘要层 | 上游在维护，schema / 权限 / 评测齐全 |

---

## 4. 结论与建议

1. **不退役 `tools/rag`（维持拍板第 3 项的原判断）**。它在「问题措辞接近摘要」时落点更准，这是预切 chunk 的优势，kb 的自动切块短期补不上。
2. **kb-platform 作为唯一正式入口**对外（`使用手册` 只写 kb 的命令）。`tools/rag` 降为**内部评测器**，不再扩语料。
3. 两套并存的前提是**语料同源**：rag 读的是 `P-R60-001/chunks/raw/*.jsonl`，kb 读的是同目录生成的 `chunks/*.md`。同一份摘要，两个视图——不会出现「两个答案」的分歧。
4. **下一步要修的是模块串味**（RQ006/7/8）：问题里虽写了 `R60Maker`，检索仍会串到 `R60Ssk`。原因是表的行 chunk 重复携带同一批表头，弱化了模块名。`tools/kb_migrate` 的 `yaml_to_markdown` 已在每节标题带模块名，但摘要 digest 的节标题没有——建议在 digest 的每节标题里补上模块名（下一轮）。

---

## 5. 本次对照不能证明的事

- 不能证明 kb 在**更大的语料**（第二个案件）上仍有 1.0 的 recall——现在只有 83 篇。
- 不能证明 `eval` 的 1.000 代表真实问答质量：24 题里 12 题是上流 demo（本次补了缺失的 `project: P-DEMO-001` 才从 0.333 变成可测），12 题来自 `eval/gold-qa.yaml` 抽样，**不是独立构造的**。
- 不能替代人工判定：本次 10 问的「判定」列是我读落点后的分类，**不是自动指标**（rules/02 §10）。

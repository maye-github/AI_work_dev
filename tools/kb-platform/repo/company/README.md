---
doc_id: HOWTO-COMPANY-INDEX-001
scope: company
title: company/ ディレクトリの使い方と昇格の判据
doc_type: howto
version: "1.0"
status: active
conf_level: 10
owner: 共通基盤チーム
updated_at: 2026-10-29
tags: [knowledge-base, company-scope, promotion]
---

# `company/` — 公司级知识（跨案件复用）

> 本目录放**任何案件都能用**的方法与标准。案件事实不放这里。
> 上层说明见 `tools/kb-platform/VENDORED.md`；上游正本是 `D:\AI_platform`。

---

## 1. 什么东西该放进来

判据只有一句：**换一个顾客、换一个系统，这条还成立吗？**

| 放进 `company/` | 放进 `projects/<P-ID>/` |
|---|---|
| 判定方法（A/B/C 怎么分、出典等级怎么判） | 某案件的 A/B/C 实际条目、Q 番号与回答 |
| 交付方式（二重化、受控回流） | 某案件的成果物清单与文件路径 |
| 审查观点的**索引与用法** | 某案件的 QA 票、指摘、偏离登记 |
| 测试比率、命名规约、编码规约 | 某案件的 TC、字段名、表名、SQL |

**反例（不该进 company）**：某个画面的项目构成、某张表的列名、某个函数的行号、
`R60Common.ts` 的函数清单。这些是案件事实，属于 `projects/` 或知识库的 `standards/`。

## 2. 现有条目

| doc_id | 路径 | 内容 |
|---|---|---|
| `STD-GLOSSARY-001` | `glossary/terms.md` | 業務用語集（受注・在庫） |
| `PAT-SCREEN-001` | `patterns/screen/list-search.md` | 一覧検索画面の標準パターン |
| `STD-CODING-001` | `standards/coding/general.md` | コーディング規約（共通） |
| `PAT-DELIVERY-001` | `patterns/delivery/dual-track.md` | 成果物の二重化（機読源と日文正式版） |
| `PAT-REVIEW-LENS-001` | `patterns/review/requirement-lenses.md` | 要求書審査の観点（4 群 52 本の使い方） |
| `STD-REQ-ABC-001` | `standards/requirements/abc-classification.md` | 未確定事項の A・B・C 分類 |
| `STD-REQ-EVID-001` | `standards/requirements/evidence-grade.md` | 出典等級 E1〜E4 |
| `STD-TEST-RATIO-001` | `standards/testing/ratio.md` | テストケースの分類と最低比率 |

上 3 篇は上流（`D:\AI_platform`）由来のデモ用文書であり、評価問題（`eval/golden.yaml` の
Q009・Q010・Q012）がこの 3 篇を期待している。**消してはならない。**

## 3. 書き方（書き足すとき）

1. **front matter は 10 項目**：`doc_id` / `scope: company` / `title` / `doc_type` / `version` /
   `status` / `conf_level` / `owner` / `updated_at` / `tags`。
   **`scope: company` に `project_id` を書いてはならない**（`run.py lint` が弾く）。
2. `doc_id` は `<種別>-<領域>-<連番>`。既存と衝突させない。
3. `doc_type` は `standard` / `pattern` / `glossary` / `decision` / `howto` から選ぶ。
4. **本文は「要約＋正本へのポインタ」にする。** 同一の定義を二箇所に書くと、必ずどちらかが古くなる。
   冒頭に「本条は要約であり、正本は 〜」の一文を置き、**食い違ったら正本を採る**と明記する。
5. 案件固有の例は**落とすか匿名化する**。実在の表名・関数名・行番号・顧客名は書かない。

## 4. 検証と上流への還流

```bash
# 形（front matter・scope・doc_type・conf_level）を検査
py -3 tools/kb-platform/run.py lint --repo tools/kb-platform/repo

# 索引を作り直してから評価
py -3 tools/kb-platform/run.py ingest --repo tools/kb-platform/repo
py -3 tools/kb-platform/run.py eval --repo tools/kb-platform/repo
```

- **本ディレクトリはベンダリング（写し）である。** 正本は `D:\AI_platform`。
  ここで足した条目は、**上流へ PR で還流させる**。上流を直接編集しない。
- 還流の単位は**条目 1 本**（ファイル 1 つ）。複数案件で使われた実績ができたら上げる、が目安。

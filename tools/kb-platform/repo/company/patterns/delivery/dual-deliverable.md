---
doc_id: PAT-DELIVERY-002
scope: company
title: "成果物の二重化（機読源 ⇄ 日文正式版）"
doc_type: pattern
version: "1.0"
status: active
conf_level: 20
owner: Nan
updated_at: '2026-11-06'
tags: [delivery, dual-track, xlsx]
source_project: framework-rules
---

# 成果物の二重化（機読源 ⇄ 日文正式版）

> **本ファイルは「成果物の二重化」の唯一の定義である（NFR-1）。**
> 他文書は本ファイルを参照するのみとし、定義を再記述しない。
>
> 出典: 落地篇 PPT **S20**「成果物の設計原則 05」・**S24**「成果物の二重化（対日開発の要点）」・
> v1 PPT **S7**「假想示例（双轨制）」・**S12**。
>
> **注意（用語の区別）**: 本概念は、本骨架の `tools/kb-platform/repo/projects/P-R60-001/review/`
> （審査前後のスナップショット＋指摘。**本骨架の追加要素**）とは**別概念**である。
> 両者を混同しないこと。詳細は `ppt-deviation-register.md` §2 A-11 を参照。

---

## 1. PPT 原文（真源・逐語）

### 1.1 定義（落地篇 S24）

> **成果物の二重化（対日開発の要点）**
> 内部は機読できる構造化ソース、対外は規約準拠の日文正式成果物。自動変換で両立させる。
>
> **内部成果物（機読源）**
> ・Markdown ＋ YAML front matter
> ・要件ID／設計ID／テストID を保持
> ・Git で版管理し、差分でレビュー
> ・AIが直接読み書きする
>
> **対外成果物（日文正式版）**
> ・Excel／Word（日方規約に準拠）
> ・レビューは従来と同じ手順
> ・顧客提出・検収の対象
> ・品質記録として保管する
>
> **自動変換**: テンプレート変換・整合チェック

### 1.2 なぜ二重化するのか（落地篇 S24・逐語）

> ① 顧客要件: 日方は従来フォーマットの日文成果物を納品物・検収対象として求める。
> ② AI活用: AIが読めるのは構造化データ。自然文のExcelは再解析コストが高い。
> ③ 整合性: 単一ソースから生成すれば、二重管理による不整合を防げる。

### 1.3 成果物の設計原則における位置づけ（落地篇 S20 05・逐語）

> **二重の形態** / 機読源（Markdown／YAML）から人読用（Excel／Word）を自動生成する

### 1.4 双轨制（v1 S7・逐語）

> **产物格式说明：内部协作与对外交付双轨制**
> 1. 内部AI协作、评审迭代阶段：优先 Markdown(.md)，纯文本 AI 读写稳定，支持版本对比与 Mermaid 流程图
> 2. 对外向日方纳品交付：按客户要求输出 Word/Excel 正式式样书，由 Markdown 内容转换生成
> 3. 含审批栏、管理编号、大量合并单元格的管理类表单，仍保留 Excel；AI 输出永远是初稿，必须人工评审修正

---

## 2. 本骨架での実装

| 層 | 実体 | 状態（Phase 1 時点） |
|----|------|---------------------|
| 機読源 | `docs/**/*.md` ＋ `*.yaml`（front-matter 7 字段） | 実装済み |
| ID 保持 | `docs/00_registry/ids.yml`（唯一発号口） | 実装済み |
| 版管理 | Git（差分でレビュー） | 実装済み |
| 自動変換 | `tools/gen_formal/` | **dry-run のみ**（`field_count` 一致検証まで） |
| 対外成果物 | 日文正式 Excel／Word | **未生成**（下記 §4 の理由） |
| 整合チェック | `tools/trace_check` gate3・gate4 | 実装済み |

### 2.1 変換パイプライン（設計）

```
機読源(.md/.yaml)
  → normalize   （項目名・桁数・区分値の正規化）
  → template binding（顧客テンプレートへ割当）
  → formal render    （openpyxl 等で Excel/Word 化）
  → 整合チェック      （列数 == I-ID 数 / 単一ソース grep == 1 / .xlsx 数）
```

**Phase 3.5 まで `formal render` で停止する**（= dry-run）。理由は §4。

---

## 3. 禁止する回路（双向回路）

対日案件では顧客が Excel に直接赤字を入れるのが常態である。しかし次の回路は **NFR-1 違反**になるため禁止する。

```
【禁止】機読源 → Excel → 人が Excel 本文を改変 → 改変版を AI に渡して .md へ逆変換
```

同一フィールドが二箇所で定義され、どちらが正か判別できなくなる。

**許可する回路（受控回流）**: 正文本体は**読み取り専用**とし、別シート「指摘シート／レビュー欄」
（行番号・ID 付き）を添付 → 顧客は**そこにのみ**記入 → AI は**その欄だけ**を読んで機読源を修正 → 再生成。

詳細: `.claude/rules/00-project-global.md` §11。

---

## 4. `.xlsx` をどこに作るか（2026-10-21 改訂）

- **`docs/**` には作らない。** 合格条件 `find docs -name "*.xlsx" | wc -l == 0`（`docs/00_plan/review.md` CP-R-3）
  は**変わっていない**。`docs/` は機読源だけを置く場所である。
- **`reports/` 配下（gitignore 区）には作してよい。** 目視・対外ドラフト用の生成物はここに置く。
  入口は `py -3 -m tools.gen_formal.book --md <機読源>.md --out reports/<…>.xlsx`。
  出力パスに `docs` を含むと Exit 2 で拒否される（規則の機械化）。
- **生成物は手で編集しない。** 直すのは機読源であり、再生成で上書きされる（規則 00 §11）。
- **顧客テンプレートへの接続**と**受控回流**は引き続き Phase 2（人ゲート G-C2）。
  それまでは参考書の体裁を `book.py` が再現する（構成の定義は
  [reference-design-book.md](reference-design-book.md)）。

参照: `tools/gen_formal/README.txt`、`ROADMAP_3PHASE.md` Phase 2 #1。

---

## 5. 参照

- `.claude/rules/00-project-global.md` §11（受控回流）・§12（可読化。`.xlsx` は `reports/` 配下のみ）
- `tools/kb-platform/repo/company/standards/ppt-deviation.md` §1（PPT 由来の確認）・§2 A-11（別概念との区別）
- `docs/00_registry/glossary.yml`（用語: 成果物の二重化／機読源／日文正式版／受控回流）

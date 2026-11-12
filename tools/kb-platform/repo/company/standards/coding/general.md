---
doc_id: STD-CODING-001
scope: company
title: コーディング規約（共通）
doc_type: standard
version: "1.3"
status: active
conf_level: 20
owner: Nan
updated_at: 2026-04-10
tags: [coding, naming, review]
source_project: upstream-demo
---

# コーディング規約（共通）

> **本条は要約であり、正本ではない。**
> 命名・実装の正本は `.claude/rules/03-design-coding.md`（§2 `BaseCamelModel`・§4 snake/camel 分区・§5 SQL 白名单）。
> **食い違ったら規則を採る。** 本条は「案件をまたいで共通な一般則」だけを持つ。

## 1. 適用範囲

受託開発の全案件に適用する。案件固有の事情で本規約を外す場合は、
案件キックオフ時に逸脱理由を ADR（decision 文書）として残すこと。

## 2. 命名規則

- クラス名は PascalCase。変数・関数は snake_case を**既定**とする。
  **ただし TypeScript の接口層は camelCase**（分区の正本は `.claude/rules/03-design-coding.md` §4。
  `BaseCamelModel` が変換を担う。本条の snake 既定を接口層へ適用しない）。
- 定数は UPPER_SNAKE_CASE とし、マジックナンバーの直書きを禁止する。
- 真偽値の変数は `is_` / `has_` / `can_` で始める。
- データベースのテーブル名は**案件の命名規約に従う**。本条の `T_` 接頭辞は既定案であり、
  案件規約が優先する（本骨架の R60 系は `*_TBL` を用いる）。カラム名は snake_case とする。
- 画面ID・PGM_ID・APIパスは案件内で一意にし、命名規則をREADMEに1箇所だけ書く。

## 3. コメント

コメントは「なぜ」を書く。何をしているかは識別子で示す。
変更履歴・チケット番号・作業者名はコードに書かず、コミットメッセージに書く。

## 4. レビュー観点

1. 入力値は系の境界で検証しているか。
2. 例外を握りつぶしていないか。
3. 同じ条件分岐が3箇所以上に散っていないか。
4. テストが仕様の「なぜ」を説明できているか。

## 5. 禁止事項

- 本番環境の接続情報をソースコードに直書きすること。
- レビュー未実施のままブランチをマージすること。

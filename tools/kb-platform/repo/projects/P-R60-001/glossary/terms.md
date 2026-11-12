---
id: KNOW-P-R60-001-GLOSSARY-TERMS
type: knowledge
req_ids: []
sensitivity: internal
doc_id: r60-001-glossary-terms
scope: project
project_id: P-R60-001
title: 用語集 — P-R60-001
doc_type: glossary
version: 0.1.0
status: open
conf_level: 30
owner: Li
updated_at: '2026-11-02'
---

# 用語集 — P-R60-001

> 記入規則の正本は `tools/kb-platform/repo/company/templates/glossary.md`（`TPL-GLOSSARY-001`）。
> **案件専用語だけ**を載せる。一般語（画面・一覧・登録）は載せない。
> 空欄を残さない（空欄は「無い」と「まだ書いていない」を区別できない）。
>
> **以下の 4 行は模擬データである。** 実案件では実際の用語に置き換えること。

| 用語ID | 用語（原文） | 読み | 中文 | English | 定義（1 文） | 出所 | 備考 |
|---|---|---|---|---|---|---|---|
| TERM-001 | 引当 | ひきあて | 分配 | allocation | 受注に対して在庫を確保し、他の受注に使えないようにする処理 | 基本設計 §4.2 | 別名「確保」 |
| TERM-002 | 締め処理 | しめしょり | 结账处理 | period close | 一定期間の取引を確定し、以後の訂正を禁止する処理 | 要件定義 §2.1 | |
| TERM-003 | 共通マスタ | きょうつうますた | 公共主数据 | common master | 複数の業務で共有する基礎データの総称 | 基本設計 §1 | 本案件の対象画面群 |
| TERM-004 | ロケ | ろけ | 库位 | location | 倉庫内で在庫を保管する場所を識別する単位 | 詳細設計 §2.3 | 正式名称は「ロケーション」 |
| TERM-005 | 排他制御 | はいせいせいぎょ | 并发控制 | exclusive control | 更新日時とリビジョンで新旧を判定し、古い画面からの更新を拒む仕組み | データベース定義 §4.2 | 別名「同時更新制御」「楽観ロック」 |
| TERM-006 | 画面遷移 | がめんせんい | 画面迁移 | screen transition | ある画面から別の画面へ移る動きと、その条件 | 基本設計 §2 | |
| TERM-007 | 共通部品 | きょうつうぶひん | 公共组件 | common component | 複数画面で共通に使う関数・部品。本案件では既存資産を呼び出す | 詳細設計 §7 | 重複実装の禁止対象 |

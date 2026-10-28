---
doc_id: STD-GLOSSARY-001
scope: company
title: 業務用語集（受注・在庫）
doc_type: glossary
version: "2.0"
status: active
conf_level: 20
owner: 共通基盤チーム
updated_at: 2026-03-28
tags: [glossary, order, stock]
---

# 業務用語集（受注・在庫）

対日受託案件で表記ゆれが起きやすい用語を定義する。
設計書・API・DBで同じ英語表記を使うこと。

## 用語対応表

| 日本語 | 英語表記 | 備考 |
|---|---|---|
| 受注 | order | 受注番号は order_no |
| 引当 | allocation | 在庫の引き当て。予約ではない |
| 在庫 | stock | 実在庫。引当可能在庫は available_stock |
| 得意先 | customer | 顧客ではなく得意先で統一 |
| 納期 | delivery_date | 希望納期は requested_delivery_date |
| 出荷 | shipment | 出荷確定は shipment_confirm |
| 部分引当 | partial allocation | 引当モード=2 のときのみ許可 |
| 取消 | cancel | 論理削除は logical delete と書き分ける |

## 表記ルール

- 英語は snake_case（DB・API）、画面表示は日本語。
- 「引当」を reserve と訳さない。既存設計書との互換のため allocation に統一する。

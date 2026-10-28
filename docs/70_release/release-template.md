---
# front-matter（7 字段固定・全テンプレート共通）
id: TPL-007
type: release_note
req_ids: []
status: draft
sensitivity: internal
owner: AI-SE
version: 0.1.0
---

# リリース記録テンプレート / 发布记录模板

> 使い方: 本ファイルを `release-<版>.md` に複製し `<...>` を実値へ置換する。
> 基本 Tag は `baseline/<R-xxx>/basic-v<x.y.z>`。baseline 後変更は CR-xxx を経由する。

## release_note
<!-- 何を・いつ・誰の承認で出すか（構造化して記載） -->
- version: `<x.y.z>`
- date: `<YYYY-MM-DD>`
- scope: `<対象モジュール / R-ID 一覧>`
- changes:
  - `<変更1>`
  - `<変更2>`
- approved_by: `<承認者（役割）>`

## rollback_procedure
<!-- 切り戻し手順。前提・手順・確認の 3 段で構造化 -->
1. 前提: `<切り戻し起動条件（監視アラート / 品質閾値割れ 等）>`
2. 手順:
   - `<手順1: 前版 baseline Tag を再デプロイ>`
   - `<手順2: DB は前版スナップショットへ復元（対象テーブルは TBL_1 等の占位）>`
   - `<手順3: キャッシュ / セッションのクリア>`
3. 確認: `<スモークテスト項目 / 監視復旧確認>`
4. 記録: `<切り戻し実施理由を CR-xxx として残す>`

## baseline_tag
<!-- Tag 命名と対応する受入基準 -->
- tag_name: `baseline/<R-xxx>/basic-v<x.y.z>`
- commit: `<短縮 SHA>`
- acceptance_ref: `<対応する AC / 受入基準>`

## 健康度記録（AB_Reports）
<!-- A/B 比較の健康度は doc/03_AI/AB_Reports 配下に集約する -->
- report_dir: `doc/03_AI/AB_Reports`
- summary_path: `doc/03_AI/AB_Reports/reports/<Module>/summary.md`
- overall_health: `<緑 | 黄 | 赤>`
- mismatch_count: `<不一致件数>`
- notes: `<赤・黄の場合は原因と対処>`

## 未確定事項（前提の明示）
- q_id: `<Q-xxx>`
  question: `<未確定の問い>`
  status: open

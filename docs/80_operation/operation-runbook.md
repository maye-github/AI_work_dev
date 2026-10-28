---
# front-matter（7 字段固定・全テンプレート共通）
id: TPL-008
type: operation_runbook
req_ids: []
status: draft
sensitivity: internal
owner: AI-SE
version: 0.1.0
---

# 運用ランブック テンプレート / 运维手册模板

> 使い方: 本ファイルを `operation-runbook-<Module>.md` に複製し `<...>` を実値へ置換する。
> 機密則: 接続情報・パスワード・実 IP・バケット名は絶対に直書きせず、占位（例: `USER_1` / `PWD_1` / `IP_1`）を用いる。

## 1. Oracle 接続プール 健康チェック SQL
<!-- 接続数・待機・セッションの健全性を定期確認する。値は占位で記載。 -->
```sql
-- 接続プール / セッションの健全性確認（読み取り専用）
SELECT
    COUNT(*)                         AS active_sessions,
    SUM(CASE WHEN status = 'ACTIVE' THEN 1 ELSE 0 END) AS busy_sessions
FROM   v$session
WHERE  username = 'USER_1';

-- 待機イベント上位（ロック・I/O 詰まりの把握）
SELECT event, total_waits, time_waited
FROM   v$system_event
WHERE  wait_class <> 'Idle'
ORDER  BY time_waited DESC
FETCH FIRST 10 ROWS ONLY;
```
- 閾値: `<busy_sessions 上限 / 待機時間 上限>`
- 異常時: `<アプリ側プール設定の再起動手順 or 切戻し判断>`

## 2. trace_check の実行方法
<!-- 6 重門番をローカルで実行。commit / push 前に必須。 -->
```bash
# 全門（ID 合法 / 追溯 / front-matter / 生成一致 / 命名 / 機密）
py -3 tools/trace_check.py --strict --gate 6 --report reports/gate6_report.json

# 単項チェック
py -3 tools/trace_check.py --strict --only-check secrets
py -3 tools/trace_check.py --strict --only-check id-chain --root <R-xxx>
```
- 合格条件: Exit 0 / `gate6_report.json` で `pass=6 fail=0` / `orphan_ids=[]`
- 失敗時: `<野号 / 孤児 ID / 機密ヒットの是正手順>`

## 3. 機密スキャン手順
<!-- 13 条キーワード（gitleaks 等価）をコミット前に必ず走査する。 -->
1. 走査: `py -3 tools/masking/mask_demo.py --self-test`
2. 走査: `<gitleaks detect --source . --no-git -v または trace_check --only-check secrets>`
3. 判定: `<1 件でも hit したら commit 禁止 → masking 必須>`
4. 占位変換: `<対象値 → TBL_1 / COL_1 / PWD_1 / IP_1 / BUCKET_1 / DOM_1 / KEY_1 等>`
5. 記録: `<マスク辞書は tools/masking/masking_dict.json（Git 非登録）>`

## 4. 緊急配信 SEND_STS='9' 切戻し手順
<!-- 緊急配信ステータス（SEND_STS）を通常へ戻す。トリガ条件は機密のため占位。 -->
1. 検知: `<SEND_STS='9' が想定外に立った検知方法>`
2. 前提: `<対象 BIZ-ID / 条件（TRG_1 占位）の特定>`
3. 切戻し:
   - `<手順1: 対象行の SEND_STS を通常値へ UPDATE（WHERE 条件は占位）>`
   - `<手順2: 関連キュー / バッチの停止 or 再送抑止>`
   - `<手順3: 監査ログ（KSN_KBN / KSN_STF_ID）の記録確認>`
4. 確認: `<再配信されないこと / 業務データ整合の確認>`
5. 記録: `<インシデント票・CR-xxx として残す>`

## 未確定事項（前提の明示）
- q_id: `<Q-xxx>`
  question: `<未確定の問い（例: 切戻し権限の範囲）>`
  status: open

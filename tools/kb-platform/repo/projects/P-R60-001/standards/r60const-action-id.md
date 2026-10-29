---
id: STD-R60-001-ACTIONID
type: knowledge
req_ids: [R-101]
status: baselined
sensitivity: internal
owner: AI-PG
version: 0.1.0
doc_id: r60-001-standards-r60const-action-id
scope: project
project_id: P-R60-001
title: r60const.py ACTION_ID 40 個の操作分類
doc_type: standard
conf_level: 30
updated_at: 2026-10-29
---

# r60const.py ACTION_ID 40 個の操作分類

`r60const.py` 15-43 行目に定義される ACTION_ID 40 個は、**基本設計（BD）の操作分類**として用いる。
サービスメソッド・画面イベントはこの ACTION_ID に紐づけて設計する。

---

## 1. 分類表

| 分類 | ACTION_ID |
|---|---|
| 初期化系 | `ACTION_ID_INIT` / `ACTION_ID_HEAD` / `ACTION_ID_CHECK` / `ACTION_ID_CONDITION` |
| 検索系 | `ACTION_ID_SEARCH` / `ACTION_ID_DETAIL` / `ACTION_ID_CHILD_SEARCH` / `ACTION_ID_CHILD_DETAIL` |
| 登録系 | `ACTION_ID_NEW` / `ACTION_ID_REGIST` / `ACTION_ID_MODIFY` / `ACTION_ID_COPY` / `ACTION_ID_DUPLI` |
| 削除系 | `ACTION_ID_DELETE` |
| ダイアログ系 | `ACTION_ID_DIALOG` |
| 画面遷移系 | `ACTION_ID_BACK` / `ACTION_ID_END` / `ACTION_ID_TITLE_CHANGE` |
| ドロップダウン系 | `ACTION_ID_MAKEDROPDOWN` / `ACTION_ID_CHILD_RESULT` / `ACTION_ID_FOOT` |
| 明細系 | `ACTION_ID_ADD_RECORD` / `ACTION_ID_CHILD_REGIST` / `ACTION_ID_CHILD_MODIFY` / `ACTION_ID_CHILD_NEW` |
| ファイル系 | `ACTION_ID_DOWNLOAD` / `ACTION_ID_DATAINIT` / `ACTION_ID_CHECK_UPLOAD` / `ACTION_ID_FILE_UPLOAD` |

---

## 2. 使い方

- **BD を書くとき**：画面の操作を ACTION_ID に対応づけて一覧化する
  （実例：`playbooks/R60Area-design-to-code.md` §2 の 7 メソッド対応表）。
- **DD を書くとき**：ロジック（L-ID）がどの ACTION_ID から呼ばれるかを追記する。
- **製造するとき**：ACTION_ID を新設しない。既存の 40 個から選ぶ。
  足りない場合は**設計変更（CR）**であって製造工程の判断ではない（紅线②）。

---

## 3. 出所

- 移設元：`docs/95_legacy/r60/`（2026-10-29 に削除。履歴は git にある）
- 抽出元スキル定義書：`.claude/skills/code-from-design-trans-cosmos-ai/SKILL.md` v0.1.0 §2.4
- 実際のファイル：旧案件側 `app/utils/r60const.py`（読み取り専用）

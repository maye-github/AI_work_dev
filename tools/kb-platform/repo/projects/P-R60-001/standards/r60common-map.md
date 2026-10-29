---
id: STD-R60-001-R60COMMON
type: knowledge
req_ids: [R-101]
status: baselined
sensitivity: internal
owner: AI-PG
version: 0.1.0
doc_id: r60-001-standards-r60common-map
scope: project
project_id: P-R60-001
title: R60Common.ts 関数活用マップ（代表 16 関数・唯一の定義）
doc_type: standard
conf_level: 30
updated_at: 2026-10-29
---

# R60Common.ts 関数活用マップ（代表 16 関数・唯一の定義）

`R60Common.ts` からエクスポートされる代表関数と、詳細設計（DD）上での活用箇所。
**既存資産を唯一真源とし、新規類似関数の自作は禁止**（`build_mode: migration` 案件の禁①）。

> **関数数の数え方（混同しやすい）**
> - `R60Common.ts` 全体は **54 関数**（`CLAUDE.md` §2 禁①）。
> - 製造で実際に呼び出す**代表関数は本表の 16 件**。
> - `.claude/rules/03-design-coding.md` §3 の表は、このうち**呼び出し順で特に重要な 13 件を抜粋**したもの。
> - **全リストの定義は本文書のみ**（NFR-1）。関数を追加・変更するときは本文書だけを直し、
>   抜粋表は「抜粋の範囲を変えるときだけ」触る。

---

## 1. 関数一覧（16 件）

| No | 関数名 | 用途 | 使用箇所 |
|----|--------|------|----------|
| 1 | `showMessageDialog` | メッセージダイアログ | エラー／情報通知時全般 |
| 2 | `subCheckSubmit` | 二度押し防止チェック | 全ボタンイベント先頭 |
| 3 | `subSetSubmitFlg` | 二度押し防止フラグ ON | API 呼出直前 |
| 4 | `subInitSubmitFlg` | 二度押し防止フラグ OFF | API 呼出 finally ブロック |
| 5 | `spreadResults` | 条件／結果領域スプレッド | toggle 関数 |
| 6 | `resetErrors` | エラー状態リセット | 検索実行前 |
| 7 | `subCheckAlphabetNumber` | 半角英数字チェック | エリアコード入力チェック |
| 8 | `showErrorAndFocus` | エラー表示＋フォーカス移動 | 入力チェック NG 時 |
| 9 | `subDownload` | CSV ファイルダウンロード | doDownload 関数 |
| 10 | `subListBtnDisabled` | 一覧画面ボタン活性／非活性 | 検索成功後 |
| 11 | `subResultListInit` | 結果一覧初期化 | 検索成功後 |
| 12 | `initReset` | スクロール／ページャ初期化 | 検索実行前 |
| 13 | `resetSortIcon` | ソートアイコン初期化 | 検索実行前 |
| 14 | `byteCheck` | バイト数チェック | 全角／半角混在項目の桁数検証 |
| 15 | `subCheckKanaByte` | カナ・バイト数チェック | カナ項目（例: エリア名）検証 |
| 16 | `chkHanEngNum3` | 半角英数字 3 種チェック | コード系項目の文字種検証 |

---

## 2. 呼び出し順の典型

```text
subCheckSubmit
  → resetErrors / initReset / resetSortIcon
  → 入力検証（subCheckAlphabetNumber / byteCheck / subCheckKanaByte / chkHanEngNum3）
  → subSetSubmitFlg
  → API
  → subResultListInit / subListBtnDisabled
  → subInitSubmitFlg（finally）
```

- `subSetSubmitFlg` は API 呼出の**直前**、`subInitSubmitFlg` は**必ず finally**（例外時も解放する）。
- 入力検証は `showErrorAndFocus` と組で使い、NG 時は項目を特定してフォーカスを移す。

---

## 3. 出所

- 移設元：`docs/95_legacy/r60/`（2026-10-29 に削除。履歴は git にある）
- 抽出元スキル定義書：`.claude/skills/code-from-design-trans-cosmos-ai/SKILL.md` v0.1.0 §3.5
- 実際のファイル：旧案件側 `R60Common.ts`（読み取り専用）

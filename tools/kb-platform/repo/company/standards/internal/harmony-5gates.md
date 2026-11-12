---
doc_id: STD-INT-HARMONY-001
scope: company
title: "社内実績取入: Harmony の 5 道ゲートと自動化飛輪"
doc_type: standard
version: "1.0"
status: active
conf_level: 20
owner: Nan
updated_at: '2026-11-06'
tags: [internal, quality-gates, lessons]
source_project: framework-rules
canonical: true
---

# 社内実績取入: Harmony の 5 道ゲートと自動化飛輪

> **本ファイルの位置づけ**
> 要件源（PPT 2 份）**ではない**。社内 AI 実績 PPT から取入れた**方法論**である。
> 取入の種別は「**資産取入**（`tools/ingest`）」ではなく「**方法論取入**」であり、
> 出力先も `reports/ingest/**` ではなく本ファイル群（`tools/kb-platform/repo/company/standards/internal/**`）である。
> 登録簿: `tools/kb-platform/repo/company/standards/ppt-deviation.md` §2。
>
> **出所**: `D:\AI_knowledge\AI share交流会\AI 在Harmony项目中的应用.pptx`（Harmony プロジェクト組、2026.06）。
> 下記は同 PPT の記載の要約であり、本骨架による解釈は「**本骨架での写像**」と明示して区別する。

---

## 1. Harmony プロジェクトの概況（PPT 記載）

| 項目 | 内容 |
|------|------|
| 題材 | Vue 2 → Vue 3 の移行（2 プロジェクト） |
| プロジェクト A | `harmony_poc_admin`（管理端）— 38 モジュール / 185 Vue ファイル / **3 人チーム並行** |
| プロジェクト B | `harmony_poc_user`（従業員ポータル）— 22 ビュー / PC＋SP の 2 端 / **1 人開発・約 1 か月** |
| A の方式 | **知識体系駆動**（CLAUDE.md → guides ×5 → prompts/+skills/ → playbooks ×4 → 検証） |
| B の方式 | **自動化流水線**（scaffold → AI 移行 → test → browser → auto-fix → retest → report の 7 步） |
| 共通 | Claude Code。**同一方法論・異なる落地模式** |

> **本骨架への示唆**: 「チーム規模が方式を決める」という結論は、本骨架が
> 「同モジュール按节点分工 ＋ 多モジュール並行」の二軸を採る判断（A-12）と整合する。
> 3 人以上なら知識層（guides 相当＝`.claude/rules/`）が効き、1 人なら自動化（tools）が効く。

---

## 2. 5 道ゲート（PPT 逐語の要約）

Harmony は Vue 2（原版）と Vue 3（新版）の**一致**を機械で確かめるため、次の 5 段を常時走らせていた。

| # | ゲート | 手段 | 判定基準 | PPT 記載の実績 |
|---|--------|------|---------|--------------|
| **G1** | 静的検査 | **11 本の check スクリプト**（`--json` で CI 接続可） | 11/11 PASS | `registry` / `breaking` / `html` / `i18n` / `sass` ほか |
| **G2** | 構築 | `yarn build` | **零 error**（約 30 秒でフィードバック） | 零 error |
| **G3** | Console | Playwright でページ読込 | **error と warning の両方が零** | 0 errors, 0 warnings |
| **G4** | スモーク | ボタンを 1 つずつクリックし **8 秒**観察 | 全インタラクション点で無報錯 | 38/38 全通過 |
| **G5** | スクリーンショット対比 | `pixelmatch` による画素圧縮比較 | **差異率 < 5%** で合格 | 3 巡で 24.7% → 8.2% → **3.5%** 合格 |

**運用品質**: 一鍵編排（`node tests/run-gates.mjs --pages=<page>`）・dev server の自動起停・**失敗時に anomaly を自動归档**。

> **G5 の意味**（見落としやすい点）: G5 は「合格するまで自動で直す」ゲートではなく、
> **AI が 3 巡かけて自力で <5% まで収束させた**ことを記録している。
> 1 巡で合格するものではないため、初回 FAIL を異常と扱わないこと。

---

## 3. 本骨架での写像（どこまで実装済みか）

**誇張しない。** 本骨架が今持っているのは次の範囲である。

| Harmony | 本骨架 | 状態 |
|---------|--------|------|
| **G1** 静的検査 | `tools/trace_check` の gate1〜gate6（野号 / 追跡閉ループ / front-matter / 生成物一致 / 命名分区 / 機密） | ✅ **実装済**（G1 の位置に対応） |
| **G2** 構築 | — | ⚪ **未実装**（本骨架は対象コードを持たない。案件側の `yarn build` / `pytest` を呼ぶ形になる） |
| **G3** Console | — | ⚪ **未実装** |
| **G4** スモーク | — | ⚪ **未実装** |
| **G5** スクリーンショット対比 | — | ⚪ **未実装** |
| 失敗時の anomaly 自動归档 | `tools/kb-platform/repo/projects/P-R60-001/review/` への**手動**追記 | 🔶 **半実装**（自動化は未実装。`rules/06` §6 参照） |
| 一鍵編排 | `py -3 -m tools.trace_check --strict` | ✅ 実装済（6 gate を 1 コマンドで） |

> **写像の粒度差（重要）**: 要件源 PPT の「品質ゲート」は概念であり、
> Harmony の G1〜G5 は **Web アプリの移行に特化した実装**である。
> 本骨架が G1 に対応するものを持ち、G2〜G5 を持たないのは、
> **本骨架が「成果物（設計書・YAML・テスト設計）の品質」を守る骨架であり、
> 「動くアプリの品質」を守る装置ではない**ためである。
> Phase 2 以降で案件側の CI（build / Playwright）へ接続する余地を残す。

---

## 4. 自動化飛輪（PPT 逐語）

Harmony の飛輪はプロジェクト A/B で形が違う。**どちらも本質は「問題 → 解決の固化」**である。

### 4.1 ケース A: 知識沈殿型

```
1. 踩坑 (G1-G5 失敗)   2. anomaly 自動創建   3. 5 問帰档分析
4. guides/traps.md 更新  5. check スクリプト新增   6. git push 全隊免疫
```

- 成果（PPT）: **22 件の anomaly → 10+ の問題模式 → 11 本の check のうち 4 本が飛輪から産出**。
- 5 つの guides: `patterns`（16 類 Vue API 対応表 等）・`traps`（**56 条の既知陷阱** ＋ 排查決策樹 ＋ 3 大錯誤恢復流程）・`registry`（45 の全局登録点＝**唯一真相源**）・`workflow`（実行原則 ＋ 5 道ゲート詳解 ＋ Git 規範）・`lessons`。

### 4.2 ケース B: 自動修復型

```
scaffold → AI 移行 → vitest → Playwright → auto-fix → retest → 逐視図 report
```

- 問題発見後、**文書に归档せずスクリプトで直す**（Pinia store 生成器 / auto-fix / scaffold）。
- 発見した bug は **vitest のテストケースを補って回帰を防ぐ**。
- 成果（PPT）: 約 50+ コミット、約 22 ビュー、1 人 1 か月。

> **落とし穴**: auto-fix 型は「直す」ことに最適化されるため、**規則が文書化されずに属人化する**リスクがある。
> 本骨架は A 型（文書 → 検査）を採用する。理由は `.claude/rules/` が起動時に自動ロードされ、
> 「配布工程」を省略できるためである（`rules/06-knowledge-flywheel.md` §1）。

---

## 5. 4 層知識体系（PPT）

```
入口層  CLAUDE.md            → 技術スタック・制約・目録構成
規則層  guides/              → 模式・陷阱・登録清単・工作流・教訓
執行層  prompts/ + skills/   → 規則をコマンド化
検証層  ゲート + check       → G1〜G5
```

**核心理念（PPT 逐語）**: 「知識一次編写，N 次消費。毎踩一個坑，全隊永久避坑。」

> **本骨架での対応**: 入口層 = `CLAUDE.md` / 規則層 = `.claude/rules/` /
> 執行層 = `.claude/skills/` ＋ `.claude/agents/` / 検証層 = `tools/trace_check`。
> **4 層の構造は一致している**（`tools/kb-platform/repo/company/standards/platform-map.md` の 7 層とは粒度が違うだけで矛盾しない）。

---

## 6. 他プロジェクトへの起步 Checklist（PPT）

| # | 手順 | 目安 |
|---|------|------|
| 1 | `CLAUDE.md` を 1 本書く | **30 分**（最も費用対効果が高い）|
| 2 | `guides/` を作る（`patterns.md` から。最初の bug で `traps.md` を起こす）| 毎週 1 時間 |
| 3 | 中核 Prompt テンプレートを 1 本書く | 2 時間 |
| 4 | 最も簡単な検証スクリプト（G1 ＋ G2）を組む | 1 日 |
| 5 | 飛輪の習慣を作る（問題 → 規則 → check の追加を検討）| 継続（毎週 30 分）|

> **本骨架はこの Checklist を既に満たしている**（1・2 は `.claude/rules/`、3 は `.claude/skills/`、
> 4 は `tools/trace_check` が担当する）。**不足しているのは手順 5 の自動化部分**である（§3 の表を参照）。

---

## 7. 参照

- 飛輪の本骨架規則: `.claude/rules/06-knowledge-flywheel.md`
- SDS2 / SDS3 の失敗教訓: `tools/kb-platform/repo/company/standards/internal/sds2-lessons.md`
- 7 層プラットフォーム写像: `tools/kb-platform/repo/company/standards/platform-map.md`
- 追加要素の登録簿: `tools/kb-platform/repo/company/standards/ppt-deviation.md` §2

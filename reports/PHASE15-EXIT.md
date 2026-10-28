# Phase 1.5 出口検証 — 機械検査の実測記録

- **実施日**: 2026-10-12
- **実行**: Claude Code（唯一の実行ツール）
- **判定**: **機械検査は全項目 PASS**、**人ゲート 3 件も承認済**（下記 §4。拍板者 `SE-001` / 2026-10-12）。
  「機械が通った」ことと「人が承認した」ことは別である。本ファイルは前者の**実測記録**であり、
  後者の**承認記録**は §4 の表である。

> 本ファイルは `docs/00_plan/review.md` の CP とは別系統である。
> CP は**独立検査員**が `spec-reviewer` 等の別コンテキストで再実行する。本ファイルは**実装者自身の実測記録**であり、
> 自己申告である以上、CP の代用にはならない（自分で作ったものを自分で合格と言わない原則）。

---

## 1. 出口条件（7 項目）の実測

| # | コマンド | 期待 | 実測 | Exit |
|---|---------|------|------|------|
| 1 | `py -3 -m tools.trace_check --strict --report reports/trace_R101.json` | 6 gate PASS・`chain_complete=true`・`orphan_ids=[]` | `gate1..gate6=PASS`、`total_ids=79`、`orphans=0`、`field_count=56` | **0** |
| 2 | `py -3 -m tools.trace_check --strict --only-check secrets` | 機密ヒット 0 | `gate6=PASS` | **0** |
| 3 | `py -3 -m tools.masking.mask_demo --self-test` | `unmask_ok=true` | `mask_hits=11 unmask_ok=true exit=0` | **0** |
| 4 | `py -3 -m tools.gen_view --self-test` | 全項目 ok | `PASS 15/15 pass` | **0** |
| 5 | `py -3 -m tools.gen_formal.gen_excel --dry-run --module R-101` | `field_count=56` | `field_count=56`、`output_columns=ara_cmp_list_56items.csv` | **0** |
| 6 | `py -3 -m tools.ingest --self-test` | Exit 0 | `35 passed, 0 failed` | **0** |
| 7 | `ls docs/**/*.xlsx \| wc -l` | **0** | **0**（リポジトリ全体でも 0） | — |

### 1.1 gate 別の内部統計（`reports/trace_R101.json`）

| gate | 検査内容 | 統計 |
|------|---------|------|
| gate1 | ID 合法性（野号） | `declared_ids=77` / `registered_ids=79` / **`wild_ids=0`** / `void_used=0` |
| gate2 | 双方向追跡閉ループ | `nodes=77` / `edges=85` / `unreachable=0` / `asymmetric=0` / **`orphans=0`** |
| gate3 | front-matter 7 字段 | `checked=55` / **`problems=0`** |
| gate4 | 生成物一致 | `expected_field_count=56` / `generated_field_count=56` |
| gate5 | snake/camel 命名分区 | **`violations=0`** |
| gate6 | 機密ゼロヒット | `scanned_files=140` / `patterns=10` / **`hits=0`** |

> **`scanned_files=140` は基準値として記録する。** この数は走査対象自身を含むため実行ごとに動く
> （本ファイルを書く前は 139 であった。本ファイル自身が走査対象に加わって 140 になった）。
> **この増加は正常である。** 基準値として意味があるのは「**この数を下回らないこと**」の 1 点だけである。
> **検査員へ**: この値を**下回る**変更は「走査範囲を狭めた」ことを意味し、統制層の弱体化である
> （`review.md` CP-R-7 / `tasks.md` TR-19.1）。`docs/00_plan/**` を除外した旧版がまさにその形で
> 本番 Oracle 接続情報を漏らした。**増加は可、減少は不可。**

---

## 2. Phase 1.5 で実施した変更（作業単位の一覧）

| # | 変更 | 種別 |
|---|------|------|
| 1.1–1.4 | 用語の分離と出所修正（`dual-deliverable` / `review-diff-asset` / `controlled-reflux`）、`review_comments.md` の偽出典 3 件訂正、`ROADMAP` の参照頁訂正 | 訂正 |
| 1.5 | `docs/00_registry/ingest-manifest.yml` 新規（`expected_count` は 32 → **34** へ訂正。§3 参照） | 新規 |
| 1.6 | `tools/ingest/`（7 ファイル）新規。`--self-test` 35 checks | 新規 |
| 1.7 | `tools/trace_check/__init__.py` に **公開 `scan_text()`** を追加 ＋ gate6 の `reports/**` 走査に `.yml/.yaml` を**追加** | 変更 |
| 1.8 | `.claude/rules/00 §13`・`rules/03 §7`・`rules/04 §9`・**`rules/06`（新）**、`docs/90_knowledge/internal/{harmony-5gates,sds2-lessons}.md`（新） | 新規・追記 |
| 1.9 | `docs/00_plan/review.md` に CP-R-7 / CP-U-3 / CP-U-4 を追加（CP 総数 8 → **11**）。`docs/00_plan/tasks.md` に **Task 19**（TR-19.1〜19.4）を追加し、TR-17.1 の期待値を同時更新 | 新規・変更 |
| 追補 | `docs/90_knowledge/ppt-deviation-register.md` §2 に A-14 / A-15 / A-17 / A-18 を登録、JET 数の誤読を訂正 | 新規・訂正 |
| 追補 | `reports/AC-selfcheck.md` AC-1 の実測値を再測定（rules **6→7**、CODEOWNERS **8→11**） | 訂正 |
| 追補 | `reports/skeleton-files.txt` をディスク状態から**再生成**（手編集していない） | 再生成 |

> **`tools/ingest` の責務境界（誤解しやすい点）**
> - **`ids.yml` へ自動書込みしない。** `id-apply` も人が `approved: true` を付けた行のみを対象とする（Phase 2.3 で実装）。
> - **案件ソースの内容を読まない。** `inventory.json` にはパス・size・sha1 のみを書く。
> - **機密の値を書かない。** `secret_evidence.json` は**パスのみ**。値は 1 バイトも読まない（git 管理下かどうかの判定のみ）。
> - **機密パターンを独自実装しない。** `tools.trace_check.scan_text()` を import して再利用する。
> - **`D:\AI_work`（歴史案件）は読み取り専用。** 1 ファイルも書き換えていない。

---

## 3. Phase 1.5 で発見した出所の誤り（2 件）

### 3.1 「JET 全 32 モジュール」— 頁番号の数量読み違え

| 走査対象 | 独立した「32」 |
|---------|--------------|
| 要件源 PPT 2 份（落地篇 30 頁 ＋ v1 13 頁） | **0 箇所** |
| `AI在实际项目中的运用实绩_SDS3.pptx` | 1 箇所（**スライド番号**であって数量ではない） |
| `JETプロジェクトにおけるAI活用シナリオ.pptx` slide 8 | **「AI 適用済み API 数: 22 本（全 34 本のうち 64.7%）」** |

→ `ingest-manifest.yml` の `expected_count` を **34** へ訂正し、`expected_count_source` / `expected_count_caveat`
（**API 数 ≠ モジュール数**、確定は人ゲート G-B2）を併記した。
**唯一の定義**: `docs/90_knowledge/ppt-deviation-register.md` §2 の訂正注記。

### 3.2 `reports/AC-selfcheck.md` の実測値の陳腐化

`rules 6 份 → 実測 6`・`CODEOWNERS >= 7 → 実測 8` は**当時の値**であり、現在は 7 / 11。
いずれも閾値は `>=` のため**合否は PASS のまま**だが、**記録値が実態と食い違うのは証跡として失格**であるため、
再実測値へ更新した（閾値そのものは変更していない）。

---

## 4. 人ゲート — **承認済**（拍板者 `SE-001` / 2026-10-12）（红线③）

3 件とも**人の拍板者 `SE-001` が 2026-10-12 に承認した**。承認の生の言葉:

> 「G-A 可以，G-B 可以，G-E 可以，我是 SE-001」

| ゲート | 対象 | 承認した内容 | `approved_by` | `approved_at` | 状態 |
|--------|------|------------|---------------|---------------|------|
| **G-A** | 用語の分離と出所修正（1.1–1.4） | 「`review-diff-asset`」等の造語を採用する。PPT の語ではないことを承知の上で採用 | `SE-001` | 2026-10-12 | ✅ **承認** |
| **G-B** | 取入機構の仕様（1.5–1.7） | manifest の範囲・機密遮断の方式・**`ids.yml` へ自動で書かない**方針を承認 | `SE-001` | 2026-10-12 | ✅ **承認** |
| **G-E** | 方法論の反映（1.8） | SDS2/Harmony の教訓を `.claude/rules/**` へ入れる。**紅线は 7 条から増やさない** | `SE-001` | 2026-10-12 | ✅ **承認** |

> **承認の記録方法**: 拍板者の識別子（`SE-001`）を `approved_by` に、日付を `approved_at` に書く。
> **AI の名前を `approved_by` に書いてはならない。** 空欄のまま先へ進んでもならない。
> 本表が**本 3 ゲートの承認記録の唯一の在処**である（G-A/G-B/G-E は複数成果物に跨る横断ゲートであり、
> 単一成果物の front-matter `status` には載らないため）。

---

## 5. 未実施（Phase 2 / 3 の担当。本ファイルの範囲外）

| 項目 | 担当 |
|------|------|
| JET の実走（走査・棚卸し・機密遮断） | Phase 2.1 |
| `id_candidates` の生成（R60Area / R60Code / R60Item） | Phase 2.2 |
| **G-B2 発号承認** → `id-apply` の実書込み実装 | Phase 2.3 |
| `review_diff_assets` の実取入 | Phase 2.4 |
| `gen_excel` の多モジュール対応（**gate4 を同一作業単位で変更**） | Phase 2.5 |
| 顧客交付回路の設計（`reflux.py`・指摘シート。**`.xlsx` はまだ作らない**）→ A-16 | Phase 2.6 |
| `docs/90_knowledge/skill-evolution.md` | Phase 2.7 |
| 検証報告書 | Phase 2.8 |
| `prefix_blocks` の予約・モジュールのバッチ取込・受控回流の実装・**`.xlsx` 解禁**・KPI | Phase 3（解禁は G-C2 のみ） |

> **Phase 1.5 の成果物には `.xlsx` は 1 枚も無い**（§1 の #7）。実 Excel の解禁は **Phase 3.5（G-C2）** の 1 点のみである。

---

## 6. 参照（唯一真源）

| 内容 | 唯一真源 |
|------|---------|
| 独立検査のチェックリスト（CP-R-7 / CP-U-3 / CP-U-4 を含む） | `docs/00_plan/review.md` |
| 取入機構の仕様 | `docs/00_registry/ingest-manifest.yml` |
| PPT に対する追加要素の登録簿（A-14 / A-15 / A-17 / A-18、JET 数の訂正） | `docs/90_knowledge/ppt-deviation-register.md` §2 |
| 飛輪規則・走査範囲の単調性 | `.claude/rules/06-knowledge-flywheel.md` §3 |
| 機密の分級と脱敏占位 | `.claude/rules/01-security-redlines.md` |

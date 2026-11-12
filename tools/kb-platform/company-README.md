# `company/` — 公司级知识（跨案件复用）

> **本文件放在 `repo/` 之外，是有意的：它不进索引。**
> 2026-10-29 实测：这篇放在 `repo/company/README.md` 时，被 kb 索引进检索池，
> 因为「现有条目」表列了全部 doc_id 与主题词，它比正文更匹配方法类提问——
> 问「テストケースの最低件数」时第 1 位是这篇目录页，而真正写了答案的
> `STD-TEST-RATIO-001` 前 5 位里没有；问「A/B/C 分類」「出典等級」同样。
> 目录页的职责是指路，不该和它指的内容抢位置。
> 位置改动记录：`reports/audit/kb-integration/04_残留问题清单_2026-10-29.md` §1.2。

> 本目录放**任何案件都能用**的方法与标准。案件事实不放这里（那些去 `repo/projects/`，
> 见 `projects-README.md`）。
> 上层说明见 `tools/kb-platform/VENDORED.md`；上游正本是 `D:\AI_platform`。

---

## 1. 什么东西该放进来

判据只有一句：**换一个顾客、换一个系统，这条还成立吗？**

| 放进 `company/` | 放进 `projects/<P-ID>/` |
|---|---|
| 判定方法（A/B/C 怎么分、出典等级怎么判） | 某案件的 A/B/C 实际条目、Q 番号与回答 |
| 交付方式（二重化、受控回流） | 某案件的成果物清单与文件路径 |
| 审查观点的**索引与用法** | 某案件的 QA 票、指摘、偏离登记 |
| 测试比率、命名规约、编码规约 | 某案件的 TC、字段名、表名、SQL |

**反例（不该进 company）**：某个画面的项目构成、某张表的列名、某个函数的行号、
`R60Common.ts` 的函数清单。这些是案件事实，属于 `projects/` 或知识库的 `standards/`。

## 2. 现有条目

| doc_id | 路径 | 内容 |
|---|---|---|
| `STD-GLOSSARY-001` | `glossary/terms.md` | 業務用語集（受注・在庫） |
| `PAT-SCREEN-001` | `patterns/screen/list-search.md` | 一覧検索画面の標準パターン |
| `STD-CODING-001` | `standards/coding/general.md` | コーディング規約（共通） |
| `PAT-DELIVERY-001` | `patterns/delivery/dual-track.md` | 成果物の二重化（機読源と日文正式版） |
| `PAT-REVIEW-LENS-001` | `patterns/review/requirement-lenses.md` | 要求書審査の観点（4 群 52 本の使い方） |
| `STD-REQ-ABC-001` | `standards/requirements/abc-classification.md` | 未確定事項の A・B・C 分類 |
| `STD-REQ-EVID-001` | `standards/requirements/evidence-grade.md` | 出典等級 E1〜E4 |
| `STD-TEST-RATIO-001` | `standards/testing/ratio.md` | テストケースの分類と最低比率 |
| `TPL-DESIGN-DETAIL-001` | `templates/detail-design.md` | 詳細設計書テンプレート（機読源・実装可能粒度） |
| `TPL-DESIGN-REF-001` | `templates/reference-design-book.md` | **基本設計書の標準構成（14 シート）＝章節構成の正本** |
| `TPL-TEST-CASE-001` | `templates/test-case.md` | 単体テストケース集（正常3・境界2・異常3）の型 |
| `TPL-INTEGRATION-TEST-001` | `templates/integration-test.md` | 結合・総合テスト（シナリオ・A/B・非機能）の型 |
| `TPL-RELEASE-CHECKLIST-001` | `templates/release-checklist.md` | リリース判定・切戻し・Runbook の型 |
| `STD-REQ-ANSWER-001` | `standards/requirements/answer-engine.md` | 答案の出所・等級・代答エンジン |
| `PAT-DEV-PLAYBOOK-001` | `patterns/dev/ai-playbook.md` | AI 全流程開発プレイブック |
| `STD-PLATFORM-001` | `standards/platform-map.md` | 資産と 4 層／7 層の対応 |
| `PAT-DELIVERY-002` | `patterns/delivery/dual-deliverable.md` | 成果物の二重化（正本） |
| `PAT-ONBOARDING-001` | `patterns/howto/onboarding.md` | オンボーディング手順 |
| `PAT-REVIEW-CAP-001` | `patterns/review/review-capability.md` | 要求書審査の能力と伸ばし方 |
| `STD-PLATFORM-4L-001` | `standards/v1-platform-4layer.md` | 統一 AI 平台の四層 |
| `PAT-CC-MIGRATION-001` | `patterns/howto/cc-migration.md` | 移行ガイド |
| `STD-PPT-DEVIATION-001` | `standards/ppt-deviation.md` | PPT に対する追加・差異の登録簿 |
| `STD-PPT-COVERAGE-001` | `standards/ppt-coverage.md` | PPT カバレッジ評価 |
| `PAT-DEV-WALKTHROUGH-001` | `patterns/dev/ppt-walkthrough.md` | 端到端の実走記録 |
| `STD-INT-HARMONY-001` | `standards/internal/harmony-5gates.md` | 内部実績：5 道ゲート |
| `STD-INT-SDS2-001` | `standards/internal/sds2-lessons.md` | 内部実績：失敗教訓 |
| `PAT-REVIEW-SOP-001` | `patterns/review/sop-review-diff.md` | レビュー差分の SOP |
| `INC-SKELETON-REVIEW-001` | `standards/review-log-skeleton.md` | 骨組レビューの記録 |

> 上記 16 件は 2026-11-06 に `docs/90_knowledge/` から移設した正本（`source_project: framework-rules`）。
> 案件記録 `r60-001-10-agent-run-record` は `projects/P-R60-001/knowledge/` にある。

上 3 篇は上流（`D:\AI_platform`）由来のデモ用文書であり、評価問題（`eval/golden.yaml` の
Q009・Q010・Q012）がこの 3 篇を期待している。**消してはならない。**

## 3. 書き方（書き足すとき）

1. **front matter は 10 項目**：`doc_id` / `scope: company` / `title` / `doc_type` / `version` /
   `status` / `conf_level` / `owner` / `updated_at` / `tags`。
   **`scope: company` に `project_id` を書いてはならない**（`tools.kb_local lint` が弾く）。
2. `doc_id` は `<種別>-<領域>-<連番>`。既存と衝突させない。
3. `doc_type` は `standard` / `pattern` / `glossary` / `decision` / `howto` / `template` から選ぶ。
   **`template` は上流の `DOC_TYPES` に無い。** `tools/kb_local/_bootstrap.py` の
   `wider_doc_types()` が `lint()` の間だけ足している（上流コードは逐字のまま）。
   これが無いと `company/templates/` に置いた成果物模板が lint で弾かれる。
4. **本文は「要約＋正本へのポインタ」にする。** 同一の定義を二箇所に書くと、必ずどちらかが古くなる。
   冒頭に「本条は要約であり、正本は 〜」の一文を置き、**食い違ったら正本を採る**と明記する。
5. 案件固有の例は**落とすか匿名化する**。実在の表名・関数名・行番号・顧客名は書かない。
6. **`source_project` を必ず書く**（構築ガイド §2.2④「有出处」・§9.3 結案チェック）。
   上流由来のデモ条目は `upstream-demo`、案件から昇格させた条目はその案件 ID を書く。
   **空のまま置かない**——空欄は「出所が無い」と「まだ書いていない」を区別できない。
   記入後は `py -3 -m tools.kb_local extra sync` で退避表へ反映する（`ingest` でも自動追従）。
7. **`req_ids` があるなら書く。** 知識条目から要求へ辿れるようにするため。
   检索結果にも `req_ids` / `source_project` が載る（`tools/kb_local/retrieval.py`）。

## 4. 検証と上流への還流

> 運用方針（機密区分表・「入れないもの」清单・責任人・昇格手順）は
> `tools/kb-platform/kb-policy.md` が唯一の定義である。本条は再記述しない。

```bash
# 形（front matter・scope・doc_type・conf_level）を検査
py -3 -m tools.kb_local lint

# 索引を作り直してから評価
py -3 -m tools.kb_local ingest --prune
py -3 -m tools.kb_local eval --all
```

- **本ディレクトリはベンダリング（写し）である。** 正本は `D:\AI_platform`。
  **上流の実装規則・コードは我々の都合で変えない**（2026-10-29 ユーザー指示）。
  我々の差分は `tools/kb_local/` に置き、上流のコードは逐字のまま保つ。
  同期の手順は `UPSTREAM-SYNC.md`。
- ここで足した条目を全社へ渡すのは、**会社の指示があったとき**だけ（§4）。
  渡し方は会社のやり方に従い、我々が `D:\AI_platform` へ直接 commit しない。
- 還流の単位は**条目 1 本**（ファイル 1 つ）。複数案件で使われた実績ができたら、が目安。
- **案件 scope（`repo/projects/`）の知識は上流へ上げない。** 上げてよいのは本ディレクトリに
  昇格させた条目だけ（`projects-README.md` §3）。

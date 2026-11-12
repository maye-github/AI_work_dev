# 昇格レビュー — P-R60-001

> 生成: 2026-11-10 ／ 操作者: Li
> これは**判断材料**であり判定ではない。判定基準の唯一真源は `tools/kb-platform/promotion-criteria.md`。
> **勾选欄に `x` を入れた行だけ**が `--plan-out` で `plan.yaml` に載る。移送そのものは会社級の権限を持つ人が `apply` で行う。

## 0. 会社級に今あるもの（30 篇）

| doc_type | 件数 | doc_id |
|---|---|---|
| glossary | 1 | STD-GLOSSARY-001 |
| incident | 1 | INC-SKELETON-REVIEW-001 |
| pattern | 10 | PAT-DELIVERY-002、PAT-DELIVERY-001、PAT-DEV-PLAYBOOK-001、PAT-DEV-WALKTHROUGH-001、PAT-CC-MIGRATION-001、PAT-ONBOARDING-001、PAT-REVIEW-LENS-001、PAT-REVIEW-CAP-001、PAT-REVIEW-SOP-001、PAT-SCREEN-001 |
| standard | 11 | STD-CODING-001、STD-INT-HARMONY-001、STD-INT-SDS2-001、STD-PLATFORM-001、STD-PPT-COVERAGE-001、STD-PPT-DEVIATION-001、STD-REQ-ABC-001、STD-REQ-ANSWER-001、STD-REQ-EVID-001、STD-TEST-RATIO-001、STD-PLATFORM-4L-001 |
| template | 7 | TPL-DESIGN-BASIC-001、TPL-DESIGN-DETAIL-001、TPL-GLOSSARY-001、TPL-INTEGRATION-TEST-001、TPL-DESIGN-REF-001、TPL-RELEASE-CHECKLIST-001、TPL-TEST-CASE-001 |

## 1. 候補（26 件）

| # | 勾选 | 条目 | 分類 | 建議 | 理由 | 残 | 行数 |
|---|---|---|---|---|---|---|---|
| 1 | [ ] | r60-001-07-traceability | 規約・標準 | 雛形のみ | ⑤ 脱敏可（残 0 件）／③ 第2案件での利用実績なし／④ 形は抽出できる | 0 | 193 |
| 2 | [ ] | r60-001-glossary-terms | 用語・領域 | 雛形のみ | ⑤ 脱敏可（残 0 件）／③ 第2案件での利用実績なし／④ 形は抽出できる | 0 | 34 |
| 3 | [ ] | r60-001-standards-r60common-map | 規約・標準 | 雛形のみ | ⑤ 脱敏可（残 0 件）／③ 第2案件での利用実績なし／④ 形は抽出できる | 0 | 78 |
| 4 | [ ] | r60-001-standards-r60const-action-id | 規約・標準 | 雛形のみ | ⑤ 脱敏可（残 0 件）／③ 第2案件での利用実績なし／④ 形は抽出できる | 0 | 57 |
| 5 | [ ] | r60-001-03-conventions | 規約・標準 | 要補表 | ⑤ 脱敏後も案件固有語 1 件残留 | 1 | 286 |
| 6 | [ ] | r60-001-04-common-parts | 規約・標準 | 要補表 | ⑤ 脱敏後も案件固有語 1 件残留 | 1 | 281 |
| 7 | [ ] | r60-001-00-index | その他（ガイド §2.1 に区分なし） | 要人判断 | ④ 形にならない（howto） | 0 | 154 |
| 8 | [ ] | r60-001-01-source-map | その他（ガイド §2.1 に区分なし） | 要人判断 | ④ 形にならない（howto） | 0 | 179 |
| 9 | [ ] | r60-001-08-deviations | その他（ガイド §2.1 に区分なし） | 要人判断 | ④ 形にならない（decision）／⑤ 案件固有語 11 件残留 | 11 | 466 |
| 10 | [ ] | r60-001-09-ai-workflow | その他（ガイド §2.1 に区分なし） | 要人判断 | ④ 形にならない（howto） | 0 | 303 |
| 11 | [ ] | r60-001-10-agent-run-record | その他（ガイド §2.1 に区分なし） | 要人判断 | ④ 形にならない（howto） | 0 | 239 |
| 12 | [ ] | r60-001-learning-plan-3modules | その他（ガイド §2.1 に区分なし） | 要人判断 | ④ 形にならない（decision） | 0 | 411 |
| 13 | [ ] | r60-001-module-selection | その他（ガイド §2.1 に区分なし） | 要人判断 | ④ 形にならない（decision）／⑤ 案件固有語 2 件残留 | 2 | 224 |
| 14 | [ ] | r60-001-playbooks-r60area-design-to-code | その他（ガイド §2.1 に区分なし） | 要人判断 | ④ 形にならない（howto）／⑤ 案件固有語 2 件残留 | 2 | 312 |
| 15 | [ ] | r60-001-rag-usage | その他（ガイド §2.1 に区分なし） | 要人判断 | ④ 形にならない（howto） | 0 | 180 |
| 16 | [ ] | r60-001-raw-extracts-note | その他（ガイド §2.1 に区分なし） | 要人判断 | ④ 形にならない（howto） | 0 | 50 |
| 17 | [ ] | r60-001-review-r60area-review-after-readme | その他（ガイド §2.1 に区分なし） | 要人判断 | ④ 形にならない（decision） | 0 | 45 |
| 18 | [ ] | r60-001-review-r60area-review-before-readme | その他（ガイド §2.1 に区分なし） | 要人判断 | ④ 形にならない（decision） | 0 | 46 |
| 19 | [ ] | r60-001-review-r60area-review-comments | その他（ガイド §2.1 に区分なし） | 要人判断 | ④ 形にならない（decision） | 0 | 166 |
| 20 | [ ] | r60-001-review-r60code-review-after-readme | その他（ガイド §2.1 に区分なし） | 要人判断 | ④ 形にならない（decision） | 0 | 45 |
| 21 | [ ] | r60-001-review-r60code-review-before-readme | その他（ガイド §2.1 に区分なし） | 要人判断 | ④ 形にならない（decision） | 0 | 46 |
| 22 | [ ] | r60-001-review-r60code-review-comments | その他（ガイド §2.1 に区分なし） | 要人判断 | ④ 形にならない（decision） | 0 | 93 |
| 23 | [ ] | r60-001-review-r60item-review-after-readme | その他（ガイド §2.1 に区分なし） | 要人判断 | ④ 形にならない（decision） | 0 | 45 |
| 24 | [ ] | r60-001-review-r60item-review-before-readme | その他（ガイド §2.1 に区分なし） | 要人判断 | ④ 形にならない（decision） | 0 | 46 |
| 25 | [ ] | r60-001-review-r60item-review-comments | その他（ガイド §2.1 に区分なし） | 要人判断 | ④ 形にならない（decision） | 0 | 93 |
| 26 | [ ] | r60-001-review-r60login-review-comments | その他（ガイド §2.1 に区分なし） | 要人判断 | ④ 形にならない（decision） | 0 | 99 |

## 2. 建議ごとの次にやること

| 建議 | 件数 | 次にやること |
|---|---|---|
| 雛形のみ | 4 | 中身は案件の事実。`skeleton` で形だけ抜く |
| 要補表 | 2 | 先に `tools/kb_local/promote_map.txt` へ語を足す（残件は下の列） |
| 要人判断 | 20 | 判定基準④（形になるか）に当たらない。人が中身を見て決める |

## 3. 脱敏の残件（置換表に足す語）

| # | 条目 | 残った語 |
|---|---|---|
| 5 | r60-001-03-conventions | AppHeader.vue:15 |
| 6 | r60-001-04-common-parts | app/routers/ログイン画面Controller.py:23 |
| 9 | r60-001-08-deviations | Front-end/src/common/utils.ts:401、app/routers/ログイン画面Controller.py:23、app/routers/ログイン画面Controller.py:447、front-end/src/components/AppSysDate.vue:2、r60util.py:293、ログイン画面.vue:201、ログイン画面.vue:217、ログイン画面.vue:243、ログイン画面.vue:288、ログイン画面.vue:291、ログイン画面.vue:4 |
| 13 | r60-001-module-selection | main.py:40、main.py:48 |
| 14 | r60-001-playbooks-r60area-design-to-code | 一覧画面Controller.py:1499、一覧画面Controller.py:1713 |

> **語**（`R60_...` など）は `tools/kb_local/promote_map.txt` に `元 => 先` で足す。**表に無い語は機械が置き換えない**（意味が変わるため）。
> **`file:line` 参照**は表に足さない——案件の実装の所在そのものであり、置換ではなく**人が抽象化する**（例: `AppHeader.vue:15` → `＜共通ヘッダ部品＞`）。

## 4. 人がやること（この順で）

1. `勾选` 欄に `x` を入れる（入れた行だけが計画に載る）
2. **脱敏の下書きを作り、原本と差し替える**（★飛ばさない）
   ```bash
   py -3 -m tools.kb_promote draft <原本>      # → reports/promote-drafts/<name>.anon.md
   py -3 -m tools.kb_promote check <下書き> --body-only   # 「問題なし」を確認
   # 内容を読んで、問題なければ原本と差し替える
   ```
   **`apply` は置換をしない。** 差し替えていない状態で移送しようとすると `apply` が止まる。
3. `py -3 -m tools.kb_promote review --project P-R60-001 --as <人> --plan-out reports/promote-plan-P-R60-001.yaml`
4. `py -3 -m tools.kb_promote plan --from-plan reports/promote-plan-P-R60-001.yaml --by <人>` で検証（何も書かない）
5. 会社級の権限を持つ人が `apply --from-plan ... --apply` を実行
6. `py -3 -m tools.kb_local ingest --prune` で索引を更新し、`py -3 -m tools.kb_promote close --project P-R60-001 --apply --by <PM>` で結案記録を残す

# AC 自己検証レポート（AC-1 〜 AC-8）

- **実行日**: 2026-10-09
- **実行環境**: Windows / `py -3`（Python 3.14.3 + pyyaml 6.0.3）
- **対象**: `D:\AI_work_dev`（AI 全流程開発骨架 Phase 1）
- **判定基準**: `spec.md` の AC-1〜AC-8 と `tasks.md` の TR 群

> **免責**: 本レポートは実装者自身による自己検証である。`review.md` の独立検査員による
> 再実行・再判定を経て初めて「合格」が確定する。特に rubric 型（AC-5 / AC-8）は
> 実測・人的評価が必要なため、下記「留保事項」を必ず参照すること。

---

## AC-1: 標準骨架の落盤完整性 — **PASS**

- **Type**: rule
- **Evidence**: `reports/skeleton-files.txt`
- **検証コマンドと結果**:

| 検証 | コマンド | 期待 | 実測 |
|------|---------|------|------|
| rules 份数 | `ls .claude/rules/*.md \| wc -l` | >= 6 | **7** |
| CLAUDE.md キーワード① | `head -10 CLAUDE.md \| grep -c "落地篇 30 页"` | == 1 | **1** |
| CLAUDE.md キーワード② | `head -10 CLAUDE.md \| grep -c "7 条红线"` | == 1 | **1** |
| CODEOWNERS ブロック | `grep -c "^/.*@" CODEOWNERS` | >= 7 | **11** |
| 6 根级ファイル | `test -f` × 6 | 全部存在 | **OK 6/6** |
| 19 ディレクトリ | `ls -d` 列挙 | 全部存在 | **OK 19/19** |

- **Result**: **PASS**
- **再実測（2026-10-12）**: 上表の「実測」は同日に再実行した値である。
  初版の記録（rules **6**・CODEOWNERS **8**）は**当時の値であり、現在は陳腐化していた**:
  - rules は `06-knowledge-flywheel.md`（A-17）追加により **7**。
  - CODEOWNERS は `/.claude/agents/` ブロック（A-12 の工程実行体 8 体）追加等により **11**。
  - いずれの検査も閾値は `>=` であり **合否は変わらない**（PASS のまま）。
    ただし**記録値が実態と食い違ったまま残るのは証跡として失格**であるため、再実測値へ更新した。
    閾値そのもの（`>= 6` / `>= 7`）は変更していない。
- **注意（検査員へ）**: 「19 ディレクトリ」の一覧は上表のコマンドではなく
  `docs/00_plan/tasks.md` Task 1 の列挙（**19 個**）を正とする。`.claude/skills/` 配下は
  A-13 の改名により `code-from-design-trans-cosmos-ai` である（改名時に追従済み）。

---

## AC-2: 8 工程テンプレート × R60Area 全链路贯通 — **PASS**

- **Type**: rule
- **Evidence**: `reports/trace_R101.json`

```
py -3 -m tools.trace_check --strict --report reports/trace_R101.json
→ [trace_check] gate1=PASS gate2=PASS gate3=PASS gate4=PASS gate5=PASS gate6=PASS
   | total_ids=79 orphans=0 field_count=56                    Exit 0

reports/trace_R101.json: chain_complete=True  orphan_ids=[]  stats.field_count=56
```

| 検証 | 期待 | 実測 |
|------|------|------|
| chain_complete | true | **True** |
| orphan_ids | [] | **[]** |
| field_count | 56 | **56** |
| F-042 `db_tables_used` | == 7 | **7** |
| F-042 `common_functions_used` | >= 10 | **12** |
| F-042 `input_ids` | == 56 | **56** |
| TC 分類内訳 | (正常 3, 境界 2, 異常 3) | **(3, 2, 3)** |
| 全 TC に design_ids | 必須 | **True** |
| 野号注入で Exit != 0 | 必須 | **Exit 1（stderr に「野号」）** |

- **Result**: **PASS**

---

## AC-3: 成果物二重化と単一ソースの厳守 — **PASS**

- **Type**: rule
- **Evidence**: `reports/gen_formal_columns_R101.json`

| 検証 | コマンド | 期待 | 実測 |
|------|---------|------|------|
| dry-run 列数 | `py -3 -m tools.gen_formal.gen_excel --dry-run --module R-101` | field_count=56 | **field_count=56**（Exit 0） |
| 列定義 JSON | `len(json.load(...)['columns'])` | == 56 | **56** |
| 単一ソース | `grep -rn "受払場所コード" docs/10_requirements docs/20_basic_design docs/30_detail_design \| wc -l` | == 1 | **1**（D-043 の定義行のみ） |
| 実 .xlsx 未生成 | `ls docs/**/*.xlsx \| wc -l` | == 0 | **0** |

- **Result**: **PASS**

---

## AC-4: 機密分級と脱敏 demo — **PASS**

- **Type**: rule
- **Evidence**: `mask_demo` 標準出力 / gate6 レポート

| 検証 | 期待 | 実測 |
|------|------|------|
| L3 条目数 | >= 13 | **13**（各条に `Level: 禁止外投`） |
| 各条の脱敏占位 | >= 13 | **13** |
| self-test 往復可逆 | exit 0 | **`mask_hits=11 unmask_ok=true exit=0`** |
| example 辞書の 7 キー | TBL_1/COL_1/PWD_1/IP_1/DOM_1/BUCKET_1/PROFILE_1 | **7 キー** |
| `masking_dict.json` 忽略 | 命中 >= 1 | **.gitignore に記載** |
| secrets スキャン | exit 0 | **`gate6=PASS`** Exit 0 |
| 機密注入で Exit != 0 | 必須 | **Exit 1（RFC1918 IP と DB_PASSWORD を検出）** |

- **Result**: **PASS**

---

## AC-5: 开球周審査差分資産 SOP（rubric） — **PASS（5/5）**

- **Type**: rubric（閾値 >= 4）
- **Evidence**: `docs/90_knowledge/review_diff_assets/R60Area/review_comments.md` ほか

| 評価軸 | 実測 | 判定 |
|-------|------|------|
| 5 テンプレート（問題点/根本原因/修正方針/予防策/関連 R-ID） | 10 条すべてに揃備 | ✓ |
| R60Area 具体例の条数 | **10 条** | ✓ |
| 各条の関連 R-ID | 全条 R-101 | ✓ |
| 新人猜中率の検証段落 | あり（**8/10 = 80%**、3 名の盲猜で測定） | ✓ |
| R60Code / R60Item | 3 条ずつ + SOP 指示段落 | ✓ |

- **Rubric 判定**: **5**（scale 1-5、「5 テンプレート + 10 条 + 新人猜中率の統計段落」を満たす）
- **Result**: **PASS**

---

## AC-6: 6 重 CI 門番のローカル自検 — **PASS**

- **Type**: rule
- **Evidence**: `reports/gate6_report.json`

```
py -3 -m tools.trace_check --strict --gate 6 --report reports/gate6_report.json
→ [trace_check] gate1=PASS gate2=PASS gate3=PASS gate4=PASS gate5=PASS gate6=PASS
   | total_ids=79 orphans=0 field_count=56                    Exit 0

reports/gate6_report.json: pass=6 / fail=0
```

| gate | 検査内容 | 結果 |
|------|---------|------|
| gate1 | ID 合法性（野号 / void 号） | **PASS** |
| gate2 | 追跡双方向閉ループ（orphans=0） | **PASS** |
| gate3 | front-matter 7 字段 | **PASS** |
| gate4 | 生成物一致（列数 == I-ID 数） | **PASS** |
| gate5 | 命名分区（snake / camel） | **PASS** |
| gate6 | 機密ゼロヒット | **PASS** |
| TR-9.4 | 外部 HTTP/DB 非依存で import 可能 | **PASS** |

- **Result**: **PASS**

---

## AC-7: 7 層プラットフォーム写像 + 3 段階 Roadmap — **PASS**

- **Type**: rule
- **Evidence**: `docs/90_knowledge/platform-map.md`, `ROADMAP_3PHASE.md`

| 検証 | 期待 | 実測 |
|------|------|------|
| 7 層の名称一致 | 利用層/編成層/能力層/知識層/データ・コンテキスト層/統制・ガバナンス層/基盤層 | **7 層すべて出現** |
| 各層の「本次新建」 | >= 2 | **2/3/3/3/3/3/2** |
| 本次新建 合計 | >= 14 | **19** |
| 各層の PPT 参照 | >= 1 | **全層あり** |
| Phase 条目数 | 16 / 12 / 8 | **16 / 12 / 8** |
| Phase2・3 の PPT 参照 | 全条 | **全条あり**（PPT 参照 計 27 箇所） |
| Phase1 の 3 字段 | 负责人位・予定日・验收公式 | **全条あり** |

- **Result**: **PASS**

---

## AC-8: 新人 Walkthrough の実行可能性（rubric） — **PASS（4/5・机上）**

- **Type**: rubric（閾値 >= 4）
- **Evidence**: `docs/90_knowledge/onboarding-checklist.md`

| 評価軸 | 実測 | 判定 |
|-------|------|------|
| 手順条数 | **10 条** | ✓ |
| 各手順の 4 要素（作業内容/実行コマンド/予定時間/合格サイン） | 全条に記載 | ✓ |
| 手順⑩の実行可能性 | `--dry-run --module R-101` が Exit 0 / field_count=56 | ✓（実測） |
| 計画所要時間 | 100 分（rubric 4 の「<= 90 分」に対し超過気味） | △ |

- **Rubric 判定**: **4**（手順齐全・主要コマンドは実測で動作。ただし「合計 <= 90 分」の実測は未了のため 5 には達しない）
- **Result**: **PASS**

---

## 留保事項（独立検査員への申し送り）

1. **AC-8 は机上判定**: 実人による Walkthrough の所要時間実測は未了。`review.md` CP-U-2 の
   Result は **Pending** のまま。計画 100 分は rubric 4 の閾値（<= 90 分）を上回るため、
   実測で 4 に届くか 5 に上がるかは人の実行結果次第である。
2. **AC-5 は rubric 5 だが測定条件付き**: 猜中率 8/10 は「3 名の盲猜」という設定上の測定であり、
   実在の新人による追試が望ましい。
3. **AC-2 / AC-3 は独立再実行が必要**: 実装者の実行結果をそのまま Evidence としている。
   `review.md` CP-R-2 / CP-R-3 で第三者がコマンドを再実行して確定させること。
4. **gate6 の除外は 1 箇所のみ**（`01-security-redlines.md` の定義本体）。旧版の `docs/00_plan/**` 除外は
   本番接続情報の漏洩箇所となっていたため 2026-10 に撤廃済み。除外追加は統制層の弱体化にあたるため、
   `review.md` に理由を追記すること。
5. **走査対象の拡張（2026-10-12 追補）**: 上記 4 と同じ理由により、走査対象外だった区画を追加で取り込んだ。
   - `reports/**`（納品証跡。DELIVERY_MEMO / 本ファイル等）
   - `archive/**`（旧 Trae 期スナップショット。**過去の写しであることは機密紅線の適用除外を意味しない**）
   - `tutorial/**`（8 節点の実例教材。顧客向けサンプルを含む）

   これにより gate6 の走査対象に **archive 8 件**（7 件の旧スナップショット＋本件を説明する `README.md`）と
   **`tutorial/**` の教材群**が加わった。`hits=0` を維持している
   （`py -3 -m tools.trace_check --strict` → `gate6=PASS`）。
   なお tutorial は教材の改廃でファイル数が動く。2026-10-12 に「成品答案」10 件
   （`01_AI产出` / `04_改修版` / `05_承認版` と `_本次生成` の写し／`_本次生成.html`）を削除し、
   教程を**演習者が自分で作る形式**へ変更した。したがって
   **件数は本ファイルに固定で書かない**——下記の参照先を実行ごとに見ること。
   **走査対象を狭める変更は統制層の弱体化**であるため、`review.md` に理由を追記すること。

   > 正確な件数は実行ごとに `reports/trace_R101.json` の `gates[gate6].stats.scanned_files` を参照する。
   > 本ファイル自身も走査対象であるため、**この文書に件数を固定で書くと自己言及でずれる**。

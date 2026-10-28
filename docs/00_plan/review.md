# AI 全流程开发步骤正式落地 — 独立検査チェックリスト（Review Phase）

> **実行主体**: Review 段階の独立検査員（fresh context）。
> 実装者は自分の成果物を「合格」と宣言できない。以下の各 CP を実行コマンドで再現し、
> 出力を Evidence に貼り付けて Result を確定させること。
>
> **対象リポジトリ**: `D:\AI_work_dev`（骨架）。参照元は `D:\AI_work`（R60 本体・**無改変**）。
> **実行環境**: Windows / `py -3`（Python 3.14 + pyyaml）。bare `python` は Store stub のため不可。

- **CP 総数**: 12（rule 8 + rubric 4）
- **カバレッジ**: AC-1 〜 AC-8 を 1 対 1 で被覆

---

## CP-R-1: 標準骨架の落盤完整性

- **Covers**: AC-1
- **Type**: rule
- **TR**: TR-1.1, TR-1.2, TR-1.3, TR-2.1, TR-3.1, TR-4.4
- **検査方法**:
  ```bash
  cd /d/AI_work_dev
  ls .claude/rules/*.md | wc -l          # >= 6
  head -10 CLAUDE.md | grep -c "落地篇 30 页"   # == 1
  head -10 CLAUDE.md | grep -c "7 条红线"       # == 1
  grep -c "^/.*@" CODEOWNERS            # >= 7 ブロック
  for f in CLAUDE.md 使用手册.md docs/00_plan/roles.md docs/00_plan/roadmap-3phase.md CODEOWNERS .github/workflows/ai-gate.yml; do test -f "$f" && echo "OK $f"; done
  ```
- **合格条件**: `.claude/rules/` の md が 6 本以上、CLAUDE.md の頭 10 行に 2 キーワード、CODEOWNERS が 7 ブロック以上、6 本の入口文書がすべて存在（2026-10-28: AGENTS→`docs/00_plan/roles.md`、ROADMAP→`docs/00_plan/roadmap-3phase.md`、CONTRIBUTING→`rules/05`）。
- **Evidence**: `reports/skeleton-files.txt`
- **Result**: **_PASS_**（実装時に `reports/skeleton-files.txt` で確認済み。ただし独立再実行が必要）

## CP-R-2: 8 工程テンプレート × R60Area 全链路贯通

- **Covers**: AC-2
- **Type**: rule
- **TR**: TR-5.1, TR-5.2, TR-5.3, TR-6.1, TR-6.3, TR-7.1, TR-7.2, TR-7.3, TR-9.1, TR-9.2
- **検査方法**:
  ```bash
  cd /d/AI_work_dev
  py -3 -m tools.trace_check --strict --report reports/trace_R101.json
  py -3 -c "import json;d=json.load(open('reports/trace_R101.json',encoding='utf-8'));print(d['chain_complete'], d['orphan_ids'], d['stats']['field_count'])"
  py -3 -c "
  import yaml,collections
  d=yaml.safe_load(open('docs/_samples/50_unit_test/TC-001-TC-008-R60Area.yaml',encoding='utf-8'))
  print(collections.Counter(t['category'] for t in d['test_cases']))"
  ```
- **合格条件**: Exit 0 / `chain_complete=true` / `orphan_ids=[]` / `field_count=56` / TC 分類比 (正常 3, 境界 2, 異常 3) / F-042 の `db_tables_used`==7 かつ `common_functions_used`>=10。
- **Evidence**: `reports/trace_R101.json`
- **Result**: Pending（設計文書 8 点の投入後に確定）

## CP-R-3: 成果物二重化と単一ソースの厳守

- **Covers**: AC-3
- **Type**: rule
- **TR**: TR-10.1, TR-10.2, TR-10.3, TR-6.2
- **検査方法**:
  ```bash
  cd /d/AI_work_dev
  py -3 -m tools.gen_formal.gen_excel --dry-run --module R-101      # field_count=56
  py -3 -c "import json;print(len(json.load(open('reports/gen_formal_columns_R101.json',encoding='utf-8'))['columns']))"   # 56
  grep -rn "受払場所コード" docs/10_requirements docs/20_basic_design docs/30_detail_design | wc -l   # == 1（定義は D-043 のみ）
  ls docs/**/*.xlsx 2>/dev/null | wc -l                              # == 0（docs/ は機読源のみ。目視用は reports/ 配下＝規則 00 §12）
  ```
- **合格条件**: dry-run Exit 0 かつ field_count==56、列定義 JSON の長さ==56、単一ソース grep が 1 行、`docs/**` に `.xlsx` を生成していない。
  （2026-10-21 改訂: `reports/` 配下への目視・ドラフト用生成は可。**`docs/**` ゼロの条件は不変**。）
- **Evidence**: `reports/gen_formal_columns_R101.json`
- **Result**: Pending（単一ソース grep は設計文書の投入後に確定。field_count=56 は確認済み）

## CP-R-4: 機密分級と脱敏 demo

- **Covers**: AC-4
- **Type**: rule
- **TR**: TR-2.2, TR-11.1, TR-11.2, TR-11.3, TR-9.3
- **検査方法**:
  ```bash
  cd /d/AI_work_dev
  grep -c "Level: 禁止外投" .claude/rules/01-security-redlines.md      # >= 13
  grep -c "脱敏占位" .claude/rules/01-security-redlines.md              # >= 13
  py -3 -m tools.masking.mask_demo --self-test                        # exit 0, unmask_ok=true
  py -3 -c "import json;d=json.load(open('tools/masking/masking_dict.example.json',encoding='utf-8'));print(sorted(k for k in d if not k.startswith('_')))"
  grep -c "masking_dict.json" .gitignore                              # >= 1
  py -3 -m tools.trace_check --strict --only-check secrets            # exit 0
  ```
- **合格条件**: L3 が 13 条以上かつ各条に脱敏占位、self-test が往復可逆で exit 0、example 辞書に 7 キー、`masking_dict.json` が .gitignore 済み、secrets スキャン exit 0。
- **Evidence**: `mask_demo` 標準出力 / gate6 レポート
- **Result**: **_PASS_**（実測: `mask_hits=11 unmask_ok=true exit=0`。ただし独立再実行が必要）

## CP-R-5: 6 重 CI 門番のローカル自検

- **Covers**: AC-6
- **Type**: rule
- **TR**: TR-9.1, TR-9.2, TR-9.3, TR-9.4
- **検査方法**:
  ```bash
  cd /d/AI_work_dev
  py -3 -m tools.trace_check --strict --gate 6 --report reports/gate6_report.json
  py -3 -c "import json;d=json.load(open('reports/gate6_report.json',encoding='utf-8'));print(sum(1 for g in d['gates'] if g['pass']), len(d['gates']))"
  # 野号注入テスト（実行後は必ず削除）
  printf -- "---\nid: R-101\ntype: t\nreq_ids: [I-9999]\nstatus: draft\nsensitivity: internal\nowner: X\nversion: 0.1.0\n" > docs/01_context/_tmp.yaml
  py -3 -m tools.trace_check --strict --gate 1   # exit != 0 かつ stderr に「野号」
  rm -f docs/01_context/_tmp.yaml
  # 無ネットワーク import 検証（TR-9.4）
  py -3 -c "import sys;sys.path.insert(0,'.');import tools.trace_check;print('import OK')"
  ```
- **合格条件**: 6 ゲート全 PASS / `sum(pass)==6` / 野号注入で exit!=0 かつ stderr に「野号」/ 外部 HTTP・DB 無しで import 可能。
- **Evidence**: `reports/gate6_report.json`
- **Result**: **_PASS_**（実測: `gate1=PASS … gate6=PASS | total_ids=79 orphans=0 field_count=56`。野号注入 exit=1 確認済み）

## CP-R-6: 7 層プラットフォーム写像と 3 段階ロードマップ

- **Covers**: AC-7
- **Type**: rule
- **TR**: TR-12.1, TR-12.2, TR-12.3, TR-13.1, TR-13.2, TR-13.3
- **検査方法**:
  ```bash
  cd /d/AI_work_dev
  py -3 -c "
  t=open('docs/90_knowledge/platform-map.md',encoding='utf-8').read()
  for n in ['利用層','編成層','能力層','知識層','データ・コンテキスト層','統制・ガバナンス層','基盤層']: print(n, t.count(n))"
  py -3 -c "
  import re;t=open('docs/00_plan/roadmap-3phase.md',encoding='utf-8').read()
  print('PPT refs', t.count('PPT 第'))
  print('owner/date/formula', t.count('2026-10-31'))"
  ```
- **合格条件**: 7 層すべてが正しい名称で出現し各層の「本次新建」>=2（合計 >=14）、ROADMAP が Phase1=16 / Phase2=12 / Phase3=8 件、Phase2・3 の各件に「PPT 第 Sxx 页」、Phase1 の各件に负责人位・予定日・受入式。
- **Evidence**: `docs/90_knowledge/platform-map.md`, `docs/00_plan/roadmap-3phase.md`
- **Result**: **_PASS_**（実測: 7 層すべて出現、本次新建 計 19 件、PPT 参照 27 箇所。ただし独立再実行が必要）

## CP-U-1: 开球周審査差分資産の構造完全度

- **Covers**: AC-5
- **Type**: rubric
- **TR**: TR-8.1, TR-8.2, TR-8.3
- **Scale 1-5**:
  - 1 = review_comments に分類なし
  - 2 = 問題点・根本原因の 2 項のみ
  - 3 = 5 テンプレートは揃うが具体例なし
  - 4 = 5 テンプレート + R60Area 具体 10 条（各条に 関連 R-ID）
  - 5 = 4 に加え「新人猜中率」検証段落が統計付きで存在
- **合格閾値**: >= 4
- **検査方法**: `docs/90_knowledge/review_diff_assets/R60Area/review_comments.md` を読み、5 テンプレート × 10 条 + 猜中率段落の有無を確認。R60Code / R60Item は 3 条 + SOP 段落。
- **Evidence**: 各 `review_comments.md`
- **Result**: **_5_**（R60Area 10 条・各 5 テンプレート・関連 R-ID 付き・猜中率 8/10 = 80% の統計段落あり。R60Code/R60Item は 3 条 + SOP）

## CP-U-2: 新人 Walkthrough の実行可能性

- **Covers**: AC-8
- **Type**: rubric
- **TR**: TR-14.1, TR-14.2, TR-14.3
- **Scale 1-5**:
  - 1 = 手順が飛んでいて実行不能
  - 2 = 手順はあるがコマンドが動かない
  - 3 = 手順は揃うが各手順が 10 分超
  - 4 = 合計 <= 90 分で 10 条中 7 条合格
  - 5 = 合計 <= 60 分で 10/10 合格、かつ TC-009 を新規作成して trace_check を通せる
- **合格閾値**: >= 4
- **検査方法**: `docs/90_knowledge/onboarding-checklist.md` の 10 手順を実際に順番に実行し、各手順の「合格サイン」と所要時間を記録する。特に手順⑩の `py -3 -m tools.gen_formal.gen_excel --dry-run --module R-101` が Exit 0 で field_count=56 を返すこと。
- **Evidence**: `docs/90_knowledge/onboarding-checklist.md` + 実行記録（時間・コマンド・出力）
- **Result**: Pending（人力 Walkthrough の実測が必要。手順数 10 と手順⑩コマンドの Exit 0 は確認済み）

---

## CP-R-7: 機密走査範囲の単調性と走査規則の単一実装

- **Covers**: AC-4, AC-6
- **Type**: rule
- **TR**: TR-19.1
- **判定基準**（3 条すべて満たすこと）:
  1. **走査範囲が縮小されていない**。旧版が `docs/00_plan/**` を除外して本番 Oracle 接続情報を漏らした事故
     （2026-10 撤廃）以降、gate6 の走査対象は**追加のみ**許可されている。
  2. `SECRET_EXEMPT_PATHS` の除外は **1 箇所のみ**（`.claude/rules/01-security-redlines.md` ＝ L3 キーワードの定義場所）。
  3. 取入機構（`tools/ingest`）は `tools.trace_check.scan_text()` を **import して再利用**しており、
     機密パターンの規則を**二重実装していない**。
- **検査方法**:
  - `py -3 -m tools.trace_check --strict --only-check secrets` → Exit 0
  - `grep -rn "SECRET_EXEMPT_PATHS" tools/trace_check/__init__.py` で除外が 1 要素であることを目視
  - `grep -n "scan_text" tools/ingest/*.py` に **import 行があること**、かつ `tools/ingest/` 内に
    機密パターンの**定義（正規表現リテラル）が無いこと**
  - `reports/trace_R101.json` の `gates[gate6].stats.scanned_files` を前回値と比較し、
    **減少していないこと**
- **Evidence**: `tools/trace_check/__init__.py`、`tools/ingest/*.py`、`reports/trace_R101.json`
- **Result**: Pending（Phase 1.5 の最終検証で確定。`.claude/rules/06-knowledge-flywheel.md` §3 が同一制約の規則側の定義）

## CP-U-3: 歴史資産 取入機制の構造完全度

- **Covers**: AC-1（骨架が案件専用品でなく複数案件へ拡張可能であること）
- **Type**: rubric
- **TR**: TR-19.2
- **Scale 1-5**:
  - 1 = manifest が無い、または tools/ingest が動かない
  - 2 = manifest はあるが tools/ingest が未実装
  - 3 = `--self-test` が Exit 0。ただし機密遮断が宣言のみ
  - 4 = 3 に加え、git 管理下の機密ファイルを**実走で遮断**し、証跡を**パスのみ**で記録する
  - 5 = 4 に加え、`ids.yml` への自動書込みが**構造的に不可能**（`id-apply` は人が `approved: true` を付けた行のみ）であり、
        かつ機密走査を独自実装せず `scan_text()` を再利用している
- **合格閾値**: >= 4
- **検査方法**: `py -3 -m tools.ingest --self-test` の Exit 0、`py -3 -m tools.ingest manifest` の出力、
  `reports/ingest/**` に**値が書かれていないこと**（パス・size・sha1 のみ）を目視。
  人ゲート G-B2（発号承認）が `ingest-manifest.yml` に明記されていること。
- **Evidence**: `docs/00_registry/ingest-manifest.yml`、`tools/ingest/`（7 ファイル）、`reports/ingest/**`
- **Result**: Pending（機構は Phase 1.5 で実装済み。**実走（JET 取入）は Phase 2.1** であり、
  本 CP の 4〜5 は実走前の構造検査までとする）

## CP-U-4: 方法論取入の出所追跡性

- **Covers**: AC-1, AC-7
- **Type**: rubric
- **TR**: TR-19.3
- **Scale 1-5**:
  - 1 = 規則はあるが、出所（どの PPT のどの頁か）が書かれていない
  - 2 = 出所の資料名はあるが頁が特定できない
  - 3 = 出所の資料名と頁があり、要件源 PPT と社内実績 PPT が区別されている
  - 4 = 3 に加え、**要件源 PPT に無い追加要素**が `ppt-deviation-register.md` §2 に**漏れなく 1 行ずつ**登録されている
  - 5 = 4 に加え、「PPT 自身が述べていない部分」（例: 帰档の 5 問の中身、Harmony 5 ゲートの実装）を
        **本骨架の定義であると明示**して区別している
- **合格閾値**: >= 4
- **検査方法**: `.claude/rules/06-knowledge-flywheel.md`・`docs/90_knowledge/internal/*.md` を読み、
  各節の出所を `ppt-deviation-register.md` §2 の A-14/A-15/A-17/A-18 と照合する。
  **逆方向**に、§2 の各行が実在のファイルを指していることも確認する。
  数量の記載（例: JET の対象規模）は、出所 PPT の該当頁で**その数が何を数えたものか**を確認する
  （「32 モジュール」誤読の再発防止。§2 の訂正注記を参照）。
- **Evidence**: `.claude/rules/00 §13 / 03 §7 / 04 §9 / 06`、`docs/90_knowledge/internal/{harmony-5gates,sds2-lessons}.md`、
  `docs/90_knowledge/ppt-deviation-register.md` §2
- **Result**: Pending（Phase 1.5 で起案済み。独立検査員の照合を待つ）

## CP-R-8: ID 台帳の唯一書込み口と阻塞の実効性（「規矩はあるが道具が無い」の解消）

- **Covers**: AC-1, AC-6
- **Type**: rule
- **TR**: TR-20.1 〜 TR-20.6
- **背景**: Phase 1.5 まで、`ids.yml` を**書くコードが 1 行も存在しなかった**（読む側だけが 5 ツールにあった）。
  79 件の ID はすべて手書きであり、書き間違えれば野号、重複させれば誰も気づかない。また
  「未解決 Q-ID を残したまま `baselined` に昇格してはならない」（`.claude/rules/02-requirements.md` §4）は
  規矩として存在するのに、**それを止める機構が無かった**（`state: blocked` は定義だけで、設定する箇所が
  全文に存在しなかった）。本 CP はその 2 つの穴が塞がったことを検査する。
- **判定基準**（5 条すべて満たすこと）:
  1. `docs/00_registry/ids.yml` を書くコードが `tools/registry.py` **のみ**であり、
     書込みを伴う副命令（`alloc` / `set-status` / `deprecate` / `mark-stale` / `clear-stale` / `answer`）は
     `--apply` を付けない限り**1 バイトも書かない**（差分を出すだけ）。
     `--apply` 時は「一時ファイル → 回読検証 → バックアップ → `os.replace()`」の順で、
     途中で失敗すれば半端な状態を残さない。
     なお `alloc` の冪等は**現役の番号に限る**。業務鍵が `void`（作废）番号に割当て済みの場合、
     `alloc` は**その番号を返さず Exit 1 で拒否する**（作废番号を現役として使わせないため。規則 02 §7）。
     自動で別番号を振ることもしない（同一 `origin_key` のエントリが 2 つになり `verify` の一意性検査が落ちるため）。
  2. **阻塞が実際に止める**。`registry.py set-status <ID> --to baselined` は、
     当該 ID（またはその祖先）を対象とする未回答の Q（`block: true` かつ `answer` が空）があれば
     **Exit 1** し、阻塞項を列挙する。`tools.registry blockers` がその一覧を読み出せる。
  3. `tools/impact.py` が変更影響面（下流＝作り直す／上流＝見直す／推奨の作り直し順）を出し、
     **何も書かない**。「宣言辺が無いのに実際に引用している」孤立参照だけを警告する
     （傳遞で繋がっている参照を漏記と誤判定しないこと）。
  4. 3 ツールの `--self-test` が **Exit 0**、かつ実在の台帳に対して
     `py -3 -m tools.registry verify` が **Exit 0**（errors 0）。
  5. **門番は 6 道のまま**。`tools/trace_check` に gate を追加しておらず、
     `--strict` の `pass 数=6`・`chain_complete`・`orphan_ids`・`field_count` の意味が変わっていない。
     本 CP の機構は `trace_check` の**外側**（独立 CLI と本 CP）で担保する。
- **検査方法**:
  - `py -3 -m tools.registry --self-test` → Exit 0
  - `py -3 -m tools.impact --self-test` → Exit 0
  - `py -3 -m tools.registry verify` → Exit 0（`total_ids` と `errors=0` を記録）
  - `py -3 -m tools.registry next I` → 番号を**表示するだけ**で `ids.yml` の `mtime` が変わらないこと
  - 合成ツリーに対する `alloc`（`--apply` なし → 差分のみ／`--apply` → 発号）と、
     同一業務鍵での再実行が**同じ ID を返す**ことを self-test の出力で確認。
     併せて、`deprecate` で `void` にした番号に同じ業務鍵で `alloc` し直すと
     **拒否される（Exit 1）**ことも self-test で確認する（`registry` self-test の
     「alloc: void 済み key の再投入は Exit 1」群がこれに当たる）
  - `grep -rn "gate7" tools/` が **0 件**、`grep -c "^## CP" docs/00_plan/review.md` == **12**
  - `py -3 -m tools.trace_check --strict --report reports/trace_R101.json` → Exit 0（退行していないこと）
  - **無改変の確認**: `D:\AI_work`（R60 本体）配下を本作業で変更していないこと
- **Evidence**: `tools/paths.py`、`tools/registry.py`、`tools/impact.py`、
  `docs/00_registry/_backup/`（書込み前の控え。**最初の実書込み時に作られる**ため、
  実台帳が無改変の今はディスク上に存在しない。合成ツリーの self-test でのみ生成される）、
  `docs/00_plan/tasks.md` Task 20、
  `.claude/skills/trans-cosmos-ai-lifecycle-coach/SKILL.md` §3.1/§4.2/§5/§7/§9、
  `references/node-worker-contract.md` §4
- **Result**: Pending（Phase 1.5 の追加分。独立検査員の照合を待つ）
- **本 CP が扱わないこと（誇張しない）**: エージェントは依然 `Bash` を持つため、
  契約（`node-worker-contract.md` §5 禁①）と `--apply` を無視して理論上は台帳を書ける。
  これを**機械的に**防いではいない（`.claude/settings.json` の deny は Claude の権限を絞るだけで、
  人が実 shell から叩く場合には効かない）。残余リスクとして記録する。

---

## 検査員への申し送り（未解決事項）

1. **CP-R-2 / CP-R-3 は設計文書 8 点の投入後に確定**させること（R-101 / F-042 / D-043 / L-014 / L-015 / E-001-E005 / TC-001-008 / IT-001）。
2. **CP-U-2 は実人による Walkthrough 実測**が必須。机上検査では 5 にできない。
3. gate6 の除外対象は **1 つのみ**: 本ルール定義ファイル `.claude/rules/01-security-redlines.md`。
   旧版では工程管理の計画文書 `docs/00_plan/**` も除外していたが、**その除外区画こそが本番 Oracle
   接続情報（接続ユーザ・パスワード・内部 IP）の漏洩箇所**であったため 2026-10 に撤廃した。
   除外を増やす変更は統制層の弱体化なので、追加する場合は本ファイルに理由を追記すること。
4. プロジェクト固有の機密識別子（接続ユーザ・バケット名・プロファイル・テナント）は
   Git に置かず `tools/trace_check/secret_patterns.local.json`（gitignore 済み）に置く運用。
5. **走査対象は 2026-10-12 に拡張済み**: 上記 3 の理由と同じく、除外区画に実値が残る事故を防ぐため
   `reports/**`・`archive/**`・`tutorial/**` を gate6 の走査に追加した
   （`hits=0`。件数は `reports/trace_R101.json` の `gates[gate6].stats.scanned_files` を参照 —
   走査対象自身を含むため固定値を文書に書かない）。**検査員はこれを「対象を狭めた」と誤読しないこと。**
6. **PPT に対する追加要素の登録簿**: `docs/90_knowledge/ppt-deviation-register.md`。
   本骨架は 2 PPT の忠実復刻を原則とするため、PPT に無い追加（`gen_view`・6 重門番・
   サブエージェント（検証系 A-5／工程実行系 A-12）・`tutorial/` 等）は同表が唯一の登録簿である。**独立検査では同表の
   網羅性（実際の追加要素が漏れなく載っているか）も確認対象とする。**
7. **CP の総数は 8 → 11（2026-10-12）→ 12（2026-10-13）へ増えた**。
   - 8 → 11: `CP-R-7`・`CP-U-3`・`CP-U-4` を追加。対応 TR は `docs/00_plan/tasks.md` **Task 19**。
   - 11 → 12: `CP-R-8`（ID 台帳の唯一書込み口と阻塞の実効性）を追加。対応 TR は **Task 20**（`TR-20.1`〜`TR-20.6`）。
   **CP を増やすときは `TR-17.1` と `TR-19.4` の期待値も同じ作業単位で更新すること**
   （片方だけ直すと本骨架が自己矛盾する。gate4 を変更する際に同時更新を要するのと同じ理由）。
   本ファイル冒頭の「CP 総数」表示も同じ作業単位で直す（2026-10-13 に 8 のまま残っていたのを修正）。
8. **「JET 全 32 モジュール」は出所の誤読であった**（正: JET PPT slide 8 の**全 34 本の API**、うち AI 適用 22 本）。
   経緯と走査結果は `docs/90_knowledge/ppt-deviation-register.md` §2 の訂正注記が唯一の定義。
   **検査員は、本骨架の文書に数量が現れたら「その数が何を数えたものか」を出所の頁で確認すること。**

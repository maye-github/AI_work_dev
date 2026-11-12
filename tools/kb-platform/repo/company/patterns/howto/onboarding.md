---
doc_id: PAT-ONBOARDING-001
scope: company
title: "新人 2 時間 Walkthrough（trans-cosmos-ai AI 全流程開発骨架）"
doc_type: pattern
version: "1.0"
status: active
conf_level: 20
owner: Nan
updated_at: '2026-11-06'
tags: [onboarding, checklist]
source_project: framework-rules
---

# 新人 2 時間 Walkthrough（trans-cosmos-ai AI 全流程開発骨架）

本チェックリストは NFR-4「新人 2 時間可上-hand」の実体として、新人が本骨架を一通り操作し、`R-ID 発番 → 基本設計 → 詳細設計 → Claude Code 造コード → trace_check → commit` の全流程を自力で走通すための手順を示す。出典：PPT 第 S6 页（チーム役割の再構築）、PPT 第 S30 页（Phase 1 パイロット）。

- 全 10 ステップ。各ステップは「作業内容」「実行コマンド」「予定時間（分）」「合格サイン（Exit code／期待 stdout）」を必須とする。
- 予定時間合計 = **100 分**（rubric 目標は <= 90 分。熟練すれば 60 分、第 1 回は 100 分前後を見込む）。
- すべてのコマンドは `py -3` を用いる（bare `python` は Windows の Store スタブのため使用禁止）。
- 実行環境に実データ・実接続情報は不要。機密の実値は一切記載せず、プレースホルダのみを用いる。

---

### 1. Git clone して `.claude/` の存在を確認する
- **作業内容**：リポジトリを clone し、AI 骨架の中核 `.claude/`（rules・skills・agents）と `docs/`・`tools/` が揃っていることを確認する。
- **実行コマンド**：
  ```
  git clone <repo-url> trans-cosmos-ai-skeleton && cd trans-cosmos-ai-skeleton
  ls .claude && ls .claude/rules && ls tools
  ```
- **予定時間（分）**：5
- **合格サイン**：`ls .claude` → Exit 0、`.claude/rules`・`.claude/skills`・`.claude/agents` が表示される（stderr 空）。

### 2. `docs/00_registry/ids.yml` に R-102 を手動申請・登記する
- **作業内容**：`ids.yml` の `ids:` に新規要求 R-102 を追記する（`status: draft`、`name`・`description`・`used_by` を記載）。発号は 3 桁起步・連番・再利用禁止の規則に従う。
- **実行コマンド**：
  ```
  py -3 -c "import yaml;d=yaml.safe_load(open('docs/00_registry/ids.yml',encoding='utf-8'));print('R-102' in d['ids'])"
  ```
- **予定時間（分）**：10
- **合格サイン**：`True` を stdout に出力し Exit 0（R-102 が `ids` に存在）。

### 3. `docs/10_requirements/req-template.yaml` を複製して R-102 の要求ファイルを作る
- **作業内容**：`req-template.yaml` を `docs/10_requirements/R-102-<Module>.yaml` にコピーし、front-matter 7 字段（id/type/req_ids/status/sensitivity/owner/version）を R-102 用に埋める。単一ソース原則により要求の定義は本ファイル 1 箇所のみに留める。
- **実行コマンド**：
  ```
  cp docs/10_requirements/req-template.yaml docs/10_requirements/R-102-<Module>.yaml
  py -3 -c "import yaml;t=open('docs/10_requirements/R-102-<Module>.yaml',encoding='utf-8').read();fm=yaml.safe_load(t[3:t.find(chr(10)+'---',3)]);print(sorted(fm))"
  ```
- **予定時間（分）**：10
- **合格サイン**：front-matter に 7 キー全部が存在し、`status` が `{draft,open,baselined,changed,done,void}` のいずれか。

### 4. F-042 を F-043 に複製し、I-ID 参照を 3 箇所変更する
- **作業内容**：`docs/_samples/20_basic_design/F-042-R60Area.yaml` を F-043 として複製し、`input_ids` の I-ID 参照を 3 箇所だけ変更する（要求 ID の追随）。ID 定義の重複書きは禁止（他工程は R-ID/I-ID 引用に留める）。
- **実行コマンド**：
  ```
  cp docs/_samples/20_basic_design/F-042-R60Area.yaml docs/20_basic_design/F-043-<Module>.yaml
  py -3 -c "t=open('docs/20_basic_design/F-043-<Module>.yaml',encoding='utf-8').read();print(t.count('I-'))"
  ```
- **予定時間（分）**：10
- **合格サイン**：I-ID 参照が差分 3 箇所で更新され、ファイルが YAML として解析可能（異常なし）。

### 5. ロジック L-016 を 1 件、エラー E-009 を 1 件登記する
- **作業内容**：`ids.yml` に業務ロジック L-016 とエラー E-009 を追記し、L-016 を D-043 に、E-009 を L-016 に紐付ける（追溯の起点を作る）。
- **実行コマンド**：
  ```
  py -3 -c "import yaml;d=yaml.safe_load(open('docs/00_registry/ids.yml',encoding='utf-8'));print('L-016' in d['ids'], 'E-009' in d['ids'])"
  ```
- **予定時間（分）**：10
- **合格サイン**：`True True` を stdout に出力し Exit 0。

### 6. `tc-template.yaml` を使って新規テストケース TC-009 を設計する
- **作業内容**：`docs/50_unit_test/tc-template.yaml` を基に TC-009 を 1 件設計する。`design_ids`（D-043/L-016）・`req_ids`（R-102）・`preconditions`・`input_spec`・`expected_output` を明記し、期待値の出典（設計 ID）を紐付ける。
- **実行コマンド**：
  ```
  py -3 -c "import yaml;d=yaml.safe_load(open('docs/50_unit_test/TC-009-<Module>.yaml',encoding='utf-8'));print(d['case_id'], d.get('design_ids'))"
  ```
- **予定時間（分）**：15
- **合格サイン**：`TC-009 [...]` が表示され、`design_ids` が空でない。

### 7. `py -3 -m tools.trace_check --strict` を実行し、注入された野号を見つけて修正する
- **作業内容**：トレーニング用に意図的に注入された野号（未登記 ID）を `--strict` 実行で検出し、正しい ID へ修正して門番を通す。
- **実行コマンド**：
  ```
  py -3 -m tools.trace_check --strict
  ```
- **予定時間（分）**：20
- **合格サイン**：初回は Exit 非 0 かつ stderr に「野号」の語が出現。修正後は Exit 0 で `[trace_check] ... orphans=0` を stdout に出力。

### 8. `.claude/rules/05-commit-messages.md` に従って commit し、タグ `baseline/R-102/basic-v0.1` を付ける
- **作業内容**：7 種 commit 形式（req/design/feat/test/fix/rel/chore）に従い「Trace: R-102/...」を含むメッセージで commit し、ベースラインタグを付与する。
- **実行コマンド**：
  ```
  git add docs/ && git commit -m "req: R-102 要求登録" -m "Trace: R-102"
  git tag baseline/R-102/basic-v0.1
  git tag --list "baseline/R-102/*"
  ```
- **予定時間（分）**：10
- **合格サイン**：`git tag --list` に `baseline/R-102/basic-v0.1` が出力され Exit 0。

### 9. `py -3 -m tools.masking.mask_demo --self-test` と secrets スキャンを実行する
- **作業内容**：双方向脱敏スクリプトの self-test と、機密ゼロヒット・スキャン（門番 gate6 相当）を実行し、機密情報が一切漏れていないことを確認する。
- **実行コマンド**：
  ```
  py -3 -m tools.masking.mask_demo --self-test
  py -3 -m tools.trace_check --strict --only-check secrets
  ```
- **予定時間（分）**：5
- **合格サイン**：1 つ目は Exit 0 かつ stdout にプレースホルダ（`TBL_`/`COL_`/`PWD_` のいずれか）と `unmask_ok=true`。2 つ目は Exit 0（機密ヒット 0 件）。

### 10. `py -3 -m tools.gen_formal.gen_excel --dry-run --module R-101` を実行し field_count=56 を確認する
- **作業内容**：機読源→日文正式版 Excel の dry-run を実行し、列数が I-ID 数（56）と一致することを確認する。実 Excel は生成しない（Phase 1 は dry-run のみ）。
- **実行コマンド**：
  ```
  py -3 -m tools.gen_formal.gen_excel --dry-run --module R-101
  ```
- **予定時間（分）**：5
- **合格サイン**：Exit 0 かつ stdout に `[gen_formal] field_count=56` を出力（`.xlsx` は生成されない）。

---

## AI Utilization 記録

本 Walkthrough における AI 活用状況を記録する（PPT 第 S6 页「AI は実行主体、人は責任主体」の実践記録）。

| 項目 | 記録内容 |
|---|---|
| 使用ツール | Claude Code（8 工程すべて）＋人のレビュー・承認ゲート・`py -3` ローカル門番 |
| AI に任せた作業 | テンプレート複製・ID 参照変更・TC ドラフト生成・trace_check 修正候補提示 |
| 人が確認した作業 | R-102 発号の妥当性・I-ID 参照変更 3 箇所の妥当性・commit 内容の責任確認 |
| 生成物の採用率 | `<採用件数> / <生成件数>`（実測後に記入） |
| レビューでの修正率 | `<修正件数> / <採用件数>`（実測後に記入） |
| trace_check 通過 | Exit 0（野号 0・機密ヒット 0） |
| 実測所要時間 | `<実測合計> 分`（予定 100 分・目標 <= 90 分） |

## 新人自評価アンケート（5 問）

各問を 1（できなかった）〜5（自力でできた）で自己評価し、講評欄に記入する。

1. `.claude/rules/` の 6 份規則と `CLAUDE.md`・`AGENTS.md` の役割分担を説明できるか。
2. `ids.yml` の唯一発号口ルール（野号禁止・再利用禁止）を理解し、R-102 を正しく発号できたか。
3. R-ID → F-ID → I-ID → L-ID → TC-ID の追溯の流れを、自分の成果物でたどれるか。
4. `py -3 -m tools.trace_check --strict` の失敗を自力で切り分けて修正できたか。
5. 機密脱敏（3 級清单・masking・secrets スキャン）の必要性を、自分の言葉で説明できるか。

> 合格基準（rubric）：合計所要時間 <= 90 分かつ 10 ステップ中 7/10 以上通過で rubric 4。60 分かつ 10/10 通過かつ TC-009 が trace_check を通れば rubric 5。

## 関連ドキュメント
- `docs/00_registry/ids.yml`（唯一発号口）
- `.claude/rules/05-commit-messages.md`（commit 形式・タグ規約）
- `tools/kb-platform/repo/company/standards/platform-map.md`（7 層マップ・知識層の位置づけ）
- `ROADMAP_3PHASE.md`（Phase 1 条 14 の実体）

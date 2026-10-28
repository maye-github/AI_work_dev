---
id: RULE-005
type: commit-messages
req_ids: [SPEC-FR-6, SPEC-C-TECH-5]
status: draft
sensitivity: internal
owner: AI-SE
version: 0.1.0
---

# コミットメッセージ規則（7 種別 / Trace-AI-Review 三段 / Tag 命名）

## 1. 適用範囲
**Summary**: 全 commit は**7 種別固定**（req/design/feat/test/fix/rel/chore）のいずれかで始め、本文に **Trace / AI / Review の三段**を必記する。種別の増減・独自種別の追加は禁止（spec.md Constraints Technical 5 / FR-6）。
- 参照: 落地篇 PPT S16（追溯）/ spec.md FR-6・NFR-3

---

## 2. 7 種 commit 種別（凡例 + 完全示例）
**Summary**: 各種別は「どの工程の成果物を確定するか」に対応する。示例はすべて種別行で始まり、下記 grep に一致する。
```bash
grep -E "^- (req|design|feat|test|fix|rel|chore):"
```

### 2.1 `req` — 要求・確認票の起案/是認（工程 01）
```
- req: R-101 R60Areaマスタ検索登録修正削除の要求を受理
  Trace: R-101
  AI: code-from-design-trans-cosmos-ai@v0.1
  Review: SE-001
```

### 2.2 `design` — 基本設計/詳細設計の基準化（工程 02/03/04）
```
- design: F-042 R60Area全画面機能のBDとI-201..256を基準化
  Trace: R-101/F-042/I-201
  AI: code-from-design-trans-cosmos-ai@v0.1
  Review: SE-002
```

### 2.3 `feat` — 製造（設計→コード生成）（工程 05）
```
- feat: D-043 R60AreaController search/editを既存仕様に合わせ実装
  Trace: R-101/F-042/L-014
  AI: code-from-design-trans-cosmos-ai@v0.1
  Review: PG-003
```

### 2.4 `test` — 単体/結合テストの追加（工程 06/07）
```
- test: TC-001..008 R60Areaの正常3境界2異常3テストを追加
  Trace: R-101/D-043/L-015
  AI: code-from-design-trans-cosmos-ai@v0.1
  Review: TESTER-001
```

### 2.5 `fix` — 不具合修正（BUG-xxx 連携）
```
- fix: BUG-002 R60Area検索0件時に前回結果が残る不具合を修正
  Trace: R-101/F-042/L-014
  AI: code-from-design-trans-cosmos-ai@v0.1
  Review: PG-003
```

### 2.6 `rel` — リリース準備・Tag 打ち（工程 08）
```
- rel: basic-v1.0 R60Area Phase1 ベースラインをリリース
  Trace: R-101/F-042/L-015
  AI: code-from-design-trans-cosmos-ai@v0.1
  Review: SE-001
```

### 2.7 `chore` — 雑務・設定・ツール（非機能コミット）
```
- chore: trace_check.py gate5 のsnake/camel判定を追加
  Trace: R-101/D-043/L-014
  AI: code-from-design-trans-cosmos-ai@v0.1
  Review: AI-RTC-001
```

---

## 3. 三段式 必記（Trace / AI / Review）
**Summary**: 全 commit 本文の末尾に、下記 3 行を**この順・この形式**で必ず付与する。欠落は commit 拒否（`code-from-design-trans-cosmos-ai` による製造実行時の検証項目）。
| # | 行 | 形式 | 説明 |
|---|----|------|------|
| 1 | Trace | `Trace: R-xxx/F-xxx/L-xxx` | 追溯 ID。R/F/L を `/` 区切りで列挙 |
| 2 | AI | `AI: <skill>@<ver>` | 生成に用いたスキルと版（例: `code-from-design-trans-cosmos-ai@v0.1`） |
| 3 | Review | `Review: <reviewer>` | レビュアー識別子（SE-xxx / PG-xxx / TESTER-xxx 等） |

- **Trace**: どの要求・機能・ロジックに紐づくかを示す。複数ある場合は `/` で連結する。
- **AI**: 人手のみのコミットであっても `AI: manual@v0` のように必ず行を置く（行の省略は不可）。
- **Review**: 人は A/I、Claude Code は R/C。Claude Code 単独 commit でも Review 行を省略しない（AI 推進担当の識別子を記す）。

---

## 4. Git Tag 命名約定
**Summary**: ベースラインおよびリリースの Tag は下記 2 系統に固定する。
| Tag | 用途 | 命名 | 例 |
|-----|------|------|-----|
| 要求単位ベースライン | R-ID 単位の基準化 | `baseline/R-xxx` | `baseline/R-101` |
| 初期リリース | Phase1 基本版のリリース | `basic-v<major>.<minor>` | `basic-v1.0` |

- `baseline/R-xxx` は該当要求の `status` が `baselined` になった時点で打つ。
- `basic-vX.Y` は工程 08（リリース運用保守）でリリース承認後に打つ。
- Tag 名・Tag メッセージにも §3 の Trace を 1 行含める（`Trace: R-101/BASELINE` 等）。
- ベースライン後の変更は `CR-xxx` を経由し、Tag の上書き・再利用は禁止（番号再利用禁止に準拠）。

---

## 5. Co-Authored-By 行（commit 末尾への追記規則）
**Summary**: commit message の**末尾**には Co-Authored-By トレーラーを必ず追加する。ツールの帰属を明示するための規則であり、**具体的な名前・メールアドレスは本規則に書き込まない**（各自の環境・Git 設定に委ねる）。
- 形式: `Co-Authored-By: <name> <email>`
- 位置: 本文（三段）の後、空行を 1 行挟んで最末尾。
- `<name>` / `<email>` は commit 作成者の環境で設定するプレースホルダであり、本ファイルには実値を記載しない。
- 例（プレースホルダ表示）:
```
Co-Authored-By: <tool-name> <noreply@example.com>
```

---

## 6. コミット前チェックリスト
- [ ] 種別が req/design/feat/test/fix/rel/chore のいずれかである
- [ ] `Trace: R-xxx/F-xxx/L-xxx` 行がある
- [ ] `AI: <skill>@<ver>` 行がある
- [ ] `Review: <reviewer>` 行がある
- [ ] 末尾に `Co-Authored-By:` トレーラーがある（実值は環境側で設定）
- [ ] `py -3 -m tools.trace_check --strict` が `Exit 0`（Push 前にも再実行）

---

## 7. ブランチ・レビューの運用（旧 `CONTRIBUTING.md` の取込・2026-10-28）

- **作業ブランチ**: `feat/<R-ID>-<短い説明>`。`main` へは**人の承認後**にマージする（紅线③）。
- **Tag** は §4 の 2 系統のみ（`baseline/R-xxx`・`basic-vX.Y`）。上書き・再利用は禁止。
- **レビューは差分で行う**（`git diff`）。「全部書き直した」は差分レビューを無効化するので避ける。
- **空コミットで門番を迂回しない**（紅线⑥）。`--skip` も同じ。
- 旧文書の全文は git 履歴にある: `git show keep/before-cleanup-2026-10-28:CONTRIBUTING.md`。

---
doc_id: PAT-CC-MIGRATION-001
scope: company
title: "Trae → Claude Code 移行ガイド"
doc_type: pattern
version: "1.0"
status: active
conf_level: 20
owner: Nan
updated_at: '2026-11-06'
tags: [migration, claude-code, tooling]
source_project: framework-rules
---

# Trae → Claude Code 移行ガイド

> **対象読者**: これまで Trae Code で trans-cosmos-ai 骨架を回していた SE / PG / テスター。
> Claude Code の設定機構に不慣れな人を前提に、**何がどこへ移り、日々どう使うか**だけを書く。
> 移行日: 2026-10-09。移行理由: Claude Code 単一ライセンスでの運用に統一するため。

---

## 1. 何が変わったか（30 秒で）

**移行前**は 2 ツール分担だった：「Trae Code が 7 工程（要件〜リリース）を担当し、Claude Code が製造 1 工程だけを担当。両者は Git + `CLAUDE.md` で受け渡す」。

**移行後**は 1 ツール：「**Claude Code が 8 工程すべてを実行し、人はレビューゲートで拍板する**」。

この変更で消えた概念：
- ❌ 「双工具交接 / Bridge」— 受け渡す相手がいないので不要。
- ❌ 「`claude --project ... --read ... --rule ...`」— 実在しないフラグだった。Claude Code は自然言語で依頼する。
- ❌ Trae 独自の Skill 形式・Spec Mode。

この変更で残った概念（重要）：
- ✅ **ID 追跡**（R-101 → F-042 → I-201..256 → D-043 → L-014/015 → E-001..008 → TC-001..008）
- ✅ **6 重門番** `tools/trace_check`
- ✅ **成果物 6 原則**と二重化（機読源 YAML/MD → 日文正式版）
- ✅ **機密 3 級分類**と脱敏

---

## 2. 新旧対照表

| 旧（Trae） | 新（Claude Code） | 備考 |
|---|---|---|
| `.trae/rules/*.md`（6 份） | `.claude/rules/*.md`（6 份） | **ファイル名は同一**。起動時に自動ロード |
| `.trae/skills/code-from-design-trans-cosmos-ai/SKILL.md` | `.claude/skills/code-from-design-trans-cosmos-ai/SKILL.md` | frontmatter に `name` / `description` を追加 |
| `.trae/specs/ai-full-lifecycle-dev-steps/{spec,tasks,review}.md` | `docs/00_plan/{spec,tasks,review}.md` | Spec Mode は廃止。単なる工程管理文書として保管 |
| `AGENTS.md`（Trae Skill 前提の役割表） | `AGENTS.md`（人向け役割表）＋ `.claude/agents/*.md`（3 体） | Claude Code は `CLAUDE.md` があると `AGENTS.md` を自動ロードしない |
| （なし） | `.claude/settings.json` | 権限設定。**deny のみ**（後述） |
| `.trae/`（作業ディレクトリ） | （削除済み） | 移行時は `archive/trae/` に保管していたが、2026-10-26 に削除した（内容は `.claude/` に統合済み） |

> **注意**: `.trae/` はもう存在しない。旧パスを参照するメモやスクリプトがあれば `.claude/` に読み替えること。

---

## 3. Claude Code の設定機構（最低限これだけ）

Claude Code は 4 つの場所を見る。役割が違うので混ぜないこと。

### 3.1 `CLAUDE.md` — 常時ロードされる中核
プロジェクト直下の `CLAUDE.md` は**毎回の起動で必ず読まれる**。だから**短く保つ**（目安 200 行未満）。
ここには「これを破ったら即アウト」だけを書く。実際、現在は §1 の 7 条紅线・§2 の禁止事項 5 条（案件固有）・commit 様式だけが入っている。

### 3.2 `.claude/rules/*.md` — 工程別の詳細規約
`CLAUDE.md` を膨らませないための逃がし先。**起動時に自動ロードされる**。
frontmatter は通常の Markdown として無視されるが、`paths:` を書くと「その glob にマッチするファイルを触ったときだけロード」になる（現在は未使用＝常時ロード）。

| ファイル | 内容 |
|---|---|
| `00-project-global.md` | プロジェクト全体のハード制約 10 条 |
| `01-security-redlines.md` | 機密 3 級分類・禁止外投 13 条・脱敏占位ルール |
| `02-requirements.md` | 8 工程 SOP・R-ID 発号手順・status 状態機 |
| `03-design-coding.md` | `BaseCamelModel` 定型・`R60Common.ts` 対応表・snake/camel 分区・SQL 白名単 |
| `04-testing.md` | TC 正常3/境界2/異常3・`design_ids` 必須・網羅率 |
| `05-commit-messages.md` | commit 7 種・Tag 命名・Review 三段 |

### 3.3 `.claude/skills/` — 手順書（Claude が自動で思い出す）
`code-from-design-trans-cosmos-ai` は「設計 → 製造」の手順を書いた Skill。`description` を見て Claude が**自分で使うべきと判断したとき**に読み込む。呼び出しは不要だが、明示したいときは「`code-from-design-trans-cosmos-ai` スキルを使って」と言えばよい。

### 3.4 `.claude/agents/` — 別コンテキストの検査役
役割を**別のコンテキスト**で走らせたいときの定義。使い分けが肝：

| Agent | 使いどころ |
|---|---|
| `spec-reviewer` | 成果物が受け入れ基準を満たすか**独立に**検める。`docs/00_plan/review.md` のチェックリストを実行する |
| `secret-auditor` | 機密漏れの点検。`trace_check --only-check secrets` と `mask_demo --self-test` を走らせる |
| `trans-cosmos-ai-node6-unit-test` | 詳細設計から TC を設計する（観点技法と比率の強制。**工程 06 の実行体がそのまま担う**） |

**なぜ別 Agent か**: 自分で作った成果物を自分で「合格」と言えてしまう問題を潰すため。作った本人と同じコンテキストでは検査にならない。

### 3.5 `.claude/settings.json` — 権限
`settings.json`（共有・コミット対象）と `settings.local.json`（個人用・gitignore 済）がある。
現在の `settings.json` は **`deny` だけ**を置いてある。つまり「Claude に読ませてはいけないファイル」を塞いであるだけで、**承認を自動化する設定は入れていない**（それはあなたが決めることなので）。

---

## 4. 移行後のディレクトリ

```
AI_work_dev/
├── CLAUDE.md                  ← 常時ロード。中核制約だけ
├── .claude/
│   ├── settings.json          ← 権限（deny のみ）
│   ├── rules/                 ← 自動ロードされる 6 份規則
│   ├── skills/code-from-design-trans-cosmos-ai/SKILL.md
│   │           trans-cosmos-ai-lifecycle-coach/（8 工程の伴走進行役 ＋ nodes/ ＋ references/）
│   └── agents/                ← 検証系（spec-reviewer 等）＋ 工程実行系（trans-cosmos-ai-node1..8）
├── docs/
│   ├── 00_plan/               ← spec / tasks / review（旧 .trae/specs）
│   ├── 00_registry/ 01_context/ 10_requirements/ … 90_knowledge/
├── tools/                     ← trace_check / gen_formal / masking
└── reports/
```

---

## 5. 日常の使い方（8 工程 × Claude Code ＋ 人のゲート）

> **詳しい手順は別冊**：工程ごとの「人が入力するもの / Claude Code への依頼文 / 成果物 / 人がレビューする観点 / 合格サイン」は
> **`tools/kb-platform/repo/company/patterns/dev/ai-playbook.md`** にまとめてある。実際に動かした実例は
> **`tools/kb-platform/repo/company/patterns/dev/ppt-walkthrough.md`**（PPT の D1–D7 走査）。以下は要約。
>
> **はじめての人はこちらから**：**`tutorial/R60Login/README.md`**（中国語の手順書）。
> 実際のモジュール R60Login を題材に、模擬お客様要求書 → 構造化 → 組内レビュー → 改修 → 承認、という
> 1 ノード分の流れを **そのまま真似できる形**で置いてある。ノード 2〜8 の入力テンプレートも同梱。


人は「全部を読む」のではなく、**4 つのゲートで拍板する**。

| # | 工程 | Claude Code に頼むこと | 人のゲート |
|---|------|----------------------|-----------|
| 1 | 要件理解 | 「仕様書を読んで要件構造化シートと確認事項一覧を作って。ID は `ids.yml` で発号して」 | **要件合意** |
| 2 | 基本設計 | 「R-101 から機能・画面・入出力一覧を起こして `docs/20_basic_design/` に」 | **設計評審** |
| 3 | 詳細設計 | 「D-043 / L-014 / L-015 の処理フロー・項目定義・SQL・エラー一覧を作って」 | 設計評審（同ゲート） |
| 4 | 框架構築 | 「`docs/40_framework/framework-record.yaml` の選型記録を埋めて」 | — |
| 5 | 製造 | 「L-014/L-015 に従って `R60AreaController` を実装して」（§5 テンプレ参照） | コードレビュー |
| 6 | 単体テスト | 「TC-001..008 を `tc-template` で設計して」／`trans-cosmos-ai-node6-unit-test` | **合否判定** |
| 7 | 結合テスト | 「8 接口の API シーケンスで IT-001 を作って」 | **合否判定** |
| 8 | リリース運用 | 「リリースノートと切戻し手順を作って」 | **リリース判定** |

**頼み方のコツ**: 「Trae に渡していた指示」はもう不要。`docs/` の設計文書を読ませて、**何を作るか・何を守るかだけ**を自然言語で伝えればよい。CLAUDE.md §5 に実装依頼のテンプレートがある。

---

## 6. 検証と門番（1 コマンド）

移行の前後でここは変わっていない。**commit 前に必ず走らせる**。

```bash
py -3 -m tools.trace_check --strict --gate 6
# 期待: gate1=PASS gate2=PASS gate3=PASS gate4=PASS gate5=PASS gate6=PASS
#       total_ids=79 orphans=0 field_count=56
```

| gate | 何を見ているか |
|---|---|
| gate1 | 野号（`ids.yml` 未登録 ID） |
| gate2 | 追跡の双方向閉ループ（R→…→TC と逆方向） |
| gate3 | 成果物の front-matter 7 字段 |
| gate4 | `gen_formal` の列数 == I-ID 数 |
| gate5 | snake/camel の命名分区 |
| gate6 | 機密ゼロヒット |

**除外は 1 箇所だけ**：`.claude/rules/01-security-redlines.md`（L3 定義そのもの）。旧版は `docs/00_plan/**`（工程管理の計画文書）も除外していたが、**その除外区画こそが本番接続情報の漏洩箇所だった**ため 2026-10 に撤廃し、走査対象に戻した（§10 参照）。除外を増やすのは統制層の弱体化なので、増やすなら `docs/00_plan/review.md` に理由を書くこと。

---

## 7. 任意：権限の緩和（あなたが決める設定）

毎回 `py -3 -m tools.trace_check ...` の承認を求められるのが煩わしければ、**あなた自身の判断で** `.claude/settings.local.json`（gitignore 済・個人用）に allow を追加する。`settings.json` には入れないこと（チーム全員に波及する）。

```json
{
  "permissions": {
    "allow": [
      "Bash(py -3 -m tools.trace_check:*)",
      "Bash(py -3 -m tools.gen_formal.gen_excel:*)",
      "Bash(py -3 -m tools.masking.mask_demo:*)"
    ]
  }
}
```

これは**門番コマンドの承認を省くだけ**で、門番自体は実行される。`--strict` を外す・gate を減らすといった改変は紅线⑥違反になるので避けること。

---

## 8. 移行の記録とロールバック

- 旧 Trae 資産は移行時に `archive/trae/` へ保管していたが、**2026-10-26 に削除した**。内容は
  `.claude/rules/` と `.claude/skills/` に統合済みであり、参照先はすべて `.claude/` 側にある。
- **ロールバック（`.trae/` へ戻す）はもうできない。** このリポジトリは git 未コミットであり、
  削除前のスナップショットは残っていない。Trae 期の状態が必要になった場合は、本節 §1〜§3 の対応表から
  `.claude/` 側の内容を読むこと。
- 移行時に**内容は意図的に変えていない**：規則 6 份の中身・`safe` な ID 体系・ツール 3 本は無改変。変わったのは参照パスと「Trae が担当する」という記述だけ。

---

## 9. よくある質問

**Q. `AGENTS.md` を直したのに Claude が読んでくれない。**
A. 仕様どおりです。Claude Code は `CLAUDE.md` が存在する場合 `AGENTS.md` を自動ロードしません。`AGENTS.md` は**人向けの役割定義書**として残してあります。Claude に守らせたいことは `CLAUDE.md` か `.claude/rules/` に書いてください。

**Q. 規則を 1 本足したい。**
A. `.claude/rules/` に Markdown を置くだけで次回起動から読まれます。front-matter の 7 字段（`id/type/req_ids/status/sensitivity/owner/version`）を付けてください（`trace_check` gate3 が検査します）。

**Q. スキルを呼ぶコマンドは？**
A. 不要です。`description` に合致する作業だと Claude が判断して自動で読みます。明示したいときは「`code-from-design-trans-cosmos-ai` スキルを使って」と自然言語で言ってください。

**Q. `docs/00_plan/` の 3 ファイルは消していい？**
A. 残してください。spec（要件）/ tasks（実装計画）/ review（独立検査のチェックリスト）は、この骨架が**何を約束して何を実装したか**の唯一の記録です。特に `review.md` はまだ未完了の検査項目（CP-R-2 / CP-R-3 / CP-U-2）を含みます。

**Q. Trae に戻したくなったら？**
A. §8 のとおり手作業での差し戻しになります。戻す予定があるなら、いま差分をどこかに控えておくことを勧めます。

---

## 10. 移行後にまだ残っている宿題

移行そのものとは別に、**以前から未完了の項目**が残っている。詳細は `reports/DELIVERY_MEMO.md`。

1. `docs/00_plan/review.md` の CP-R-2 / CP-R-3 / CP-U-2 が **Pending** — `spec-reviewer` Agent で実行して確定させる。
2. AC-8（新人 Walkthrough）が**机上判定のみ** — 実測の所要時間が必要。
3. gate6 は内蔵正規表現 — 実 `gitleaks` CLI への置換は Phase 2。
4. ~~**`docs/00_plan/` は gate6 の走査対象外**~~ → **2026-10 に解消済み**。
   旧版では計画文書を走査対象外としていたため、移行前から存在する実値
   （spec.md の NFR-2 記述、tasks.md の Task 9 スキャナ pattern 例など）がそのまま残っていた。
   実際に **本番 Oracle 接続情報（接続ユーザ・パスワード・内部 IP・テナント・バケット・プロファイル）が
   `docs/00_plan/spec.md` と `docs/00_plan/tasks.md` に平文で残存**していたことが判明した。
   対応：①当該実値をすべて脱敏占位（`TBL_1` / `PWD_1` / `IP_1` / `DOM_1` / `BUCKET_1` / `PROFILE_1`）へ置換、
   ②`SECRET_EXEMPT_PATHS` から `docs/00_plan` を削除して走査対象に戻し、
   ③gate6 に「資格情報付き接続 URL」の汎用検出（占位は除外）を追加した。
   以降 `docs/00_plan/**` も `py -3 -m tools.trace_check --strict --only-check secrets` の対象である。

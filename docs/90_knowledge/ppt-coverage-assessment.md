---
id: KNOW-PPT-COVERAGE
type: knowledge
req_ids: []
status: draft
sensitivity: internal
owner: AI-SE
version: 0.1.0
---

# 要件源 PPT への適合状況評価（「AI 全链路開発 agent は今あるのか」）

> **★状態（2026-10-28 追記・必読）**: これは**評価時点（2026-10 上旬）のスナップショット**である。
> 当時は「R60Login 0/8 承認」であったが、**現在は 8/8 承認済み**
> （`docs/00_plan/coach/R60Login/n01〜n08.yml` の `state: approved`）。
> **本文の数値を「今の状態」として引用しないこと。** 現在地は `SessionStart` のブリーフか
> `py -3 -m tools.coach_brief` で取る。本文件は「当時どこが足りなかったか」の記録として残す。

> **この 1 枚の目的**：要件源 2 份 PPT（`D:\AI_knowledge\方案与落地`）が要求する
> **AI 全链路開発 agent 一式**が、いま `D:\AI_work_dev` に**どこまで在るか**を、
> **推測ではなく実測で**一覧にする。そして**足りない分をどの順で埋めるか**を決める。
>
> **読むタイミング**：「うちに AI 全链路の agent はあるのか」と聞かれたとき、
> または別案件へ横展開する前に「何が土台で、何が未実装か」を確認したいとき。
>
> **関連**：[platform-map.md](platform-map.md)（7 層の対応）／
> [v1-platform-4layer.md](v1-platform-4layer.md)（v1 四層の対応）／
> [ppt-deviation-register.md](ppt-deviation-register.md)（PPT に無い追加要素の登記簿）／
> `ROADMAP_3PHASE.md`（3 段階計画）

---

## 0. 結論（1 段）

**骨架は、2 份 PPT を「動く Claude Code 実装」に翻訳し終えている。**
ただし **3 点だけ欠けている** — ①プラットフォーム層（模型網関・RAG・KPI 実測・監査ログ・
コスト管理・評測集）②**検証**：この agent 一式は**まだ一度も端から端まで走っていない**
③内容：56 画面カードは 1 枚だけ。

**そして ①は我方の漏れではない。** PPT 自身が v1 S11 で
「**不要求立刻自建完整平台**…小步验证，先跑通一个小项目的全链路」と述べ、
v1 S12 で優先順を「**先做接入层模板库 + 知识库 RAG（投入小、见效快），再逐步建设编排层和模型网关层**」と
明示し、落地篇 S30 でプラットフォーム化を **Phase 3（6〜12 ヶ月）** に置いている。
骨架の `ROADMAP_3PHASE.md` はこの順序と一致している。

> **したがって「まだ足りない」は失敗ではない。順番どおりである。**
> 本当に手を打つべきなのは **②検証（1 回も走っていない）** である。

---

## 1. 何をどう核したか（再現可能）

| 側 | 対象 | 手段 |
|---|---|---|
| 要件 | `AI実践に基づくソフトウェア開発プロセスの再考_落地篇.pptx`（30 頁）・`基于统一 AI 平台的全生命周期软件工程方案_v1.pptx`（13 頁） | zip+XML から `<a:t>` を抽出し**全文**（standards ライブラリのみ、追加 package なし） |
| 実装 | `.claude/agents`（14）・`.claude/skills`（5）・`.claude/rules`（7）・`tools/**`・`docs/00_registry/ids.yml`・`docs/00_plan/**`・`.github/**`・`.claude/settings.json` | 3 体の Explore による棚卸し ＋ `--help` 実行 ＋ grep 実測 |

> **核した範囲の限界（正直に）**：PPT の**図中テキスト以外の図形**・**スピーカーノート**は
> 抽出していない。「PPT に無い」と書いた項目は「本文テキストに無い」の意味である。

---

## 2. 主対照表

### 2.1 落地篇（PART01〜PART04）

| PPT の要求（頁） | 現状 | 根拠 |
|---|---|---|
| **8 工程の全链路像**（S4） | ✅ **具备** | `.claude/agents/trans-cosmos-ai-node1〜8`（＋ n09 旁路環） |
| **役割の再構築** SE/PG/テスター（S6）＋ **RACI**（S17） | ✅ **具备** | `.claude/rules/02-requirements.md` §2 8 工程表・§8 RACI |
| **端到端走査**：1 件の改修要望を追う（S7） | 🔶 **具备，但未走破** | 手順は `.claude/skills/trans-cosmos-ai-lifecycle-coach/nodes/n0*.md` にある。走破記録は `agent-run-record.md` |
| **AI 作業①②③④⑤／人の観点／成果物／下流連携**（S9〜S15） | ✅ **具备** | 各 `nodes/nNN-*.md` §3 手順＋§5 審査清単＋§9 実案件差分 |
| **得られうる形** 7 層（S26） | 🔶 **6 層に写像、1 層欠** | [platform-map.md](platform-map.md) |
| **主要コンポーネント 6 要素**（S27） | 🔶 **4 有 / 2 欠** | 工程別 Agent ✅・コンテキストハブ ✅・セキュリティ部分 🔶／**模型網関 ❌・RAG ❌・評価ガバナンス ❌** |
| **成果物 6 原則**（S20） | ✅ **具备** | `.claude/rules/03-design-coding.md`・`04-testing.md`・[dual-deliverable.md](dual-deliverable.md) |
| **成果物の二重化** 機読源 ⇄ 日文正式版（S21〜S24） | 🔶 **半具备** | `tools/gen_view`（中文ビュー `.zh.html`）は稼働。`tools/gen_formal.book` が**参考書体裁の `.xlsx` を `reports/` 配下へ生成**できる（2026-10-21 追加。`docs/**` には作らない＝CP-R-3 は不変）。顧客テンプレート接続と受控回流は Phase2 |
| **工程間の連携 7 メカニズム**（S16） | ✅ **具备**（7 中 6 が稼働） | コンテキストハブ＝`ids.yml`＋gate2／トレーサビリティ＝`trace_check`／変更影響＝`tools/impact.py`／成果物リポジトリ＝Git／ナレッジ＝`docs/90_knowledge/**`／**品質メトリクス＝定義のみで未計測** |
| **技術選型**（S28） | ✅ 相当 | Claude Code 単一ツール（規則 00 §13）。CI は占位 |
| **KPI 6 分類**（S29） | 🔶 **定義のみ・実測なし** | [ai-dev-playbook.md](ai-dev-playbook.md) §8 に 6 分類。計測実装は `tools/` に**無い** |
| **ロードマップ 3 段階**（S30） | ✅ **具备** | `ROADMAP_3PHASE.md`（Phase1 16 条／Phase2 12 条／Phase3 8 条） |

### 2.2 v1（统一 AI 平台の四層）

唯一真源は [v1-platform-4layer.md](v1-platform-4layer.md) §4。判定もそこに既に書かれている。

| v1 の層 | 現状 | 逐語（`v1-platform-4layer.md`） |
|---|---|---|
| **接入層**（Prompt 模板庫・権限・監査） | ✅ 実装済 | L130「✅ テンプレート群として存在」（`docs/*/**/*-template.yaml` 8 份） |
| **能力編排層**（Agent 工作流・人工検証節点） | 🔶 部分実装（**粒度差**） | L131「🔶 **工程別 Agent の粒度が PPT と異なる**」 |
| **知識庫層**（RAG） | ✅ 実装済 | L132「✅ `docs/90_knowledge/**`」— **ただしファイル型 KB であり、ベクトル検索ではない** |
| **模型網関層**（モデル接入・安全過濾・コスト） | ⚠ **未実装（意図的）** | L133「⚪ 単一ツール構成のため意図的に非実装」／L112-116「**欠落ではなく、単一ツール構成における意図的な非実装**として記録する」 |

> **粒度差の中身**（L141・L154）：v1 は「**业务理解Agent → 设计Agent → 编码Agent → 测试Agent**」の
> **4 体**を想定する。本骨架は**8 体のノード実行体**で実現している。
> **数を減らしたのではなく、細かくした**。PPT の 4 体は本骨架では
> 要件＝node1／設計＝node2・node3・node4／製造＝node5／テスト＝node6・node7 に対応する。

---

## 3. 既に具备で、かつ PPT に無いもの

`ppt-deviation-register.md` §2 に **A-1〜A-20（A-16 は予約欠番）**を登録済み。
このうち「PPT が"理念"としてしか書いていないものを"機械"にした」4 件が効いている。

| 追加要素 | PPT 側の対応要求 | 本骨架が足したもの |
|---|---|---|
| **A-2 / A-3** 6 重門番 | S28「CI に組み込み、品質ゲートとして強制する」 | `tools/trace_check` gate1〜6（野号／双方向追跡／7 字段／生成物一致／命名分区／機密ゼロヒット） |
| **A-6** 受控回流 | S24 成果物の二重化 | 規則 00 §11：顧客が Excel に直接赤字を入れる運用を**禁止せず、記入欄という出口を作る** |
| **A-19 / A-20** 変更・指摘環 | S15「改修時の影響範囲を分析する」 | `nodes/n09-change.md`＋`tools/impact.py`（下流／上流／推奨作り直し順）＋`tools/registry.py`（唯一の書込み口） |
| **A-17** 知識飛輪 | v1 S5「学习闭环必须不断开…一次踩坑、全员同步学会」 | `.claude/rules/06-knowledge-flywheel.md`（踩坑→規則化→検査追加→全隊免疫） |

---

## 4. 缺口は 3 類だけ

### ① プラットフォーム層 — `tools/` に 1 つも無い

`tools/**/*.py` を gateway / RAG / vector / embedding / KPI / audit / cost / token / LLM で
走査した結果、**命中 0**（唯一の LLM 言及は `tools/masking` の「外部 LLM に投げる前の関門」の説明文）。

| 要求機構 | 在るか |
|---|---|
| 模型網関（多モデルルーティング・機密はローカル） | ❌ |
| RAG／ベクトル検索 | ❌ |
| KPI 実測（生産性・品質・AI 活用度・網羅性・リードタイム・知識資産） | ❌ |
| 監査ログ（誰が生成し、誰が修正し、誰が採用したか） | ❌ 相当物のみ（gate6＝gitleaks 相当 ／ commit の Trace-AI-Review 三段） |
| コスト管理（token 計量・案件別配賦） | ❌ |
| 評測セット（モデル出力を採点） | ❌ 相当物のみ（`docs/00_plan/review.md` の CP 12 項） |
| 権限（役割別） | 🔶 `.claude/settings.json` は **deny 6 パターンのみ**（allow なし・自動承認なし） |

> **PPT 自身の優先順（v1 S12）**：**先做接入层模板库 + 知识库 RAG → 再逐步建设编排层和模型网关层**。
> 本骨架は接入層と知識庫層まで来ている。**次に来るべきは「編排層の実測」であって、
> いきなりの網関建設ではない。**

### ② 検証缺口 — **1 回も走っていない**（最重要）

```
docs/00_plan/coach/R60Login/n01.yml → state: not_started / steps_done: 0 / approved_by: []
SessionStart フックのブリーフ → 「R60Login（tutorial） 0/8 已承认」
tutorial/R60Login/ → 节点1・节点2 は人の記入済み、节点3〜8 は入力テンプレートのみ
```

**14 体の agent・5 つの skill・6 道の門は、いまだ一緒に走ったことがない。**
したがって「具备しているか」への厳密な答えは
**「コードは具备、能力は未検証」**である。

### ③ 内容缺口 — 56 画面カードは 1 枚

`docs/90_knowledge/legacy-r60/screens/` に `R60Login.md` が 1 枚だけ。
（これは 2026-10-14 の裁定「先 R60Login 垂直打通，确认质量后再横向铺开」どおりの状態。）

---

## 5. では何をするか（推奨順）

**先にプラットフォームを埋めない。先に走らせる。**

| 步 | やること | なぜこの順か |
|---|---|---|
| **1** | 1 画面を coach＋8 agent で**节点1→节点8 まで走破**（人は 4 つの門で拍板するだけ） | **新規機構を一切作らない**。既存資産だけで「使えるか」を判定できる唯一の方法 |
| **2** | 走破の**詰まりを記録**する（どの agent の産出が使えない／どの門が誤報・漏報した） | 缺口の優先順は**実戦が露呈させる**もので、机上で決めると外す |
| **3** | 露呈した順に埋める。自然な優先順は **KPI 実測 → 監査痕跡 → 評測セット → 権限** | 前三者は「AI 産出を統制できるか」。権限は組織の話で、後ろに置ける |
| **4** | 模型網関／RAG | 「閉域内のローカルモデルを呼ぶ」または「56 画面＋複数歴史案件で Grep が効かなくなる」まで着手しない |

### 走破の題材（2026-10-14 のユーザー裁定）

**R60Login を使う。** 理由：`screens/R60Login.md` の知識卡が既にあり、
**人が書いた版（`Front-end/src/views/R60Login.vue`・`R60LoginController.py`）と逐行対照できる**ため、
「AI 産出物の質」を測る基準が同時に手に入る。

---

## 6. 未決事項（人が裁定する）

| # | 問い | 選択肢 | 状態 |
|---|---|---|---|
| 1 | 走破の題材 | **R60Login**（裁定済 2026-10-14） | ✅ 決着 |
| 2 | 走破の記録先 | `docs/90_knowledge/agent-run-record.md` | ✅ 決着 |
| 3 | ①②③ のうち、どれから埋めるか | ② 検証が先（本表の推奨） | ⚪ **未決** |
| 4 | 模型網関を建てるか、建てないか | 建てない（規則 00 §13・PPT v1 S11 と整合） | ⚪ **未決** |

> **規則（`.claude/rules/**`）と PPT の間に矛盾は見つかっていない。**
> 本評価で骨格側の規則を書き換える必要は生じていない。

---

## 7. 出典

- 要件源（読み取りのみ）：`D:\AI_knowledge\方案与落地\AI実践に基づくソフトウェア開発プロセスの再考_落地篇.pptx`（30 頁）・同 `基于统一 AI 平台的全生命周期软件工程方案_v1.pptx`（13 頁）
- 実装側の実測：`.claude/agents/**`・`.claude/skills/**`・`.claude/rules/**`・`tools/**`・`docs/00_registry/ids.yml`・`docs/00_plan/**`・`.github/workflows/ai-gate.yml`・`.claude/settings.json`（2026-10-14 実行）
- 骨架側の既存整理：[platform-map.md](platform-map.md)・[v1-platform-4layer.md](v1-platform-4layer.md)・[ppt-deviation-register.md](ppt-deviation-register.md)・`ROADMAP_3PHASE.md`・`docs/00_plan/spec.md`・[ai-dev-playbook.md](ai-dev-playbook.md)・[dual-deliverable.md](dual-deliverable.md)

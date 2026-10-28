---
id: RULE-000
type: project-global
req_ids: [SPEC-C-TECH-1, SPEC-C-TECH-2, SPEC-C-TECH-3, SPEC-C-TECH-4, SPEC-C-TECH-5, SPEC-C-BIZ-1, SPEC-C-BIZ-2]
status: draft
sensitivity: internal
owner: AI-SE
version: 0.2.0
---

# プロジェクト全体硬约束規則（13条）

> **実行モデル**: 本プロジェクトは Claude Code を唯一の実行ツールとする。Claude Code が 8 工程
> （要件理解／基本設計／詳細設計／框架構築／製造／単体テスト／結合総合テスト／リリース運用保守）
> のすべてを実行し、人間はレビュー／承認ゲート（要件合意・設計評審・合否判定・リリース判定）を
> 保持する。第二のツールは存在しない。

## 1. 暗号化方式は案件ごとに確定する（AES-256-ECB は骨架の既定ではない）
**Summary**: ログイン認証・暗号化項目の**方式は骨架が一律に固定しない**。`migration` は案件プロファイル
（`docs/01_context/case-profile-<案件>.yaml`）が与える既存方式、`greenfield` は工程 04 で人が承認した
設計が方式を定める。復号は**案件が指定する復号関数**を必ず使用する（R60 は `R60_DECRYPTION_FNC`）。
- **R60 実例（`migration`）**: AES-256-ECB **ではない**。既存設計書が定める「桁変換＋当日 `yyyymmdd` 加算」の方式
  （詳細は案件の設計成果物を単一ソースとする）。復号は `R60_DECRYPTION_FNC`。
- **AES-256-ECB を採用する案件**は、その旨を案件プロファイル／承認済み設計に明記する。
  骨架の既定として主張してはならない（本項の旧版がそう書いていたのは誤り。2026-10-20 是正）。
- 参照: spec.md Constraints Technical 3（同じ一般化を行う）

## 2. Oracle NLS_DATE_FORMAT = 'RR-MM-DD'
**Summary**: Oracleセッション・SQL全般で NLS_DATE_FORMAT は固定 'RR-MM-DD' を使用、変更禁止。
- 参照: spec.md Constraints Technical 3

## 3. PrimeVue Select bindLabelClickListener → no-op
**Summary**: PrimeVue Select コンポーネントの bindLabelClickListener は no-op（空実装）とし、ラベルクリックによる意図しない展開抑止。
- 参照: spec.md Constraints Technical 1

## 4. Blob 応答インターセプタ → JSON 変換
**Summary**: HTTP応答が Blob 型の場合、インターセプタ層で自動的に JSON にパースする処理を必ず挿入。
- 参照: spec.md Constraints Technical 1（Vue3+PrimeVue 栈既定挙動）

## 5. ページネーション推奨 ROWID
**Summary**: Oracle 検索一覧のページング処理は原則 ROWID 方式を採用、OFFSET-FETCH は doc/01 の報告書に基づき必要時のみ使用。
- 参照: spec.md Constraints Technical 2

## 6. 野号厳禁（必ず ids.yml 登録）
**Summary**: R-ID/F-ID/I-ID/D-ID/L-ID/E-ID/TC-ID 等の全 ID は docs/00_registry/ids.yml が唯一発番口、未登録番号（野号）は trace_check で Exit 1。
- 参照: spec.md Constraints Business 2 / NFR-1

## 7. 7種 commit 形式 + Trace/AI/Review 三段付与
**Summary**: commit種別は req/design/feat/test/fix/rel/chore の7種固定、本文には Trace:R-xxx/F-xxx/L-xxx + AI:code-from-design-trans-cosmos-ai@v0.1 + Review:SE-xxx の三段を必記。
- 参照: spec.md Constraints Technical 5 / FR-6

## 8. parallel 新版 R60Common / r60util 禁止（`migration` 案件固有）
**Summary**: **`build_mode: migration` の案件に限る**。既存 R60Common.ts 54 関数・r60util.py 31 クラスを唯一真源とし、並行新版の作成・分岐を禁止。Claude Code はスキル実行時に既存関数へコメントでマッピングする。
**既定の `greenfield` 案件では適用対象が無い**（再利用すべき既存資産が存在しない）。共通部品は本案件で新規定義し、以降それ自体が唯一真源となる。
- 参照: spec.md Constraints Technical 4

## 9. trace_check 必実行・スキップ禁止
**Summary**: commit 前・Push 前に `py -3 -m tools.trace_check --strict` を必ず実行、--skip オプションによる門隙突破を禁止。
- 参照: spec.md NFR-3 / AC-2 / AC-6
- **コマンド表記**: ローカル（Windows／社内網）は `py -3 -m tools.xxx`、CI（ubuntu-latest）は `python -m tools.xxx`。裸の `python` は Windows で Microsoft Store のスタブに解決される場合があり起動しない。

## 10. Phase1 ベースライン src/app/routers 生産コード不触（`migration` 案件固有）
**Summary**: **既存の生産コードを持つ案件（`migration`）に限る**。Phase1 期間中は既存の src/ ・ app/routers 生産コード一切変更禁止、新規 assets（.claude/ / docs/ / tools/）のみ操作。
**`greenfield` 案件では「既存生産コード」が存在しない**ため、本項は空条件である（工程 05 で作るコードは本項の対象ではなく、通常のレビューゲートに従う）。
- 参照: spec.md Non-Goals 1 / NFR-5

## 11. 成果物の二重化は単一ソース厳守、顧客の赤字は「受控回流」で受ける
**Summary**: 機読源（`.md` + `.yaml`）が唯一の真源。人向けの日文正式 Excel / Word / HTML ビューは
**必ず機読源から生成**し、**生成物を手で編集しない**（FR-3）。
対日案件では顧客が Excel に直接赤字で修正を入れるのが常態であるため、**禁止ではなく出口を用意する**。

- **禁止する回路（双向回路）**: 機読源 → Excel → 人が Excel 本文を改変 → 改変版を AI に渡して `.md` へ逆変換。
  → 同一フィールドが二箇所で定義され（NFR-1 違反）、どちらが正か判別できなくなる。
- **許可する回路（受控回流）**: 機読源 → 生成（**正文は読み取り専用**）＋ 別シート「指摘シート／レビュー欄」
  （行番号・R-ID 付き）を添付 → 顧客は**そこにのみ**記入 → AI は**その欄だけ**を読んで機読源を修正 → 再生成。
  → 正文が改変されないため、二重化も diff 逆推も発生しない。
- **顧客への確認は「確認依頼書」で行う**: 未確定事項＋記入欄だけを渡し、機読源の全文は渡さない。
  確認依頼書は「質問」であり同一業務フィールドの再定義ではないため、NFR-1 には抵触しない。
- **記入欄以外は書き換えないよう顧客に明示する**（理由も添える：「本文と回答が混ざると、どちらが正か判別できなくなるため」）。
- 参照: spec.md FR-3 / NFR-1、`tools/gen_formal/README.txt`、`docs/00_plan/review.md` CP-R-3、`ROADMAP_3PHASE.md` Phase2-1
- 実例: `tutorial/R60Login/节点1_需求/03_客户確認依頼書（AB類）.md`（A=顧客が決める／B=当方の提案・顧客が承認／C=我方内部で決定）

## 12. 成果物は「人が読める」こと。ただし Phase1 は `.xlsx` を作らない
**Summary**: 節点成果物の `.md` は日本語の機読源であり、そのままでは
6 列の広表が折り返されず肉眼レビューが困難（特に「輸入項」「待確認事項」＝人が最も見たい表）。
**人向けの閲覧ビューは同名の `<name>.zh.html`（中文）** とし、`tools/gen_view` で機読源から生成する。

- **媒体は 2 本だけ（2026-10-21 ユーザー指示）**：
  **`.md`＝日本語のみ、`.zh.html`＝中文のみ。**
  日本語の `.html` は作らない（日中の 2 本が並ぶと、どれが正式か分からなくなるため）。
  中文ビューの名前は**節点1 の既存慣行どおり `<name>.zh.html`** とする（2026-10-21 ユーザー指示「合节点1统一」）。
- 実行: 中文に書き直した `<file>.zh.md` を用意し、
  `py -3 -m tools.gen_view <file>.zh.md -o <file>.zh.html` → **`<file>.zh.md` を削除**（`Ctrl+P` で PDF 化可）
- 自己検証: `py -3 -m tools.gen_view --self-test` → Exit 0
- **これは可読性の道具であり合格条件ではない**。合格判定は各節点の `02_確認事項一覧.md` と
  `py -3 -m tools.trace_check --strict` で行う。
- **Phase1 は `docs/**` に `.xlsx` を作ってはならない**（`find docs -name "*.xlsx" | wc -l == 0` が
  CP-R-3 の合格条件。**この条件は変わらない**）。
  **ただし `reports/` 配下（gitignore 区）に目視・対外ドラフト用の `.xlsx` を作ることは許す。**
  `py -3 -m tools.gen_formal.book --md <file>.md --out reports/<…>.xlsx` がその入口である。
  理由：節点8 で「正式 Excel」を出す要件（ユーザー指示 2026-10-21）と、`docs/` を機読源だけに保つ
  原則（NFR-1）は両立させられる。**生成物はいずれも手で編集しない**（次回生成で消える）。
  **基本設計書は Stop フック（`tools/gen_formal/auto.py`）が自動で描き直す**——機読源が xlsx より
  新しければ 1 ターン終了ごとに再生成し、更新が無ければ何もしない（ユーザー指示 2026-10-22）。
  自動出力は `reports/_auto/<case>/<節点>/<stem>_预览版.xlsx`。`_预览版` は目視用の下書きの印であり、
  顧客交付物ではない（正式版は節点8 で `_正式版` を付けて別に出す）。旧稿（`01_`/`04_`）は自動対象外。
  `book` は出力パスに `docs` を含むと **Exit 2 で拒否する**（規則の機械化）。
  顧客テンプレートへの接続と受控回流は Phase2（`tools/gen_formal/README.txt`）。
- Phase1 で顧客に出す正式媒体は、確認依頼書（Markdown → gen_view → PDF）までとする。
- 参照: spec.md FR-3、`docs/00_plan/review.md` CP-R-3、`tools/gen_view/README.txt`

### 12.1 節点成果物の媒体・言語は固定する（2026-10-20 ユーザー指示・毎節点で同じ）

| 成果物 | 正式媒体 | 言語 | 人向けビュー（残す） | 必ず削除するもの |
|---|---|---|---|---|
| `02_確認事項一覧.md` 等の内部成果物 | `.md`（機読源） | 日本語 | **同名 `.zh.html`（中文）** | `.zh.md`・日本語 `.html` |
| `03_客户確認依頼書（AB類）.md` | **PDF（顧客交付）** | **日本語** | **無し（PDF のみ）** | 一時日本語 `.html`・`.zh.md`・`.zh.html` |
| `03_技術者検討課題（C類）.md` | **PDF（顧客交付）** | **中文** | **無し（PDF のみ）** | 一時 `.zh.html`・`.zh.md` |

- **理由**: AB は顧客に渡す文書なので**顧客の言語（日本語）**で出す。C は**当方内部の検討課題**であり、
  読むのは中国語話者の開発側なので**中文**で出す。**顧客に渡すのは PDF だけ**。
  ただし**社内で読むための中文 `.zh.html` は内部成果物に 1 本ずつ残す**（2026-10-21 ユーザー指示）。
  **残さないのは日本語の `.html`** である。
  **★例外：`03_客户確認依頼書（AB類）` と `03_技術者検討課題（C類）` は PDF だけを残す**
  （2026-10-21 ユーザー指示「这两个只需要 PDF」）。中文ビューは作らない。
- **AB の作り方**: 機読源（日本語 `.md`）→ `gen_view` → **一時**日本語 `.html` → ヘッドレスブラウザで PDF →
  **一時 `.html` を削除**。翻訳を挟まない（機読源が既に日本語であるため）。中文ビューは作らない。
- **C の作り方**: 機読源（日本語 `.md`）→ **中文に書き直した `.zh.md`** → `gen_view` → **一時 `.zh.html`** →
  PDF（顧客交付）→ **`.zh.html` と `.zh.md` を削除**。残すのは PDF だけである。
- **★中文ビューは自然な中国語で書く**（2026-10-21 ユーザー指示：「注意避免**中式日文**」）。
  日本語の語順・語彙を漢字に置き換えただけの文（不中不日の直訳調）は不可。
  そのうえで、**実装値は原文のまま**残す（次項）。
- **★中文の派生ビューでも、実装値を翻訳してはならない**（2026-10-20 追加）。
  画面上の固定文言・画面名・項目名など、**そのまま実装される値**は**日本語のまま**残し、
  必要なら直後に「（原文为日文，按原文实现）」と注記する。
  **訳すと仕様が変わる**——たとえば C-06 の論点は「固定値 `共通マスタ　ログイン`（全角空白を含む）」
  そのものであり、中文に訳すと論点が消える。中文ビューの「本文に仮名 0」は**説明文についての基準**であり、
  **引用された実装値には適用しない**。
- **毎回同じ出力にする**。節点 1〜8 のいずれでも、この 2 文書を出すときは上の表に従う。
  `deliverable-reviewer` は本表を出力契約として持つ
  （`.claude/skills/trans-cosmos-ai-lifecycle-coach/references/node-worker-contract.md` も同旨）。
- **PDF 化コマンド**（Windows・Edge）:
  `"/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" --headless --disable-gpu --no-pdf-header-footer --print-to-pdf="<abs.pdf>" "file:///<abs.html>"`

## 13. 顧客指示優先・専線環境での単一ツール維持（**紅线ではない**）
**Summary**: 社内実績（SDS3）の統制事項を取入れる。**専線網絡（顧客の閉域網）内で作業する場合、
勝手に各種 Agent をインストールしたり、任意の大モデルを呼び出したりしない。AI 方面の推進は顧客の指示に従う。**

- **出所**: 社内 AI 実績 PPT `AI在实际项目中的运用实绩_SDS3.pptx`（注意事項の頁）。
  これは**要件源（PPT 2 份）に無い追加要素**である（登録: `ppt-deviation-register.md` §2）。
- **本骨架での意味**: `CLAUDE.md` §0 の「Claude Code 単一ツール」構成を維持する。
  顧客環境において別 Agent・別モデルの導入を提案する場合は、**顧客の明示指示を先に得る**。
- **境界（誤解しやすい点）**: 本項は **紅线ではない**。紅线は `CLAUDE.md` §1 の **7 条のまま**である。
  理由: `grep -c "7 条红线"` に依存する機械検査が 5 箇所
  （`docs/00_plan/review.md` CP-R-1 / `docs/00_plan/spec.md` / `docs/00_plan/tasks.md` 2 箇所 /
  `reports/AC-selfcheck.md`）あり、条数を増やすと同時に複数が落ちるため。
  **新しい横断規則は紅线ではなく `.claude/rules/` 側へ置く**（`rules/06-knowledge-flywheel.md` §2）。
- **運用**: 顧客から「この Agent を使ってよい」「このモデルを呼んでよい」という指示を得た場合は、
  その指示を `docs/01_context/` に記録し、以降はそれに従う。**口頭合意だけで進めない。**
- 参照: `docs/90_knowledge/internal/sds2-lessons.md` §3・§4

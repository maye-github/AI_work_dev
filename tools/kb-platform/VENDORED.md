# 这份代码是从哪儿来的

**来源**：`D:\AI_platform\kb-platform`（社内知识库基盤，Phase 0）
**复制日期**：2026-10-28
**原因**：本骨架要往知识库里灌 R60 的知识，但写到 `D:\AI_platform` 是改别的项目，撤不回来。
所以复制一份到本项目里，在本项目内完成接入。

## 复制时做了什么

- **没有复制** `data/kb.sqlite3`（372KB）。那是索引，`ingest` 一条命令就能重建。
- **没有复制** `__pycache__/`、`*.pyc`。
- 其余原样（`kbkit/`、`run.py`、`api.py`、`repo/` 的 7 篇示例、两份构建指南）。

## 这里的代码不是我们写的

**不要按本项目的规矩改它**（commit 7 种格式、7 字段 front matter 等都不适用）。

**也不要在抄本里改它。** 上游 `D:\AI_platform\kb-platform` 的实现规则是上游的决め事であり、
こちらが手を入れたり、変更を提案・commit したりしない（2026-10-29 ユーザー指示）。
我々の差分は **`tools/kb_local/`（本地拡張層）** に置き、`kbkit/` `run.py` `api.py` は
**上流と逐字一致**を保つ（合格条件は `py -3 -m tools.kb_vendor_manifest --check` の
「本地改変（コード）= 0」）。**上游是正，这份是抄本；抄本不动上游。**

## 怎么用

**`repo/projects/P-R60-001/` 就是知识正本，直接编辑，然后建索引。**
2026-10-29 之前链的是另一个方向（`docs/95_legacy/r60/` 为正本、`repo/` 是导出物），
那个方向的导出器 `tools/kb_export` **已停止使用**（运行即返回 2 并说明原因，留作映射规则的参考）。

```bash
# 1. 重建派生物：模块卡的 .md 视图（36 篇）＋ 检索摘要（7 篇）
#    幂等；正本没变时输出一模一样
py -3 -m tools.kb_migrate --apply

# 2. 建索引（差分，没变的不重建）
py -3 -m tools.kb_local ingest --prune

# 3. 查（检索、lint、评测都要走 tools.kb_local，见下「偏离 1」）
#    ★ 読権限の既定は「会社級のみ」。案件級を引くには --as <人> か --all が要る。
py -3 -m tools.kb_local search "エリアマスタ 排他制御" --as <人> --project P-R60-001 --top-k 5
py -3 -m tools.kb_local search "検索一覧は実項目で何件" --as <人> --project P-R60-001 --module R60Ssk
py -3 -m tools.kb_local search "テスト比率" --all          # 管理者（制限なし）

# 4. 状态 / 评测
py -3 -m tools.kb_local stats
py -3 -m tools.kb_local eval --all                         # 全体で測る（--as <人> でも可）
```

检索返回哪些状态，由 `tools/kb_local/_bootstrap.py` 的 `DEFAULT_RETRIEVABLE` 决定
（`active,open,baselined,changed,done`，可用环境变量 `KB_RETRIEVABLE_STATUSES` 覆盖）。
**`draft` 与 `void` 检索不到，这是有意的**——未定稿和作废的知识不该被当成答案。

> **上流 CLI（`py -3 tools/kb-platform/run.py …`）直接敲会看起来「坏了」**（2026-10-29 实测）：
> `search` 返回 0 件、`lint` 是 `NG 79 件の問題`、`eval` 是 `recall@5=0.500`（上流 demo 12 问还中，
> 案件 12 问全落）。原因不是坏了，而是上流只认 `status = 'active'`、只认它自己的状态词表。
> **用 `tools/kb_local` 就好。**（`ingest` / `stats` 走哪个都行。）

## 在规格书里是哪一个组件

`AI全链路软件工程平台_实施规格书.md` §11.2 の **组件④「ナレッジベース（RAG）」** 就是它。
按 §11.1 的七层，它同时占 **知識層（内容）** 和 **データ・コンテキスト層（索引）** 两层（§11.1.1 的对应表）。

**检索入口只有这一个。** `tools/rag` 不是第二个知识库，它是这套检索的**回归测试尺**
（§11.2 ⑤「評価・ガバナンス」、§13 KPI⑥「RAG検索のヒット率」），不往里加知识 → `tools/rag/README.md`。

## 依赖

上游声明只依赖 `numpy`。本机原来没装，为跑 `ingest` 装了：

```bash
py -3 -m pip install numpy     # 装的是全局 Python 3.14.3 环境
```

不想要了：`py -3 -m pip uninstall numpy`。但卸载后 `ingest` / `search` 跑不了（`lint` 也跑不了）。

---

## 本抄本对上游的偏离（2026-10-29 最终形）

**合否判定は 1 行で言える**: `py -3 -m tools.kb_vendor_manifest --check` の
**「本地改変（コード）= 0」**。`kbkit/` `run.py` `api.py` は上流と逐字一致である。

| # | 事項 | 置き場所 | 性質 |
|---|---|---|---|
| 1 | 骨架の状態語彙＋可检索状态 | `tools/kb_local/_bootstrap.py` | **本地拡張（上流コード不変）** |
| 2 | `module` / `scope` の絞り込み | `tools/kb_local/` | **同上** |
| 3 | `expect_heading` による節判定 | `tools/kb_local/evaluation.py` | **同上** |
| 4 | ディレクトリ頁を索引に入れない | `repo/` の置き方（README を `repo/` の外へ） | データの組織 |
| 5 | 生成物が `generated_by` を持つ | `tools/kb_migrate.py`（**`tools/` 側の我々のコード**） | 生成器 |
| 6 | `golden.yaml` に案件 12 問を追加・demo に `project` を補完 | `repo/eval/golden.yaml` | データ（規則ではない） |

### 1〜3: 上流を書き換えずに足した（本地拡張層）

上流には無いが我々に要る 3 つは、**上流のコードを 1 行も変えずに** `tools/kb_local/` で足した。
仕組みは `_bootstrap.py` の冒頭に書いてある。要点だけ:

- **状態語彙**: 骨架の状態機（`.claude/rules/02` §6）は `open/baselined/changed/done` を使う。
  上流の `search` は `status = 'active'` 固定、`lint` は `draft/review/active/deprecated` しか知らない。
  そのままだと「索引には入るが 1 件も当たらない／lint が NG」になる。
  → `_bootstrap.patched_candidates()` が `retrieval._load_candidates` を、`wider_statuses()` が
  `pipeline.STATUSES` を、**呼び出しの間だけ**差し替える。
- **`module` / `scope`**: 案件知識を 1 つの `project_id` にまとめたため、`R60User` の問いが
  `R60SesModel` の同型章に奪われる（実測 80 題中 3 件）。呼び方**は**モジュールを知っているのに
  口が無かった。→ 差し替えた `_load_candidates` が候補抽出の WHERE に押し込む
  （上流の鉄則「後掛けしない」に従う）。実測 `recall@5` 0.863 → 0.925、top-1 モジュール 76/80 → 80/80。
- **節判定**: doc 単位の的中は「モジュールは合っているが節が違う」を見逃す。
  実測 12 問中 2 問は doc 命中でも答えの節は 8 / 12 位（`top_k=5` の外）で、
  doc 級指標は `recall@5=1.000` のままだった。→ `evaluation.py` が `expect_heading` を持つ
  ケースだけ見出しまで判定し、`節recall` を出す。

**並び替え（dense+sparse → RRF → rerank）は上流の 1 本をそのまま呼ぶ。複製していない。**
上流が検索品質を上げれば、我々の数字も自動で上がる。

### 4: ディレクトリ頁（`company-README.md` / `projects-README.md`）は `repo/` の外に置く

`collect_docs()` は `repo/` 下の `.md` を**全部**索引に入れる（README 除外は無い）。
`repo/company/` に目次頁を置いたら、全 `doc_id` と主題語を並べているため
「テストケースの最低件数」「A/B/C 分類」「出典等級」の 3 問で 1 位を取り、
答えを書いた条目が top-5 から落ちた。目次の仕事は道案内であって、案内先と席を争うことではない。
→ **上流の `collect_docs()` は変えない**。我々が目次を `repo/` の外に置く。
（記録: `reports/audit/kb-integration/04_残留问题清单_2026-10-29.md` §1.2）

### 5: 生成物は front matter に `generated_by` を持つ（`tools/kb_migrate.py`）

`repo/projects/P-R60-001/` の 79 篇は派生物だが、以前は何の印も無く、手で直せそうに見えた
（手で直すと次の `--apply` で黙って上書きされる）。`tools/kb_migrate.py` の `merged_fm()` が
`generated_by: tools/kb_migrate.py` を出し、`stamp_existing()` が既存分にも補う（鍵だけ、本文は触らない）。
**これは `tools/` 側の我々のコードであり、`kbkit/` には入っていない。**
幂等: 2026-10-29 実測、`--apply` 2 回連続で 79 篇の SHA-256 が一致。

### 6: `repo/eval/golden.yaml` は上流 24 問＋案件 12 問（データ）

- 上流 demo の 12 問は `project:` を持たず、company scope だけを引くため `eval` が
  `recall@5=0.333` に固定されていた。`project: P-DEMO-001` を補って `1.000` にした。
- 案件 12 問（`module` / `expect_heading` 付き）を後ろに足した。**規則ではなくデータ**である。
- 同期のときは「上流の 24 問を残したまま末尾に 12 問を足す」だけ。手で当て直すのはここだけ。

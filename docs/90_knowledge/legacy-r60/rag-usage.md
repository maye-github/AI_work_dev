---
id: KNOW-LEGACY-R60-RAG-USAGE
type: knowledge
req_ids: []
status: draft
sensitivity: internal
owner: AI-SE
version: 0.1.0
---

# R60 知識ベースの RAG 索引 — 構築・検索・評価

> 対象：`docs/90_knowledge/legacy-r60/chunks/*.jsonl`（機読 chunk）と `eval/gold-qa.yaml`。
> 実装：`tools/rag/`（Python 標準ライブラリのみ）。
> 設計方針の原典：`learning-plan-3modules.md` §6〜§7。
> 本ファイルは**実装後の実測値**を記録する。計画値と異なる箇所はそのまま書く。

---

## 1. 何を作ったか

| 物 | 場所 | 役割 |
|---|---|---|
| chunk 生成 | `reports/module-survey/<module>/make_chunks.py` | 卡片 → JSONL。モジュールごとに 1 本 |
| chunk 語料 | `docs/90_knowledge/legacy-r60/chunks/<module>.jsonl` | 機読・可審査。12 字段固定 |
| 索引構築 | `tools/rag/loader.py` / `store.py` | JSONL を検証し SQLite を再生成 |
| CLI | `tools/rag/__main__.py` | `build` / `query` / `eval` / `stats` |
| 金標問答 | `eval/gold-qa.yaml` | 80 問（6 モジュール） |
| 評価報告 | `reports/rag/eval-*.json` | 設問ごとの hit / rank / 取得 chunk |

索引は `build/rag/` に置き、`.gitignore` で除外する。**語料（JSONL）からいつでも再生成できる**ため、
索引ファイル自体は成果物ではない。

---

## 2. 語料の現状（実測 2026-10-19）

### 2.1 teaching（教材）

| モジュール | chunk 数 | 位置づけ |
|---|---:|---|
| `R60Area` | 57 | 骨架の貫通例（既存） |
| `R60Ssk` | 52 | 簡単・主教材（更新専用） |
| `R60User` | 19 | 簡単・補完（薄い 4 類） |
| `R60Plc` | 68 | 中等・主教材 |
| `R60Maker` | 44 | 中等・フル |
| `R60SesModel` | 80 | 複雑・主教材（主従 4 画面・6 テーブル） |
| `R60KkuChi` | 21 | 複雑・補完（薄い 4 類） |
| **合計** | **341** | |

`artifact_type` の内訳：logic 96、field 63、review 46、api 45、screen 35、error 32、
test 21、convention 3。

### 2.2 holdout（考题側）

現在 **3 chunk** のみ。内容は `R60Ssk` / `R60Plc` / `R60Maker` の
「廃止_画面項目内容(入力)」シート（いずれも `R60Maker` の残骸）である。
**これは R60Login の実装ではない。** R60Login の実装を holdout に入れるのは、
練習（節点 8 以降）を始める時点である。

> `corpus_scope` は「教材に出してよいか」の印であり、`holdout` は
> 「まだ答えを見せない」という意味である。**R60Login の設計書は teaching に入れてよい**
> （入力であって答えではない）。**`.vue` / `.py` の実装だけを holdout に入れる。**

---

## 3. 使い方

```bash
# 1. 索引を作る（teaching と holdout を物理的に別ファイルへ）
py -3 -m tools.rag build --scope all

# 2. 検索する（節点は module を指定できる）
py -3 -m tools.rag query "排他チェックの条件" --module R60Plc -k 5 --text 160

# 3. 評価する
py -3 -m tools.rag eval --gold eval/gold-qa.yaml \
  --report reports/rag/eval-2026-10-19.json

# 4. 節点へ渡す context_bundle を作る
py -3 -m tools.rag bundle --node n03 --module R60Plc \
  --query "排他チェック" -k 8 --out build/rag/context_bundle_n03_R60Plc.json

# 5. 索引のメタ情報
py -3 -m tools.rag stats --scope teaching
```

- `build` は**毎回 DB を作り直す**（追記しない）。同じ語料からは同じ `corpus_sha256` になる。
- `query --json` は chunk 全体を返す。`context_bundle` を作る場合はこれを使う。
- `eval` は既定で `--min-recall 0.80` / `--min-module-recall 0.75` を下回ると Exit 1。

---

## 4. 検索方式（実装の事実）

1. **SQLite FTS5 `tokenize='trigram'`** を張る。3 文字以上の語は FTS5 の BM25 で候補を取る。
2. **決定論的な文字 n-gram スコアラ**を併用する。日本語の 2 文字語（「排他」「登録」）は
   trigram で 0 件になるため、2-gram / 3-gram の IDF 重み付き一致で補う。
3. スコア融合は**辞書順位を主、FTS を副**とする（`3/(10+rank)` と `0.5/(60+rank)`）。
   初期実装は RRF 等重みだったが、モジュール名（`R60Ssk` 等）が全 chunk に現れるため
   FTS が全件を拾い、期待 chunk が 5 位圏外に落ちた。**モジュール名をクエリ語から除外**し、
   辞書スコアを主にすることで解消した。
4. `--module` 指定時は**語料をそのモジュールに限定してから**ランキングする。
   節点は対象モジュールを知っているため、これが実運用の既定である。

**やっていないこと**：embedding、外部モデル、形態素解析器。専線環境で動くことを優先した。
BM25 の recall が不足した場合に初めて第二版（ハイブリッド）を検討する。

---

## 5. 評価結果（2026-10-19）

| 指標 | 値 | 閾値 |
|---|---:|---:|
| recall@5（module 指定あり） | **1.000** | ≥ 0.80 |
| strict recall@5（module 指定あり） | **1.000** | — |
| MRR（module 指定あり） | **0.901** | — |
| unsupported rate | **0.000** | = 0 |
| recall@5（module 指定なし） | 0.863 | 参考値 |
| MRR（module 指定なし） | 0.645 | 参考値 |

モジュール別（指定あり）は 6 モジュールすべて recall@5 = 1.000。
報告の生データは `reports/rag/eval-2026-10-19.json`。

### 5.1 この数字を過大に読まないこと

- 80 問は**卡片を書いたのと同じ AI が作成した**。独立した出題者ではない。
  したがって recall 1.000 は「检索器が自分の書き方に合っている」ことを示すにとどまる。
- **citation accuracy は測っていない**。回答文を生成していないため、引用が回答を支持するかは
  判定できない。数値を出すには、検索結果から回答を生成する工程が別に要る。
- module 指定なしの 0.863 は、モジュール間で似た chunk（排他・ソート・削除）が競合するため。
  実運用では `--module` を渡すので、こちらを主指標にしない。

---

## 6. 8 工程への接続（次の作業）

節点ごとに `context_bundle.json` を作る。形は `learning-plan-3modules.md` §8 のとおり。

```json
{
  "node": "n03",
  "module": "R60Plc",
  "query": "排他チェック",
  "chunks": [
    {"chunk_id": "PLC-LGC-011", "text": "...", "source": "03-logic.yaml ; logics[L-PL-11]"}
  ],
  "token_estimate": 1200
}
```

- 取得は `bundle --node <nXX> --module <module> --query "..." -k 5..10`。
  `token_estimate` は**文字数からの保守的推定**であり、実トークナイザの値ではない。
- **語料全体をプロンプトへ入れない。** 命中した 5〜10 件と出典だけを渡す。
- 練習期は `--scope teaching` のみ。`holdout` は節点 8 の対比まで開かない。

---

## 7. 未確定・限界

| # | 事項 |
|---|---|
| 1 | citation accuracy の測定手段が未実装（回答生成が前提） |
| 2 | 金標 80 問は自己作成。第三者出題による再評価が望ましい |
| 3 | holdout 索引は現時点で R60Login を含まない（廃止シート 3 件のみ） |
| 4 | embedding / 形態素解析は未導入。2 文字語は n-gram 補完に依存する |
| 5 | `R60Area` は教材セットの 6 モジュールに含まれないが、骨架の貫通例として索引に残している |

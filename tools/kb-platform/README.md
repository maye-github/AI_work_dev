# kb-platform — 知識ベース基盤（Phase 0）

会社共通＋案件固有の知識を 1 つのリポジトリで管理し、検索 API として引くための最小構成。
外部サービス不要（Python + numpy + SQLite のみ）で、`git clone` 直後にそのまま動く。

Phase 0 の目的は**方式の検証**であり、性能・精度の本番品質は目指さない。
本番構成への移行点は「[本番移行](#本番移行)」を参照。

---

## 設計の鉄則

1. **Git が正本**。`repo/` 配下の Markdown だけが真実。索引はいつでも捨てて作り直せる。
2. **索引は派生物**。`data/kb.sqlite3` は gitignore 対象。壊れたら `--reset`。
3. **権限は SQL で先に絞る**。検索結果を後からフィルタしない（情報漏えい防止）。
4. **差分だけ取り込む**。文書の sha256 が変わらなければ再索引しない。

---

## 必要環境

| 項目 | 要件 |
|---|---|
| Python | 3.10 以上（動作確認: 3.14.3） |
| 依存 | `numpy` のみ（動作確認: 2.4.6） |
| シェル | Git Bash / bash / PowerShell いずれも可 |
| 任意 | `fastapi` + `uvicorn`（`api.py` を使う場合のみ） |

```bash
python -c "import numpy; print(numpy.__version__)"
```

---

## ディレクトリ構成

```text
kb-platform/
├── README.md               本ファイル（日本語）
├── readme_cn.md            中国語版
├── run.py                  CLI（lint / ingest / search / eval / stats）
├── api.py                  任意の FastAPI ラッパ（fastapi 導入時のみ）
├── .gitignore
│
├── kbkit/
│   ├── fm.py               front matter（YAML サブセット）パーサ
│   ├── chunker.py          見出し / 表行 / コードブロック単位の分割
│   ├── embedder.py         埋め込み（hash = 既定 / bge-m3 = 本番）
│   ├── store.py            SQLite スキーマとアクセサ
│   ├── retrieval.py        権限フィルタ + RRF 融合 + rerank
│   ├── pipeline.py         lint / ingest / prune
│   └── eval.py             ゴールデンセット評価
│
├── repo/                   ★ ナレッジ本体（Git 管理の正本）
│   ├── company/            全案件共通
│   │   ├── standards/      規約・標準
│   │   ├── glossary/       用語集
│   │   └── patterns/       設計パターン
│   ├── projects/
│   │   └── <案件ID>/        案件固有（例: P-DEMO-001）
│   │       ├── requirements/
│   │       ├── design/basic/
│   │       ├── design/detail/
│   │       └── test/
│   └── eval/golden.yaml    検索品質のゴールデンセット
│
└── data/
    └── kb.sqlite3          索引（派生物 / gitignore）
```

`repo/eval/` は索引対象外。文書ではなく評価データとして扱う。

---

## クイックスタート

```bash
cd d:/kb-platform

python run.py lint                                  # 1. 記述ルールの検査
python run.py ingest --all                          # 2. 索引の作成
python run.py search "在庫不足のときのエラーコードは？" \
       --project P-DEMO-001 --context               # 3. 検索
python run.py eval --project P-DEMO-001             # 4. 品質評価
```

`run.py` はどこから実行しても動く（パスは `run.py` の位置を基準に解決）。

### 実行例

```text
$ python run.py ingest --all
追加=7 更新=0 スキップ=0 チャンク=74
索引: 文書7 / チャンク74 / model=['hash-ngram-1024']

$ python run.py eval --project P-DEMO-001
cases=12  top_k=5  recall@5=1.000  MRR=0.917
...
しきい値 recall@5 >= 0.85: PASS
```

---

## コマンドリファレンス

共通オプション（全サブコマンド）:

| オプション | 既定値 | 説明 |
|---|---|---|
| `--db` | `data/kb.sqlite3` | 索引ファイル |
| `--repo` | `repo` | ナレッジのルート |
| `--embedder` | `hash` | `hash`（依存なし） / `bge`（要 sentence-transformers） |

### `lint` — 記述ルールの検査

```bash
python run.py lint
```

front matter の必須キー、列挙値、doc_id の一意性、配置先ディレクトリとの整合を検査する。
問題が 1 件でもあれば終了コード 1（CI / pre-commit にそのまま置ける）。

### `ingest` — 索引への取り込み

```bash
python run.py ingest              # 変更された文書だけ
python run.py ingest --all        # 全件を再索引
python run.py ingest --reset      # 索引を全消しして作り直す
python run.py ingest --prune      # リポジトリから消えた文書を索引からも削除
```

`ingest` は 1 文書ごとに「既存チャンク削除 → 新規チャンク挿入」を同一トランザクションで行う。
途中で失敗しても中途半端なチャンクは残らない。

### `search` — 検索

```bash
python run.py search "楽観ロックに使うカラムは？" --project P-DEMO-001
python run.py search "..." --project P-DEMO-001 --top-k 10 --level 20
python run.py search "..." --project P-DEMO-001 --context   # LLM 用コンテキストも出力
python run.py search "..." --json                            # 機械処理用
```

| オプション | 既定値 | 説明 |
|---|---|---|
| `--project` | なし | 案件ID。指定すると「会社共通＋その案件」が対象。未指定なら会社共通のみ |
| `--level` | `30` | 利用者の権限レベル。`conf_level <= level` の文書だけが候補になる |
| `--top-k` | `5` | 返却件数 |
| `--context` | off | 引用付きのコンテキスト文字列を追加出力 |

### `eval` — ゴールデンセット評価

```bash
python run.py eval --project P-DEMO-001
python run.py eval --project P-DEMO-001 --top-k 10 --threshold 0.9
```

`recall@k` と `MRR` を出力し、既定のしきい値 `recall@5 >= 0.85` を下回ると終了コード 1。

### `stats` — 索引の状態

```bash
python run.py stats
```

文書数・チャンク数・scope 別件数・使用中の埋め込みモデル・文書一覧を表示する。

---

## ナレッジの書き方

### front matter

各 Markdown の先頭に必須。

```yaml
---
doc_id: REQ-001                    # 一意。英数字とハイフン
scope: project                     # company | project
project_id: P-DEMO-001             # scope=project のとき必須
title: 受注・在庫引当システム 要件定義書
doc_type: requirement              # 下記の列挙値
phase: requirement                 # 任意（工程）
version: "1.0"                     # クォート推奨
status: active                     # draft | review | active | deprecated
conf_level: 30                     # 10 公開 / 20 社内 / 30 案件 / 40 機密
owner: 要件定義チーム
updated_at: 2026-09-02
tags: [order, allocation]
---
```

| キー | 必須 | 内容 |
|---|---|---|
| `doc_id` | ○ | チャンクID・引用の基準。後から変えない |
| `scope` | ○ | `company` / `project` |
| `project_id` | △ | `scope=project` のとき必須。ディレクトリ名と一致させる |
| `title` | ○ | 4 文字以上。検索結果の引用に使う |
| `doc_type` | ○ | 下記の列挙値 |
| `version` | ○ | 設計書の版 |
| `status` | ○ | `active` 以外は検索対象外 |
| `conf_level` | ○ | 10 / 20 / 30 / 40 |
| `updated_at` | ○ | `YYYY-MM-DD` |
| `phase` / `owner` / `tags` | - | 任意 |

`doc_type` の列挙値:

`standard` / `pattern` / `glossary` / `requirement` / `design-basic` /
`design-detail` / `test` / `decision` / `incident` / `howto`

### 配置ルール

| scope | 置き場所 | 例 |
|---|---|---|
| `company` | `repo/company/<種別>/<任意>/` | `repo/company/standards/coding/general.md` |
| `project` | `repo/projects/<案件ID>/<工程>/` | `repo/projects/P-DEMO-001/design/basic/BS-001.md` |

`lint` は `project_id` と配置先ディレクトリの不一致を検出する。

### 本文の書き方

チャンク品質は本文の構造で決まる。

- **1 見出し = 1 トピック**。見出しは検索対象になるので、業務語を入れる。
- **表は 1 行 = 1 チャンク**になる。勘定科目・エラーコード・項目定義は必ず表にする。
  ヘッダ行は各チャンクに複写されるため、列名に意味を持たせる（例: `| コード | 内容 | 発生箇所 |`）。
- **箇条書きは 1 項目 1 文**。長い段落は分割される。
- 図・Excel・PDF はそのまま置かず、テキスト化した要約を Markdown にし、原本のパスを本文に残す。

---

## 取り込みの仕組み

```text
*.md 走査（repo/eval を除く）
  → front matter 解析
  → sha256 計算 → 前回と同じならスキップ
  → チャンク分割（見出し / 表行 / コード）
  → 埋め込み
  → 既存チャンク削除 → 挿入（1 トランザクション）
```

チャンク分割の規則:

| 単位 | 条件 | 備考 |
|---|---|---|
| 見出しセクション | `#` 〜 `######` | 長い場合は 700 文字で段落分割 |
| 表の行 | 表ヘッダ＋1 行 | 用語集・エラーコード表で効く |
| コードブロック | ``` で囲まれた範囲 | 分割しない |

チャンカーや埋め込みモデルを変えたら、必ず `--all` で再索引する
（sha256 は本文のハッシュなので、コード変更では差分が検出されない）。

---

## 検索の仕組み

```text
クエリ
  → SQL で候補を絞る（status / conf_level / scope / project_id）
  → dense（コサイン類似度）
  → sparse（文字 bigram の IDF 重み付き被覆率）
  → RRF で融合（k=60）
  → rerank（本文被覆 0.30 / 見出し 0.10 / タイトル 0.05 を加点）
  → top_k を引用付きで返す
```

**権限フィルタは候補取得の SQL の WHERE 句に入っている**。
ランキング後に除外する実装ではないため、権限外の文書がスコア計算に混ざらない。

現在の埋め込みは文字 n-gram のハッシュ（`hash-ngram-1024`）。
同義語・言い換えには弱い。この弱点は本番で bge-m3 に差し替えて解消する。

---

## 評価（ゴールデンセット）

`repo/eval/golden.yaml` に「質問 → 期待する文書ID」を並べる。

```yaml
- id: Q002
  question: 在庫不足を表すエラーコードは何番か
  expect: [REQ-001, BS-001]
  project: P-DEMO-001        # 省略時は --project の値
```

| 指標 | 意味 | 目標 |
|---|---|---|
| `recall@k` | 期待文書が top-k に 1 件でも入った質問の割合 | **0.85 以上** |
| `MRR` | 最初に正解した順位の逆数の平均 | 参考値（0.8 以上を目安） |

運用ルール:

- 案件ごとに **10 件以上**を用意する。要件・設計・テスト・用語の各層から満遍なく。
- ゴールデンセットは**検索の弱点を晒すため**のもの。落ちた問題を消して通すのは禁止。
- 文書を追加したら質問も追加する。評価が実態から遅れると意味がなくなる。

---

## 新規案件の立ち上げ手順

| # | 作業 | 完了条件 |
|---|---|---|
| 1 | `repo/projects/<案件ID>/` を作る | `requirements` / `design/basic` / `design/detail` / `test` の 4 ディレクトリ |
| 2 | キックオフ資料を Markdown + front matter で配置 | 要件定義・基本設計・用語・非機能の 4 点が揃う |
| 3 | `python run.py lint` | 問題 0 件 |
| 4 | `python run.py ingest` | エラー 0 件 |
| 5 | `repo/eval/golden.yaml` に案件の質問を 10 件以上追加 | 各質問に `expect` が入っている |
| 6 | `python run.py eval --project <案件ID>` | `recall@5 >= 0.85` |
| 7 | 以降、文書を更新したら `ingest` を実行 | 共作業は差分のみで数秒 |

### 日常運用

- 文書の変更は Pull Request で行い、CI で `lint` と `eval` を回す。
- 「同じ質問を 2 回したら同じ答えが返る」ことを最低品質線とする。
- 案件終了時、他案件でも使える文書は `company/` へ昇格させる。
  昇格時に固有名詞・顧客名・実データを一般化し、`conf_level` を下げる。

---

## 本番移行

| 項目 | Phase 0 | 本番 |
|---|---|---|
| 埋め込み | `hash-ngram-1024` | `bge-m3`（日英中、dense + sparse） |
| ベクトルDB | SQLite + 総当たり | Oracle 23ai `VECTOR` または Qdrant |
| API | CLI / `api.py` | 既存 FastAPI に `build_router()` で合流 |
| 権限 | `conf_level` の数値比較 | 文書単位 ACL（案件メンバー表と連携） |
| CI | ローカル実行 | マージ前に `lint` + `eval` を必須化 |

移行時に変えないもの:

- `repo/` のディレクトリ構成と front matter のスキーマ
- 候補を SQL で絞るという検索の形（`VECTOR_DISTANCE` に置き換えても WHERE 句の権限条件は残す）
- ゴールデンセットと評価指標

### 埋め込みの差し替え

```bash
pip install sentence-transformers
python run.py ingest --all --embedder bge
python run.py eval --embedder bge --project P-DEMO-001
```

`hash` と `bge` の索引は混在できない。切り替えたら必ず `--all`（または `--reset`）。

---

## API（任意）

`fastapi` 未導入の環境では `api.py` は import できない（`run.py` には影響なし）。

```bash
pip install fastapi uvicorn
uvicorn api:app --host 127.0.0.1 --port 8000
```

| メソッド | パス | 用途 |
|---|---|---|
| POST | `/kb/search` | 検索（`query`, `project_id`, `user_level`, `top_k`, `with_context`） |
| GET | `/kb/stats` | 索引の状態 |

既存アプリへ合流させる場合:

```python
from api import build_router
app.include_router(build_router("d:/kb-platform/data/kb.sqlite3"))
```

認証は持たない。必ず社内認証の内側に置き、`user_level` は認証済みユーザー情報から
サーバー側で決めること（クライアントから受け取った値をそのまま使わない）。

---

## トラブルシューティング

| 症状 | 原因と対処 |
|---|---|
| `front matter が '---' で閉じられていません` | 先頭の `---` と閉じ `---` の対応を確認 |
| `doc_id 'X' が ... と重複` | 同一 doc_id の文書が 2 つある。片方をリネーム |
| `project_id '...' と配置先ディレクトリが不一致` | `repo/projects/<案件ID>/` 配下に移動するか、front matter を直す |
| `scope=project には project_id が必須です` | front matter に `project_id` を追加 |
| 検索結果が 0 件 | 未 ingest / `--project` の指定違い / `conf_level` が `--level` より大きい |
| 文書を直したのに結果が変わらない | `ingest` 未実行、またはチャンカー変更後に `--all` をしていない |
| 引用の見出しがおかしい | 見出し階層（`#` のレベル）を確認して `ingest --all` |
| `ModuleNotFoundError: fastapi` | `api.py` を使う場合のみ `pip install fastapi uvicorn` |

---

## 既知の制約（Phase 0）

- 埋め込みは文字 n-gram のハッシュ。表記ゆれ・同義語・言い換えに弱い。
- SQLite の総当たり検索。実用上の上限は 1 万チャンク程度。
- 文書単位の ACL、監査ログ、インクリメンタルなベクトル更新は未実装。
- `api.py` に認証・レート制限はない。

---

## 参考

- 構築ガイド（案件起点）: `d:/JET/doc/03_AI/知識ベース構築ガイド_案件起点.md`
- ゴールデンセット: `repo/eval/golden.yaml`

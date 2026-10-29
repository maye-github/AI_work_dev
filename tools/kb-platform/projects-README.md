# `repo/projects/` — 案件知识（生成物，勿改）

> **本文件放在 `repo/` 之外，是有意的：它不进索引。**
> 2026-10-29 实测：目录页一旦被索引，它列出的 doc_id 与主题词会让它自己排在正文前面
> （问「テストケースの最低件数」时第 1 位是目录页，真正写了答案的条目不在前 5）。
> 同样的判断见 `company-README.md` 开头的说明。

> 上层说明：`tools/kb-platform/VENDORED.md`。上游正本：`D:\AI_platform`。

---

## 1. 这里的东西是生成的

`repo/projects/P-R60-001/**/*.md` 全部是**生成物**，每一篇的 front matter 都带：

```yaml
generated_by: tools/kb_migrate.py
```

**手で編集してはならない。** 次回の再生成で上書きされ、編集は消える。

| 何を直したいか | どこを直すか |
|---|---|
| モジュールカードの内容 | 同ディレクトリの `.yaml`（これが正本） |
| 検索摘要の本文 | `chunks/raw/<module>.jsonl`（1 行 1 chunk） |
| 見出し・節の切り方 | `tools/kb_migrate.py`（生成器そのもの） |
| 索引の対象・権限・スコープ | `kbkit/pipeline.py` / `kbkit/retrieval.py` |

直したあと：

```bash
py -3 -m tools.kb_migrate --apply          # .md を作り直す（何度実行しても同じ結果）
py -3 -m tools.kb_local lint
py -3 -m tools.kb_local ingest --prune
py -3 -m tools.kb_local eval
```

> **上流 CLI（`tools/kb-platform/run.py`）を直接叩かないこと。** 上流は `status = 'active'` 固定で、
> 骨架の状態語彙（`open` / `baselined` / …）を知らないため、我々の文書では `search` が 0 件・
> `lint` が NG になる。差分は `tools/kb_local/` にあり、上流のコードは逐字のまま
> （`UPSTREAM-SYNC.md` §3・`VENDORED.md` 偏离 1〜3）。

`--apply` は**冪等**である（2026-10-29 実測：2 回連続実行で全 79 篇の SHA-256 が一致）。
一致しない場合は生成器に時刻・乱数・順序不定の反復が混入している（`.claude/rules/03` §7.1）。

> **改行コードの但し書き**：生成器は `newline="\n"` で書く。本リポジトリは
> `core.autocrlf` によりチェックアウト時に CRLF へ変換されるため、
> **ハッシュ比較は同じチェックアウト状態の中で行うこと**（CRLF 状態と LF 状態を跨いで比べると
> 全篇が差分に見える）。git 側は staging で LF に正規化するので、差分は出ない。

## 2. 構成

| パス | 中身 | 正本か |
|---|---|---|
| `modules/<module>.yaml` | 詳細設計カード（ロジック・データ・エラー） | **正本** |
| `screens/<module>.yaml` | 画面カード | **正本** |
| `screens/<module>.md` | 上記から生成した閲覧ビュー | 生成物 |
| `modules/<module>-03-logic.md` 等 | 同上（節ごとに分割） | 生成物 |
| `chunks/raw/<module>.jsonl` | 検索摘要の生データ（1 行 1 chunk、`sha256` 付き） | **正本** |
| `chunks/<module>.md` | 上記から生成した検索摘要 | 生成物 |
| `review/` `howto/` | レビュー指摘・手順 | 生成物（移設元から写したもの） |

**案件事実はここに置く。** 会社共通の方法・標準は `repo/company/`（判据は `company-README.md` §1）。

## 3. 上流へ出さない

`repo/projects/P-R60-001/` は**顧客案件の資産**である。`D:\AI_platform`（全社）へは上げない。
上げてよいのは `repo/company/` に昇格させた条目だけであり、昇格の条件は
`company-README.md` §1 と §4 に書いてある。

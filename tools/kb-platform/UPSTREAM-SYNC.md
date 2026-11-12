# 上流 `D:\AI_platform` との同期と、社内への還流

> 対象: `tools/kb-platform/`（上流 `D:\AI_platform\kb-platform` の写し）。
> 上流の来歴は `VENDORED.md`、案件データの扱いは `projects-README.md`、
> 会社共通条目は `company-README.md`。

**基本方針（2026-10-29 ユーザー指示）**: **上流の実装規則は我々の持ち物ではない。**
`D:\AI_platform` に git があっても、我々の都合で上流のコードや規則を変える提案・commit はしない。
我々の差分は**すべて `tools/kb_local/`（本地拡張層）に置く**。上流は逐字のまま保つ。

---

## 0. いまの前提（2026-10-29 実測）

**上流は git リポジトリではない。** `D:\AI_platform\kb-platform` に `.git` も `VERSION` も無い、
ただのフォルダである（`find -maxdepth 3 -name .git` → 0 件）。

これは同期の設計を左右する。git があれば「何が変わったか」を git が教えてくれるが、
無い場合は**こちらで指紋を持つしかない**。だから `VENDOR_BASE.json` がある。

| 実測 | 値 |
|---|---|
| 上流のファイル数（`data/`・`__pycache__` を除く） | **23** |
| 本抄本で上流と一致 | **19** |
| 本抄本で手を入れた（**コード**） | **0** — `kbkit/` `run.py` `api.py` は上流と逐字一致 |
| 本抄本で手を入れた（データ） | **4** — `repo/eval/golden.yaml`（案件 12 問を追記）＋ `repo/company/` の上流デモ 3 篇（`source_project: upstream-demo` を追記。`kb-policy.md` §2.3）。いずれも規則ではなくデータ |
| 本抄本だけの追加 | **134** = 案件データ 122（`repo/projects/`）＋ 会社条目 6（`repo/company/`：5 篇＋`templates/`）＋ 説明 6（`VENDORED.md` / `UPSTREAM-SYNC.md` / `company-README.md` / `projects-README.md` / `kb-policy.md` / `VENDOR_BASE.json`）。本地拡張層は `tools/kb_local/`（`tools/` 側）なのでここには入らない |

確認コマンド:

```bash
py -3 -m tools.kb_vendor_manifest --check
# → 上流由来 23 件: 一致=19 本地改変=4（うちコード 0） 消失=0
```

> **データの改変 4 件は、同期のたびに手で当て直す必要がある。** 当て方は
> `repo/eval/golden.yaml` は「上流 24 問を残したまま後ろに案件 12 問を足す」、
> 上流デモ 3 篇は「front matter に `source_project: upstream-demo` を 1 行足す」。

**コード側の本地改変は 0 である。** 次に上流の新版が来たら、`kbkit/` と `run.py` は
「フォルダを丸ごと差し替える」だけで済む。

---

## 1. 三本の線を混ぜない

同期が壊れるのは、たいてい「どれが上流の物で、どれが我々の物か」が曖昧なときである。
線を 3 本に分け、**線ごとに違う扱い**をする。

| 線 | 場所 | 上流との関係 | 同期のしかた |
|---|---|---|---|
| **コード線** | `kbkit/` `run.py` `api.py` | 上流が正。**逐字一致を保つ** | 上流の新版で**丸ごと差し替える**。我々の差分は `tools/kb_local/` にあり、ここには無い |
| **会社線** | `repo/company/` | 我々の成果 | 同期では触らない。社外へ渡すのは会社の指示があったときだけ（§4） |
| **案件線** | `repo/projects/` | 我々の成果。**上流へ出さない** | 同期では触らない。**永久に出さない** |

**この 3 本を混ぜた瞬間に同期は手作業になる。** コードに案件固有の分岐を書かない、
案件データを `company/` に置かない、が守るべき全部である。

---

## 2. 上流が更新されたときの手順（5 ステップ）

```bash
# 0) 出発点を汚さない。いまの状態で回帰を取る（§2.1 の基準値と一致するはず）
py -3 -m tools.kb_local lint
py -3 -m tools.kb_local eval --all
py -3 -m tools.kb_eval
py -3 -m tools.kb_eval --with-module
py -3 -m tools.rag eval

# 1) 上流の新しい版を置く（D:\AI_platform は直接編集しない。読むだけ）
py -3 -m tools.kb_vendor_manifest --check      # 「上流そのものが N 件動いています」を見る

# 2) 上流のコードを丸ごと差し替える（当て直すファイルは 0 本）
#    ただしデータ 4 件は当て直す:
#      repo/eval/golden.yaml                      … 「上流の 24 問 ＋ こちらの 12 問」に戻す
#      repo/company/{glossary/terms,patterns/screen/list-search,standards/coding/general}.md
#                                                 … front matter に source_project: upstream-demo を 1 行戻す
cp -r "/d/AI_platform/kb-platform/kbkit" tools/kb-platform/
cp "/d/AI_platform/kb-platform/run.py" tools/kb-platform/

# 3) 指紋を取り直す
py -3 -m tools.kb_vendor_manifest --snapshot

# 4) 回帰。数値が動いたら、動いた理由を説明できるまで次へ進まない
py -3 -m tools.kb_local lint
py -3 -m tools.kb_local ingest --prune          # 上流 CLI へ委譲（差分取り込み）
py -3 -m tools.kb_local eval --all
py -3 -m tools.kb_eval
py -3 -m tools.kb_eval --with-module
py -3 -m tools.rag eval

# 5) 同期記録を §5 に 1 行足す
```

**手で当て直すファイルは 0 本である。** 数値が動いたときだけ `tools/kb_local/` を見る
（`_bootstrap.py` が上流の `_load_candidates` / `STATUSES` を掴んでいるので、
上流がその名前を変えたら**そこで例外が出る**——黙って壊れない）。

### 2.1 回帰の基準値（2026-10-29 時点。同期のたびにここへ追記する）

| 指標 | 値 | 意味 |
|---|---|---|
| `tools.kb_local lint` | `OK 91 文書` | 形（front matter・scope・doc_type） |
| `tools.kb_local eval --all` | `recall@5=1.000  MRR=0.958  節recall=0.833 (12 件)` | 上流 demo 24 問。**下がったら同期で壊した** |
| `tools.kb_eval`（KPI⑥）— ヒントなし | `recall@5=0.863  MRR=0.672  top1_module=76/80` | 80 問を案件知識に対して。**これが本来の指標** |
| `tools.kb_eval --with-module` | `recall@5=0.925  MRR=0.720  top1_module=80/80` | 呼び出し側がモジュールを知っている場合の上限。**下がったら `tools/kb_local` の module 絞り込みが壊れた** |
| `tools.rag eval` | `filtered 1.000 / 0.901` `unfiltered 0.863 / 0.645` | chunk 単位の回帰尺。**同期では動いてはならない** |

`tools.rag` の数値は**同期と無関係に動かない**はずである（`kbkit/` を通らない）。
ここが動いたら、同步のつもりが chunk データを触っている。

---

## 3. 本地拡張層 `tools/kb_local/` の意味（上流を変えずに済ませる方法）

上流には無いが我々に要るものが 3 つある。**どれも上流のファイルを書き換えずに足した。**

| 要るもの | 上流の状態 | この層での足し方 |
|---|---|---|
| 骨架の状態機の語彙（`open` / `baselined` / `changed` / `done`） | `search` は `status = 'active'` 固定、`lint` は `draft/review/active/deprecated` のみ | `_bootstrap.patched_candidates()` が `retrieval._load_candidates` を、`wider_statuses()` が `pipeline.STATUSES` を、**呼び出しの間だけ**差し替える |
| モジュール絞り込み（`--module`）とスコープ絞り込み（`--scope`） | 引数が無い | 差し替えた `_load_candidates` が WHERE 句に押し込む（上流の鉄則どおり後掛けしない） |
| 節レベルの評価（`expect_heading`） | doc 単位の的中しか見ない | `evaluation.py` が `expect_heading` を持つケースだけ見出しまで判定し、`節recall` を出す |

**並び替え（dense+sparse → RRF → rerank）は上流の 1 本をそのまま呼ぶ。複製していない。**
だから上流が検索品質を上げれば、我々の数字も自動で上がる。

**上流 CLI との関係**（使い分けを間違えると「壊れた」と誤解する）:

| したいこと | 使うコマンド | 上流 CLI を直接叩くと |
|---|---|---|
| 検索 | `py -3 -m tools.kb_local search …` | **0 件**（我々の文書は `active` でないため） |
| lint | `py -3 -m tools.kb_local lint` | **`NG 79 件の問題`**（`open`/`baselined` を知らないため） |
| 評価 | `py -3 -m tools.kb_local eval --all` | **`recall@5=0.500`**（上流 demo 12 問は `active` なので当たる。案件 12 問が全落ち） |
| 取り込み・索引状態 | 上流 `run.py ingest` / `stats` でも可（この層も委譲している） | 問題なし |

上流のデータに手を入れたのは 4 件だけである（§0 の表）。
- `repo/eval/golden.yaml` … 上流 24 問 ＋ 案件 12 問。同期のときは「24 問を残したまま後ろに足す」
- `repo/company/` の上流デモ 3 篇 … `source_project: upstream-demo` を 1 行足しただけ（`kb-policy.md` §2.3）

いずれも**規則ではなくデータ**であり、同期のときに当て直す箇所はこの 4 つに限られる。

---

## 4. 逆方向 — 成熟した案件知識を全社へ（社命が来たとき）

**最初に断っておくべきこと**: **案件の知識は、そのままでは全社に出せない。**
`repo/projects/P-R60-001/` は顧客案件の資産であり、表名・項目名・業務定数・画面仕様を含む。
全社展開の対象になるのは、**そこから抽出した「方法」だけ**である。
つまり `company/` へ昇格させた条目であり、案件そのものではない。

**また、これは上流のコードや実装規則を変える話ではない。** 渡すのは条目（知識）だけで、
渡し方は会社の指示に従う（我々が `D:\AI_platform` へ直接 commit しない）。

### 4.1 昇格の判据（`company-README.md` §1 と同じ）

**「別の顧客・別のシステムへ持って行っても成立するか。」**

| 上げてよい | 上げてはいけない |
|---|---|
| A/B/C の判定手順、出典等級 E1〜E4 の判定、受控回流の運用 | とある案件で A だった項目の中身 |
| テスト比率 正常3/境界2/異常3、追跡の閉じ方 | とある案件の TC 一覧 |
| 審査観点の索引と使い方 | QA 票の実物、指摘の原文 |
| 「二重化する」という方法 | どのファイルを二重化したか |

### 4.2 昇格の手順

1. **実績を待つ。** 複数案件で使われた（少なくとも 1 案件で「これで詰まらなかった」）条目だけ上げる。
   1 案件でしか使っていないものは、まだ方法ではなく偶然である。
2. **匿名化する。** 表名・関数名・行番号・顧客名・実データ値を落とす。
   落とすと意味が消える条目は、上げない（＝まだ案件事実である）。
3. **要約＋正本ポインタの形にする。** 同じ定義を 2 箇所に書かない。冒頭に
   「本条は要約であり、正本は 〜」を置き、食い違ったら正本を採ると明記する（`company-README.md` §3）。
4. **1 条目＝1 件。** 受け取り側が条目ごとに採否を判断できるようにする。
5. **採られたら、こちらも合わせる。** 受け取り側が文言を直したら、こちらの写しも直す。
   **受け取り側が正**である（写しを正にしてはいけない）。

### 4.3 上げる前に必ず通すもの

- `py -3 -m tools.trace_check --strict --only-check secrets`（`CLAUDE.md` 紅线⑦）。
  **外部へ出るものは全部**。必要なら `tools/masking/mask_demo.py` で占位化してから出す。
- `py -3 -m tools.kb_local lint` — `scope: company` に `project_id` が無いこと、
  `doc_type` が語彙内であること。
- **顧客名を入れたまま上げない。** 内部資料に書くのは可、対外へは不可
  （`.claude/rules/01-security-redlines.md` 補足）。

---

## 5. 同期記録（1 回 1 行。消さない）

| 日付 | 上流の状態 | 動いたファイル | 手当てした本地改変 | 回帰 lint / eval / kb_eval / rag |
|---|---|---|---|---|
| 2026-10-29 | 初回取り込み（`VENDOR_BASE.json` 作成時点） | — | コード 4 本を直接書き換えていた | `OK 91` / `1.000・0.958・0.833` / `0.863・0.672` / `1.000・0.901` |
| 2026-10-29 | 同上（変更なし） | — | **`tools/kb_local/` へ移設し、上流 4 本を逐字へ復元（コード改変 0）** | 上と同じ値（逐字一致。`kb_eval --with-module` も `0.925・0.720` で不変） |

---

## 6. 上流を git にしてもらう（**上申しない**）

git 化されれば同期は楽になるが、**それは上流の持ち物の決め事であり、我々から求める話ではない**
（2026-10-29 ユーザー指示：上流の実装規則は我々の都合で変えない）。
上流が git になった場合は、こちらは次の 1 行で差分を見られる、というだけである。

```bash
git -C <上流のクローン> fetch && git -C <上流のクローン> log --oneline HEAD..origin/main
```

git 化されるまでの間は §2 の手順で回す。**指紋（`VENDOR_BASE.json`）は必ず更新してから commit する**
（更新を忘れると、次の `--check` が「上流が動いた」と「こちらが壊した」を区別できなくなる）。

---

## 7. やってはいけないこと

- **`D:\AI_platform` を直接編集する。** あれは上流であり、他の人の持ち物である。
- **上流のコードを書き換えて差分を作る。** 我々の差分は `tools/kb_local/` に置く。
  上流の `kbkit/` `run.py` `api.py` は逐字のまま（`--check` のコード改変 0 が合格条件）。
- **上流の実装規則を変える提案・commit をする。** 上流のルールは上流が決める。
- **`repo/projects/` の内容を上流へ上げる。** 顧客案件の資産である（§4 冒頭）。
- **上流のコードに案件固有の分岐を書く。** `if project == "P-R60-001"` を `kbkit/` に入れない。
  案件差は**データ**（`repo/projects/`）で表現する。
- **`VENDOR_BASE.json` を更新せずに commit する。** 次回の `--check` が意味を失う。
- **回帰の数値が動いたまま次工程へ進む。** 動いた理由を説明できるまで進めない。

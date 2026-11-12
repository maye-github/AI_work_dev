---
id: KB-POLICY-001
type: policy
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
---

# 知識ベース運用方針（構築ガイド STEP 0 の成果物）

> **本文件は「規則」だけを書く。手順は `知识库使用手顺.md`。**
> `repo/` の外に置くのは、索引されると目次頁が答えの席を奪うため（`company-README.md` 冒頭の実測）。

---

## 1. 機密区分（`conf_level`）

| ガイド | 実装値 | 意味 | 例 |
|---|---|---|---|
| 1 = public | `10` | 公開可 | 公開規格の要約 |
| 2 = internal | `20` | 社内限定 | 社内規約、設計パターン、テンプレート |
| 3 = confidential | `30` | 案件限り | 案件の設計書・ソース・QA 票 |
| 4 = client_only | `40` | **外へ出せない** | 顧客固有の画面文言、顧客提供の実データ仕様 |

- **既定は `30`**。会社級（`scope: company`）は `20` 以下しか置けない。
- `client_only` は「見せる相手」ではなく「**外へ出せない**」印（`01-security-redlines.md` の L3 と同じ）。
- **止め方は 2 つ**。片方だけでは足りない。

| 経路 | 止めるもの | コマンド |
|---|---|---|
| 検索 → 資料へ貼る | 検索結果に L40 を出さない | `search --for-external`（権限 40 でも 30 に落とす） |
| 人がコピーして貼る | 対外ファイルに L40 本文が入っていないか | `external-check <file>`（20 文字以上の一致） |

---

## 2. 何を入れるか（**先に「入れないもの」を決める**）

### 2.1 入れないもの（除外基準・これが先）

| 入れないもの | 理由 |
|---|---|
| 未匿名化の顧客名・個人名・メール | 一度入ると消しにくい。入口で止める |
| 見積金額・工数実績・契約条件 | 知識ではなく営業情報 |
| 接続情報（ユーザ・ホスト・SID・鍵） | 13 類の機密。gate6 で落ちる |
| 本番データの実値 | 占位（`COL_1` / `VAL_1`）に置換してから |
| 議事録の生ログ（発言者名つき） | 要約して発言者を落とす |
| 顧客受領資料の原文 | `docs/01_context/incoming/` に置く。KB は要約と所見だけ |
| 未承認の設計（`draft`） | 既定の可检索状態に `draft` は入っていない |

### 2.2 入れるもの

| 種別 | 中身 | 置き場所 | 既定 `conf_level` |
|---|---|---|---|
| 会社級 | 規約・パターン・用語・テンプレート | `repo/company/` | `20` |
| 案件級 | 要件・設計・試験・ADR・案件用語 | `repo/projects/<P-ID>/` | `30` |

**★ 方法の「正本」も会社級に置いてよい（2026-11-06 統合）。**
以前は「正本は `docs/90_knowledge/`、ここには要約だけ」という二重構造だったが、
知識庫を 2 つに分けないため **`docs/90_knowledge/` の 17 篇を `repo/company/`・`repo/projects/` へ移設**した。
- 移設した正本は `source_project: framework-rules` を持つ（`company-README.md` の表に追記）。
- **要約条目（`STD-REQ-ABC-001` 等）は正本を指す**。本文に定義を書き直さない（§3.4 の規約はそのまま）。
- 旧パスは `docs/90_knowledge/README.md` に移設表として残す。**そこへ文書を戻さない。**

### 2.3 `source_project` の値（**会社級のみ**）

案件級は `project_id` が出処そのものなので**書かない**（二重管理になる）。

| 値 | 意味 |
|---|---|
| `P-<案件>-<番号>` | 実在の案件から昇格した |
| `upstream-demo` | 上流 kb-platform 同梱のデモ文書 |
| `framework-rules` | `.claude/rules/` 等から整理した条目（案件の沈殿ではない） |

**空欄は「出所が無い」ではなく「まだ書いていない」。** 検査は `kb_local extra report`。

### 2.4 規則の真源台帳（**2026-11-06 追加・不一致の再発防止**）

**同じ規則域に、二つ以上の文書が「正本」を名乗ってはならない。**
要約（summary）は必ず `正本は …` の一文を持つ。**食い違ったら正本を採る。**

| 規則域 | 唯一の正本 | KB の条目 | 条目側の扱い |
|---|---|---|---|
| 未確定事項の A／B／C | `.claude/rules/02-requirements.md` §4.1 | `STD-REQ-ABC-001` | 摘要（正本を指す） |
| 出典等級 E1〜E4 | `.claude/rules/02` §4.1／`STD-REQ-ANSWER-001` §3 | `STD-REQ-EVID-001` | 摘要 |
| 技術選型は B（A にしない） | `.claude/rules/02` §4.1 | — | — |
| 命名・snake/camel 分区 | `.claude/rules/03-design-coding.md` §4 | `STD-CODING-001` | 摘要（接口層は適用外） |
| SQL 白名单 | `.claude/rules/03` §5 | — | — |
| TC 比率 正常3/境界2/異常3 | `.claude/rules/04-testing.md` §2 | `STD-TEST-RATIO-001` | 摘要 |
| 成果物の二重化・受控回流 | `.claude/rules/00-project-global.md` §11〜§12 | `PAT-DELIVERY-002`（正本）／`PAT-DELIVERY-001`（摘要） | — |
| 基本設計書の節構成 | `TPL-DESIGN-REF-001` | `TPL-DESIGN-BASIC-001` | 簡略版（**節数は REF を採る**） |
| 機械可読の方法文書 | 各文書自身 | `canonical: true` の `STD-*`（7 件） | **正本**（摘要ではない） |

- **`canonical: true`** は「この条目は要約ではなく正本である」の印。付いた `STD-*` は
  規則の摘要扱いをせず、`kb_refs` に**先例として引用してよい**（作業票の「STD-* は書かない」の例外）。
- 現在の canonical: `STD-REQ-ANSWER-001`・`STD-PLATFORM-001`・`STD-PLATFORM-4L-001`・
  `STD-PPT-DEVIATION-001`・`STD-PPT-COVERAGE-001`・`STD-INT-HARMONY-001`・`STD-INT-SDS2-001`。
- `tools/kb_refs.py` の `_is_rule_summary()` は **`canonical: true` を読む**（2026-11-06 是正）。
  したがって `--strict` でも方法の正本は「摘要」と誤判定されない。
- `--strict` は**要約（canonical でない `STD-*`）を不合格にする追加の厳格モード**である。
  通常の承認ゲート（非 strict）は、規約を「遵守の記録」として受理する。

### 2.5 節点の必読条目（2026-11-09 追加・「每节点都参考同一个 KB」の実装）

**「先例を引いてください」では引かれない。** 節点ごとに**必読の doc_id** を決め、
作業票（`nodes/nNN-*.md` §1.5）と `tools/kb_refs.NODE_REQUIRED` の**両方**に同じ表を置く。
承認前は `py -3 -m tools.kb_refs check <承認版> --node N --require-node` で機械検査する。

| 節点 | 必読 doc_id | 何のために |
|---|---|---|
| 1 要件理解 | `PAT-REVIEW-LENS-001`／`PAT-REVIEW-CAP-001`／`PAT-DEV-PLAYBOOK-001` | 52 の観点で要求書を審査／審査能力の分解／工程①の入出力 |
| 2 基本設計 | `TPL-DESIGN-REF-001`／`TPL-DESIGN-BASIC-001`／`PAT-SCREEN-001` | 14 節の骨格／簡略テンプレート／一覧検索の標準 |
| 3 詳細設計 | `TPL-DESIGN-DETAIL-001`／`STD-CODING-001` | D/L/SQL/E/境界値／命名分区・SQL 白名单 |
| 4 框架 | `TPL-DESIGN-DETAIL-001`／`STD-CODING-001`／`PAT-DEV-PLAYBOOK-001` | 実装可能粒度／技術規約／工程④ |
| 5 製造 | `STD-CODING-001`／`PAT-DEV-PLAYBOOK-001`／`TPL-DESIGN-DETAIL-001` | 実装細則／工程⑤の検査点／設計粒度 |
| 6 単体テスト | `STD-TEST-RATIO-001`／`PAT-DEV-PLAYBOOK-001` | 正常3/境界2/異常3・design_ids／工程⑥ |
| 7 結合テスト | `PAT-DEV-PLAYBOOK-001`／`PAT-DEV-WALKTHROUGH-001` | 工程⑦／端到端の実走例 |
| 8 リリース | `PAT-DELIVERY-001`／`PAT-DEV-PLAYBOOK-001` | 成果物の二重化／工程⑧ |

- **規則との階層（衝突の解消）**：`.claude/rules/` は**条文の唯一真源**（常時ロード）。
  KB の `STD-*` のうち要約条目は**条文を指す**だけであり、**必読条目には要約を選ばない**
  （`STD-TEST-RATIO-001` のみ例外＝他に該当条目が無いため）。
- **表の唯一真源は `tools/kb-platform/node-map.yaml`**。`tools.kb_refs.NODE_REQUIRED` はこれを読む。
  作業票（`nodes/nNN-*.md` §1.5）と `kb-policy` の表は**その写し**であり、**片方だけ変えない**（NFR-1）。
- **遡及**：2026-11-09 より前に承認された文書には適用しない（当時その条目が無かった）。

### 2.6 `knowledge/` の条目の型（2026-11-09 追加）

**AI が `sources/` から作る案件知識は、決められた型で書く。**
型が無いと「AI が何を根拠に何を書いたか」を機械でも人でも確かめられない。

- 雛形（**唯一真源**）: `tools/kb-platform/knowledge-template.md`
- 型: front matter（`doc_id` / `scope` / `project_id` / `title` / `doc_type` /
  `conf_level` / `status` / `updated_at` / **`source_files`**）＋ 本文 5 節
  （`結論` / `根拠` / `適用範囲` / `未確定` / `更新条件`）。
- **`source_files` の無い知識は作らない**（紅線⑤「出典なきテストケース禁止」と同じ思想）。
  原本に無いことは `## 未確定` に置く。**推測で埋めない。**
- 検査: `py -3 -m tools.kb_local check-knowledge`（4 点だけ見る。内容の正しさは人が読む）。
- 遡及免除: `tools/kb-platform/knowledge_exempt.txt`（理由を書いて 1 行。新規は免除不可）。

---

## 3. 誰が更新・削除できるか（`owners.yaml` が正本）

### 3.1 権限モデル

| 範囲 | 更新・削除できる人 | 備考 |
|---|---|---|
| 会社級 `repo/company/**` | 会社の責任者（＋代理） | `company.owner` |
| 案件級 `repo/projects/<P>/**` | その案件の PM | `projects.<P>.owner` |
| 結案済み（`CLOSED.md` あり） | **誰もできない** | 読み取り専用 |
| `owners.yaml` 自身 | 会社の責任者のみ | |

**`null` は「制限なし」ではなく「未任命（凍結）」。** 空欄の範囲は誰も更新できない。

### 3.2 読権限（`--as`）

| 誰 | 会社級 | 案件級 |
|---|---|---|
| 会社の責任者・代理 | 見える | **全案件** |
| 案件の `owner` / `members` | 見える | **その案件だけ** |
| それ以外 | 見える | **見えない** |

- **既定は拒否**。身元が無ければ**会社級だけ**を返す。
- 身元の解決順：**`--as` → `whoami.txt`（端末に 1 回だけ設定）→ 無し**。
  `whoami` は人が明示的に設定する操作であり、これで制限が緩むわけではない。
- 身元が無いのに `--project` を指定したら**エラーで止まる**（黙って空を返すと誤解される）。
- `--all` は管理者用の明示的な逃げ道。

> **★ これは検索範囲の制御であり、ファイルアクセス制御ではない。**
> 案件フォルダを直接開ける人は中身を見られる（`kb_acl` も同じで、事前の錠ではなく提出前の点検）。
> 機密性が要るなら、案件ごとにアクセスできる場所へ置くこと——それはファイルシステム側の仕事である。

### 3.3 二層で止める

| 層 | 何を止めるか | 実体 |
|---|---|---|
| ツール層 | 変更を**検出して落とす** | `tools.kb_acl check --by <人> --from-git` |
| Git 層 | マージを**止める** | `CODEOWNERS` ＋ ブランチ保護 |

ツールだけでは故意の直接編集を防げない。Git だけでは「誰がやったか」が残らない。**両方そろえる。**

### 3.4 責任人の現状

`owners.yaml` に記入済み（会社級・案件級とも）。**未記入の範囲は凍結**される。

---

## 4. 昇格の手順（ガイド STEP 12）

> **何を上げてよいかの判定は `promotion-criteria.md`（5 項チェック）が唯一の入口。**

### 4.1 流れ

```bash
py -3 -m tools.kb_promote candidates --project <P> --types template,glossary,standard
py -3 -m tools.kb_promote check <file>          # 匿名化体检（0 件になるまで直す）
py -3 -m tools.kb_promote plan  --from-plan plan.yaml     # 検証だけ
py -3 -m tools.kb_promote apply --from-plan plan.yaml --by <人> --apply
py -3 -m tools.kb_local ingest --prune
py -3 -m tools.kb_promote close --project <P> --apply
```

**`plan` で 1 件でも不備があれば 1 件も動かない。**

**移送（`apply`）と結案（`close`）は、書き込みの直前に `kb_acl` で権限を検査する。**
移送先は通常 `company/` なので**会社の責任者だけ**が実行でき、結案は**その案件の PM だけ**。
予演（`--apply` を付けない実行）でも同じ検査が走る——予演が通ってから本番で弾かれると、
何が悪いのか分からないため。

### 4.2 一括計画 YAML

```yaml
promotions:
  - file: projects/P-XXX-001/standards/foo.md   # repo/ からの相対
    to: standards/requirements                   # company/ からの相対
    doc_id: STD-REQ-FOO-001                      # 省略時は自動採番
    source_project: P-XXX-001                    # 省略時は --source-project
```

`doc_id` は**リポジトリ全体で一意**（バッチ内の重複も弾く）。

### 4.3 結案記録（`CLOSED.md`）

`close --apply` が書く。中身は 3 つ：

1. **人が確認する 4 項**（結案評議会・候補抽出・匿名化・KB 責任人承認）— 空欄で出す
2. **機械がやった 4 項**（移送・`scope` 変更・`source_project` 記録・読み取り専用の印）— 実績件数つき
3. 昇格した条目と残件数

**読み取り専用は OS 権限ではなく「印」。** 再開するときは削除せず、理由と日付を追記する。

---

## 5. 昇格のトリガー

ガイドは「案件結案時」だが、本骨架は **「2 案件目で使われたとき」** を推奨する。
1 案件で「通用する」と思ったものが 2 案件目で通用しないことは多い。
使われた実績が無いまま上げると、会社級が「各案件の置き場」になる。

---

## 6. 何を昇格するか（3 種類）

### 6.1 雛形（顧客へ出した成果物のテンプレート）

```bash
py -3 -m tools.kb_promote skeleton <成品.md> --out <模板.md> --source-project <P>
```

| 残す | 置き換える |
|---|---|
| 見出し・表の見出し行・リスト記号・コードフェンスの言語 | 段落・表の本体・コードの中身 → `<…>` |

**見出しは残す。** 案件名が入っていれば `check` が拾う。機械が見出しを書き換えると意味が変わる危険のほうが大きい。

### 6.2 用語

雛形は `repo/company/templates/glossary.md`（`TPL-GLOSSARY-001`）。
案件では `init-glossary --project <P> --by <PM> --apply` で起こし、`status: open`（可检索）で使う。
結案時に「2 案件目でも通じる語」だけを会社級へ上げる。

### 6.3 規約

`doc_type: standard`。`candidates --types standard` で候補が出る。

### 6.4 匿名化の下書き（`draft`）

```bash
py -3 -m tools.kb_promote draft <対象.md>
```

1. 置換表 `tools/kb_local/promote_map.txt`（`元 => 先`）に従って置き換える
2. 置き換えられなかった語を「未対応」として標準出力に並べる
3. **原本は書き換えない。** 出力は `reports/promote-drafts/<name>.anon.md`

**表に無い語は置き換えない。** 機械が同義語を推測すると業務の意味が変わる。
下書きを `repo/` の中に置くと索引され、原本と二重にヒットする（必ず外に置く）。

### 6.5 遮蔽語リスト（`promote_denylist.txt`）

`check` が使う。**1 行 1 語、`#` で区分を切り替える。**

```text
# 顧客名
〈客先の呼び方〉
# 人名
〈実名〉
# 案件名
R60
```

- 置き場所 `tools/kb_local/promote_denylist.txt`（gitignore 済）
- **顧客名は自動で拾えない**（本文に出てこないことが多い）。人が書く
- 人名・案件名は `denylist --project <P>` で候補を自動生成できる（人が不要分を消す）

**検出区分は 3 つ**：`顧客名` / `人名` / `案件名`。加えて機械が形から拾う
`案件接頭辞つき識別子`（`R60Area`）・`案件ID`・`ファイル:行` 参照。**どれも 0 件になるまで昇格できない。**

---

## 7. 節点産出の先例参照（`kb_refs`）

### 7.1 何を書くか（**2 種類ある。意味が違う**）

| 種別 | 中身 | 何のために書くか |
|---|---|---|
| **先例** | 案件の事実（`r60-001-screens-*`）・`TPL-*`・`PAT-*` | **照らし合わせる対象**。これが無いと「何を根拠にしたか」が辿れない |
| **規約** | `STD-*`（`company/standards/`） | **遵守の記録**。どの規約に従ったかを残す（新情報ではない） |

- どちらも `kb_refs` に書いてよい。**検査は 2 種を区別して並べるだけで、合否には使わない。**
- **設計書を作るときは必ずテンプレート（`TPL-*`）を引く**——`company/templates/` は
  「顧客に出す成果物の骨格」であり、これが先例の中心になる。
- **規約は `.claude/rules/` が常時読み込むので、引用しても情報は増えない。**
  それでも書くのは「どの規約に従ったか」を残すためである（監査のためであって、知識のためではない）。

### 7.2 節点ごとに引く範囲

| 節点 | 引く範囲 |
|---|---|
| 1 要件理解 | `company/patterns/review`・`projects/<P>/glossary` |
| 2 基本設計 | `company/patterns/screen`・`projects/<P>/screens` |
| 3 詳細設計 | `projects/<P>/modules`・`projects/<P>/standards` |
| 4 框架構築 | `company/standards/coding`・`company/templates` |
| 5 製造 | `projects/<P>/standards`・`company/standards/coding` |
| 6 単体テスト | `company/standards/testing`・`projects/<P>/review` |
| 7 結合テスト | `projects/<P>/modules`・`projects/<P>/screens` |
| 8 リリース | `company/patterns/delivery`・`projects/<P>/glossary` |

**いずれか 1 件でも当たれば合格。** 先例が無い場合は `kb_refs: []` とし、
`open_questions` に「先例なし」と理由を書く（空欄で放置しない）。

### 7.3 使い方

```bash
py -3 -m tools.kb_refs show --node 3
py -3 -m tools.kb_refs suggest --project <P> --as <人> --query "<主題>"
py -3 -m tools.kb_refs check <承認版> --node 3
py -3 -m tools.kb_refs scan                 # 演習＋実戦をまとめて
py -3 -m tools.kb_refs cited <doc_id>       # 逆引き：この知識を引用した成果物
py -3 -m tools.kb_refs cited --zero         # 一度も引用されていない条目
```

**`scan` が対象にするもの：**

| 区分 | 対象 | 節点の決め方 |
|---|---|---|
| 演習 | `**/05_承認版_*.md` | ディレクトリ名 `节点N_` |
| **実戦** | `docs/<NN>_<工程>/` の `.yaml` / `.md` | ディレクトリ名（`10_`→1 … `70_`→8） |

- `*template*` と `front matter の id が TPL-*` のものは**雛形なので対象外**。
- 節点5（製造）は `docs/` に成果物を置かない（コードが成果物）ため対象外。

### 7.4 遡及適用しない文書（`kb_refs_exempt.txt`）

`kb_refs` は 2026-11-03 に導入した。**それ以前の承認版は、参照すべき先例が存在しなかった**
（`company/templates/` は 2026-11-02 以降、案件知識は 2026-10-28 以降）。
遡って引用を書かせると、存在しないものへの参照を後から作ることになり、**記録として嘘になる**。

したがって次で扱う：

| 対象 | 扱い |
|---|---|
| 導入前の承認版 | `tools/kb-platform/kb_refs_exempt.txt` に**理由つきで**載せる。`scan` は「適用外」と表示 |
| 新規の承認版 | **免除できない。** 承認前に `kb_refs check` を通す |

**免除は「静かに飛ばす」ための仕組みではない。** 1 行 1 理由を書き、レビューで外せる形にする。

### 7.5 判定しないこと

**「その先例に沿っているか」は見ない。** 見るのは 3 点だけ：

1. `kb_refs` が書かれているか
2. 引いた ID が実在するか
3. その節点で引くべき範囲を引いているか

**中身の妥当性は人が読む**（紅線③）。「先例を引いた」と言えても「先例に合っている」とは言えない。

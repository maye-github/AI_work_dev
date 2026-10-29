---
name: code-from-design-trans-cosmos-ai
description: "trans-cosmos-ai の設計→製造（design-to-code）パイプラインスキル。承認済みの基本設計（F-ID・I-ID）と詳細設計（D-ID・L-ID・E-ID）から製造コードを生成し、R/F/I/D/L/E/TC のトレーサビリティを ids.yml 単一ソース配下で確保する。`build_mode: migration`（既存システム・旧設計書を持つ案件）では既存の共通部品を唯一真源として呼び出し、並行新版の作成を禁止する。`greenfield`（既定）では共通部品を本案件で新規定義する。案件固有の値（共通部品一覧・操作 ID・SQL テンプレート・貫通例）は知識庫 `tools/kb-platform/repo/projects/<P-ID>/` から取る（§0.5）。設計書からコードを起こす・設計と実装の対応を確認する・製造物をレビューするときは必ずこのスキルを使うこと。"
id: SKL-001
type: skill
req_ids: [R-101]
status: baselined
sensitivity: internal
owner: AI-PG
version: 0.2.0
---

# code-from-design-trans-cosmos-ai スキル定義書

## スキル概要

本スキルは、設計情報から製造コードを生成するエンドツーエンドのパイプラインを提供する。
上流 SE が作成した R-ID（要求 ID）をトリガーとし、基本設計 BD、詳細設計 DD、製造（コーディング）の
4 ステップを **Claude Code 自身が** 順に実行する。各工程は `ids.yml` による ID 管理の下で
トレーサビリティを確保し、`trace_check --strict` による閉ループ検証を必須とする。
**交接工程は存在しない**。Claude Code は設計からコード生成・検証までを単独で担い、人間は
レビュー／承認ゲート（要件合意・設計評審・合否判定・リリース判定）を保持する。

**本スキルが持つのは方法だけである。** 案件固有の値（表名・項目名・関数名・SQL 本文・貫通例）は
本スキルに書かない。それは知識庫が持つ（§0.5）。判定基準は
「この一文を、別の顧客の別のシステムへ持って行っても成立するか」——成立しなければ知識庫へ
（`.claude/rules/06-knowledge-flywheel.md` §8）。

---

## 0. 前提：案件形態（`build_mode`）と適用範囲

`build_mode` の宣言場所は `docs/00_plan/coach/<module>/case.yml` の **1 箇所のみ**。
宣言が無ければ **`greenfield`**（從無到有）とみなす。

| 形態 | 既存資産 | 共通部品の扱い | 本スキルの重点 |
|---|---|---|---|
| `greenfield`（既定） | 無い | 工程 04 の承認スタックに沿って**本案件で新規定義**する。定義後の改変禁止はその新規資産に働く | §2.1〜§3.3 の設計→製造の順序と追跡 |
| `migration` | 有る（旧設計書・共通部品） | **既存の共通部品を唯一真源**とし、並行新版の作成・分岐を禁止する（案件プロファイル §2 禁①） | 既存資産との対応付け（§1.2）と既存関数の呼び出し（§2.3） |

**適用条件**
- 対象 R-ID が `docs/00_registry/ids.yml` の R セクションに **事前登録済み**であること（§1.3）。

**適用外（本スキルを使わない）**
1. **要件の構造化（工程 01 要件理解）** — 要件書を要求一覧へ構造化する作業は本スキルの守備範囲外である。
   工程 01 の実行体（`trans-cosmos-ai-node1-requirements`）または教程の節点 1 手順を使う。
2. **`ids.yml` 未登録の R-ID（教学号段など）** — 渡すと **Step 1 で受理拒否**となり、先へ進まない。
   これは仕様であり、回避してはならない（紅线① 野号禁止）。

**逸脱した場合の症状**
- 未登録 R-ID を渡すと Step 1 で受理拒否される。
- 案件知識を読まずに製造すると、既存関数を自作したり、設計に無い項目を足したりする
  （＝禁①違反・紅线②違反）。

---

## 0.5 案件知識の取り方（毎回、最初にこれをする）

**設計→製造を始める前に、対象案件の知識庫を引く。** 引かずに書き始めると、
既存の関数・項目名・SQL を「もっともらしく」作り直す（これが最も多い事故である）。

```bash
# 1. 何が入っているかを見る
py -3 tools/kb-platform/run.py stats --repo tools/kb-platform/repo

# 2. 案件知識を引く（project を必ず指定する）
py -3 tools/kb-platform/run.py search "共通部品 呼び出し順" \
    --repo tools/kb-platform/repo --project P-XXXXXX-001 --top-k 5

# 3. 引いた文書を読む（落点は doc_id で示される）
```

引くべきものと、その置き場：

| 引くもの | 知識庫での置き場 |
|---|---|
| 共通部品の一覧と呼び出し順 | `projects/<P-ID>/standards/` |
| 操作 ID・定数の分類 | `projects/<P-ID>/standards/` |
| 設計→製造の貫通例（ID 実値・SQL・テンプレート） | `projects/<P-ID>/playbooks/` |
| 画面・モジュールの項目定義 | `projects/<P-ID>/screens/`・`modules/<module>/` |
| 方法（本スキル・rules） | 本ファイルと `.claude/rules/`（知識庫ではない） |

**知識庫に無い場合は、作らない。** 人に確認する（紅线③）。推測で埋めた値は設計を汚染し、
後から「設計と実装のどちらが正か」が判別できなくなる。

---

## Step 1: R-ID 受理（要求登録段階）

### 1.1 入力情報の確認

上流工程から引き渡された R-ID の妥当性を検証する。R-ID は `ids.yml` の R セクションに
事前登録されている必要があり、未登録の R-ID は受理しない。R-ID には以下が含まれることを確認する：

- 要求名称、要求概要、機能分類
- 優先度（A/B/C）、想定工数、リリース時期
- 関連する既存機能（画面 ID、API エンドポイント）
- 利害関係者（要求元、承認者）

### 1.2 対象機能と既存実装の対応付け（`migration` では必須）

R-ID が画面ライフサイクルのどこに影響するかを、**既存実装から特定する**。
`greenfield` では既存実装が無いため、本節は「設計した画面のライフサイクルを決める」作業に読み替える。

`migration` での手順：

1. 画面コンポーネントの初期化フック（`onMounted` 等）を読み、**行番号つきで**初期化の順序を書き出す。
2. サービス層のメソッドを列挙し、各メソッドの用途と**操作 ID** の対応を表にする。
3. 上記 2 つを設計書（BD）の入力にする。**コードは設計の入力ではなく、対応付けの証拠である**
   （`.claude/rules/02-requirements.md` §4：回答の出所は顧客の公式文書）。

対応付けの実例（案件固有）は知識庫の `playbooks/<module>-design-to-code.md` §2 を参照する。

### 1.3 ids.yml への事前登録確認

`ids.yml` の F-ID（機能 ID）と I-ID（画面項目 ID）の体系を確認し、R-ID に対応する
F-ID / I-ID が登録済みであることを確かめる。**未登録なら発号してから進む**
（`docs/00_registry/ids.yml` が唯一の口。野号は gate1 で Exit 1）。

- F-ID：1 要求に対して 1 以上の機能。画面構成（一覧＋ダイアログ等）が分かれるなら F も分ける。
- I-ID：画面項目は**データ項目と 1:1** に対応させる。件数を数えて `count` を持つ。

---

## Step 2: 基本設計 BD 生成

### 2.1 ids.yml への F-ID・I-ID 登録

BD 作成の**前に** ID を登録する（後から発番すると溯及が崩れる）。登録する形：

```yaml
F:
  F-xxx:
    r_id: R-xxx
    name: "機能名"
    description: "画面構成（例: 一覧検索画面 + 登録修正ダイアログ）"
    service: <サービス名>
    endpoints:                       # メソッドと 1:1 で並べる
      - "POST /<path>/init"          # <service>.init
      - "POST /<path>/search"        # <service>.search
I:
  I-xxx..I-yyy:
    f_id: F-xxx
    count: <件数>
    note: "<データ項目との対応（1:1）。個別定義は ids.yml を参照>"
```

- **全 I-ID を列挙しない**（56 件を 56 行書くと単一ソースが二重化する）。範囲と件数で表す。
- 野号（飛び番・自作 ID）を作らない。**登録は `ids.yml` への追記のみ**。

### 2.2 bd-template.yaml への埋め込み

登録した F-ID・I-ID を front matter 7 項目に埋め込む：

```yaml
---
id: BD-<機能>-001
type: basic-design
req_ids: [R-xxx]
func_ids: [F-xxx]
if_ids: [I-xxx..I-yyy]   # 範囲表記、個別定義は ids.yml
status: draft
sensitivity: internal
owner: AI-PG
version: 0.1.0
---
```

### 2.3 BD 本体の作成項目

基本設計書には以下を記載する。**案件固有の実値は知識庫の `playbooks/` から引く**。

1. **画面構成**：テンプレート構造（ヘッダー、条件部／結果部、フッター、編集ダイアログ）
2. **画面項目一覧**：検索条件と結果一覧カラム（I-ID と 1:1 で対応させる）
3. **権限制御**：ボタン活性／非活性の条件（権限フラグ × 自工／他工フラグの決定表）
4. **画面遷移**：一覧 → 新規／複製／修正ダイアログ、業務終了
5. **共通部品呼出し**（`migration` のみ）：既存共通部品の**どの関数をどこで呼ぶか**を表にする。
   一覧と**呼び出し順**は知識庫の `standards/<common-parts>.md` が唯一の定義である。
   `greenfield` では本項を「本案件で定義する共通部品の一覧」に読み替え、工程 04 の承認対象にする。

---

## Step 3: 詳細設計 DD

### 3.1 D-ID / L-ID / E-ID の登録

`ids.yml` に D-ID（データモデル）・L-ID（業務ロジック）・E-ID（エラー・イベント）を追加する：

```yaml
D:
  D-xxx:
    f_id: F-xxx
    name: "<データモデル名>"
    description: "<テーブルに対する SELECT/INSERT/UPDATE の物理設計>"
L:
  L-xxx:
    d_id: D-xxx
    name: "<業務名>"
    file: "<実装ファイル>"
    lines: "<開始-終了行>"      # migration のみ（既存実装の対応箇所）
E:
  E-xxx:
    l_id: L-xxx
    error_id: <エラーコード>
    jp: "<メッセージ>"
```

- 1 ロジック = 1 業務の切れ目（検索／編集／削除など）。**排他・被参照・重複は別ロジックに分けず、
  1 つの編集ロジック内の判定として書く**（判定順序が仕様だから）。
- E-ID はロジックに紐づける。正常系のメッセージも E に含める（確認ダイアログ等）。

### 3.2 dd-template.yaml 作成

```yaml
---
id: DD-<機能>-001
type: detail-design
req_ids: [R-xxx]
logic_ids: [L-xxx, L-yyy]
data_ids: [D-xxx]
error_ids: [E-xxx, ...]
status: draft
sensitivity: internal
owner: AI-PG
version: 0.1.0
---
```

### 3.3 SQL の書き方（方法）

- **動的ソートは白名单**にする（`ALLOWED_SORT_FIELDS`）。白名单外・未指定は固定ソートへフォールバックし、
  末尾に `ROWID` を付けて一意化する（`.claude/rules/03-design-coding.md` §5）。
- **値は必ずプレースホルダで束縛**する（`:param`）。f-string で値を埋め込まない。
- ページングは原則 `ROWID` 方式。`OFFSET/FETCH` は必要な場合の例外として**理由を設計書に書く**。
- 総件数取得と明細取得は**同じ WHERE 条件**で書く（条件の二重管理を避ける）。
- **案件固有の SQL 本文**（表名・列名・DB 関数）は知識庫の `playbooks/` から引く。本スキルには書かない。

---

## Step 4: 製造（コーディング）実行

**本ステップは Claude Code 自身が実行する。外部ツールへの交接は行わない。**

### 4.1 CLAUDE.md と禁止事項の再確認

製造開始前に `CLAUDE.md` および `.claude/rules/` を読み込み、7 条紅线・禁止事項・
commit メッセージ 7 様式を再確認する。`migration` では特に次を守る：

- 禁①：既存共通部品（案件プロファイル §2 が指定するファイル）の手改変禁止・並行新版の作成禁止
- 禁②：`BaseCamelModel` の 4 行 `model_config` 改変禁止（`alias_generator` / `populate_by_name` /
  `serialize_by_alias` / `extra`）
- 禁③：`ids.yml` 未登録の野号（飛び番・自作 ID）禁止
- 禁④：`trace_check --strict` スキップ禁止
- 禁⑤：マスクされていない機密情報を外部 LLM へ送らない（`tools/masking/mask_demo.py` を経由）

`greenfield` では ①② の対象が存在しない。代わりに、工程 04 で**人が承認した採用スタック**を
無断で置換しないこと（紅线④）。

### 4.2 ids.yml の読込みと D-ID 払出し

対象の R-ID → F-ID → I-ID → L-ID/E-ID を `ids.yml` から読出し、D-ID（製造 ID）を払い出す。
D-ID は**製造単位の最小単位**であり、1 エンドポイント群 = 1 D-ID を目安にする。

```yaml
D:
  D-xxx:
    f_id: F-xxx
    target: "<対象テーブルと操作>"
    branch: "feature/D-xxx-<短い説明>"
```

### 4.3 ブランチ運用

標準は 7 種（`.claude/rules/05-commit-messages.md` §7 と併せて読む）：

| ブランチ | 用途 | 命名 |
|---|---|---|
| `main` | リリース済安定版 | `main` |
| `develop` | 統合開発ベース | `develop` |
| `feature/R-ID` | 要求単位 | `feature/R-101` |
| `feature/F-ID` | 機能単位 | `feature/F-042` |
| `feature/D-ID` | 製造単位（最小） | `feature/D-043` |
| `hotfix/YYYYMMDD-事象番号` | 緊急障害対応 | `hotfix/20261008-001` |
| `release/vX.Y.Z` | リリース準備 | `release/v0.1.0` |

製造は `feature/D-xxx-<説明>` を作成し、そのブランチ上で実装する。

### 4.4 製造指示テンプレート

以下の自然言語テンプレートを入力として、**設計文書を正として**実装を進める：

> **【製造指示 / D-xxx】**
> 対象: `<ファイル>` の `<エンドポイント群>`。
> 入力とする設計: `L-xxx` / `L-yyy`（と `D-xxx`）を正とする。
> 準拠する既存資産（`migration`）: `<サービス>` のメソッド、`<画面>` の初期化パターン、
> および知識庫 `standards/<common-parts>.md` の関数マッピング表。
> 実装スタック: `<採用スタック>`。`BaseCamelModel` の 4 行 `model_config` は改変しない。
> 遵守事項: 禁止事項を厳守。既存共通部品を改変せず、既存関数をそのまま呼び出す。
> SQL は `playbooks/` のテンプレートに準拠し、値はプレースホルダで束縛する。
> 完了条件: 実装後に §4.5 のトレース検証を実行し `Exit 0` を確認する。

実装は**設計と既存パターンの写像**として行う。設計に無い独自ロジックの追加や野号 ID の混入を行わない。
設計に誤りを見つけたら**勝手に直さず停止して報告する**（変更は上流から。`rules/02` §6.3）。

### 4.5 trace_check --strict による閉ループ検証

実装完了後、Claude Code 自身が必ず以下を実行する：

```
py -3 -m tools.trace_check --strict --report reports/trace_<R-ID>.json
```

検証項目：

- R-ID から D-ID までが途切れなくつながっている（`chain_complete=true`、`orphan_ids=[]`）
- 各 commit メッセージに正しい D-ID / F-ID / R-ID が入っている
- `ids.yml` にない野号が出現していない
- 既存共通部品・`BaseCamelModel` 4 行 config の改変がない（`migration`）
- 機密情報の外投がない（mask 通過済み）

検証が `Exit 0` にならない場合は製造工程を完了とみなさず、人間のレビューを求めない。

---

以上、4 ステップを Claude Code 自身が実行し、SKL-001 を完了とする。
各工程の出口で人間がレビュー／承認ゲート（要件合意・設計評審・合否判定・リリース判定）を保持する。

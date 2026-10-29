---
name: legacy-case-navigator
description: "歴史案件（レガシー案件）の知識庫ナビゲータ。読み取り専用の実案件リポジトリを**絶対に変更せず**、既に構築済みの知識庫 tools/kb-platform/repo/projects/<P-ID>/ を引いて、画面カード・API 契約・DB 定義・規約・追跡台帳・差異登記簿を即答する。『〈案件〉の〈画面名〉を調べたい』『この画面の設計書はどこ』『この画面はどう作られているか』『共通部品の関数は何がある』『あの画面を重做するための情報が欲しい』『知識庫を見せて』『別の画面のカードを書きたい』『歴史案件を新しく学びたい』と言われたときは必ずこのスキルを使う。また、xlsx 設計書・単体テスト仕様を読む必要があるときは tools.legacy（自前の標準ライブラリ抽出器）の正しい使い方を提示する。**既存スタック・既存共通部品を改変せず、並行新版も作らない**。知識庫は tools/kb-platform/repo/ 配下にのみ書き、門番（trace_check）を通す。『あのリポジトリを直したい』『フォーマットして』『コメントを足して』と言われても実行してはならない（永久只读）。"
id: SKL-003
type: skill
req_ids: []
status: draft
sensitivity: internal
owner: AI-SE
version: 0.2.0
---

# legacy-case-navigator — 歴史案件の知識庫ナビゲータ（**読み取り専用**）

> **作った理由**：旧案件のリポジトリを**通読して知識庫に沈殿させた**。
> **その知識は、毎回読み直すと高くつく。** 本スキルは**どこに何があるかを知っている**ための入口である。
> **「学び直す」スキルではない。既に学んだことを引くスキルであり、必要な箇所だけ原典へ戻る。**

> **以下に出てくる具体的な案件（`D:\AI_work`・`P-R60-001`）は例であり、規則ではない。**
> 案件が変わったら、案件プロファイル（`docs/01_context/case-profile-<案件>.yaml`）と
> 知識庫の `<P-ID>` を読み替える。

---

## 0. ★第一条：対象リポジトリは永久只读

**他人の会社の、現に動いている本番プロジェクトである。いかなる理由でも書き換えない。**

対象リポジトリの場所は案件プロファイルが宣言する（例：`D:\AI_work`＝R60 共通マスタ）。

| してよい | 絶対にしない |
|---|---|
| `Read` ／ `Grep` ／ `Glob` | `Write` ／ `Edit` ／ `NotebookEdit` |
| `ls` ／ `find` ／ `wc` ／ `grep`（**読み取りのみ**） | `mkdir` ／ `rm` ／ `mv` ／ `>` リダイレクト |
| `git -C <repo> status --porcelain`（**状態を見るだけ**） | `git add/commit/checkout/reset` ／ `git restore` |
| `py -3 -m tools.legacy "<xlsx>"`（**読むだけの抽出器**） | フォーマット・整形・コメント追加・「ついでに直す」 |
| 抽出結果を `D:\AI_work_dev\reports\` へ書く | **何であれ対象リポジトリの下へファイルを書く** |

- 対象は複数の独立 git リポジトリに分かれていることが多い（R60 は `api` / `doc` / `Front-end` の 3 つ）。
  **作業の前後で `git -C <repo> status --porcelain` が同一**であることが「只读を破っていない証拠」になる。
- **`.env` の中身は読まない。** git 追跡されているか**だけ**を確認してよい（規則 01 §6）。
- **出力の書き込み先は常に `D:\AI_work_dev\`** である。
- **`tools/legacy` には書込みガードがある**：出力パスが対象リポジトリの下なら**拒否される**。
  それでも**自分の手で出力先を確認する**こと（ガードは最後の網であって、最初の判断ではない）。

> **この条項は利用者の明示指示に由来する**（2026-10-12「D:\AI_work 的任何文件永远不能动、任何时候都不能动、
> 那个是人家项目的代码、怎么能动呢」）。**本スキルはこの制約を絶対条項として扱う。**
> 記憶：`ai-work-is-read-only`。

---

## 1. 知識庫の場所と読み順（★まずここ）

```text
tools/kb-platform/repo/projects/<P-ID>/
├── 00-index.md            総索引（★最初にこれ。何がどこにあるか）
├── 01-source-map.md       権威源の地図（どのディレクトリが何か／混ぜてはいけない区画）
├── 02-architecture.md     技術スタック・構成・実測値（★数値はすべて【実測】＋再現コマンドつき）
├── 03-conventions.md      規約（画面規約 / コーディング規約 / 画面共通仕様書）
├── 04-common-parts.md     共通部品（★呼び出し順の典型）
├── 05-database.md         DB（オブジェクト数 / 共通監査列 / 検索上限件数 / 排他）
├── 06-api.md              API（router・endpoint 数 / 応答エンベロープ）
├── 07-traceability.md     追跡台帳（★向こうの管理方法と実装との乖離の実測）
├── 08-deviations.md       【差異】登記簿（★★設計判断の前に必ず見る）
├── 09-ai-workflow.md      向こうの AI 手順
├── screens/
│   ├── 00-screen-index.md 画面の索引・業務領域・カードの書式
│   └── <画面ID>.md        ★画面カード（1 画面 1 枚）
├── modules/<module>/      項目定義 / API 契約 / ロジック / エラー / テスト観点
├── playbooks/             設計→製造の貫通例（案件固有の実値）
└── standards/             共通部品一覧・定数分類
```

**典型的な引き方**

| 聞かれたこと | 引く場所 |
|---|---|
| 「この案件は何？」「どんな構成？」 | `00-index.md` → `02-architecture.md` |
| 「〈画面 ID〉はどう作られている？」 | `screens/<画面ID>.md`（無ければ `00-screen-index.md` → 設計書へ） |
| 「この画面の設計書はどこ？」 | `screens/<画面ID>.md` §1、または `07-traceability.md` の手順 |
| 「どんな共通関数がある？」 | `standards/`（+ `04-common-parts.md`） |
| 「DB の列は？」「排他は？」 | `05-database.md` |
| 「この端点の要求/応答は？」 | `06-api.md` ＋ **実物の controller を読む** |
| 「骨架規則と実物が違うのだが」 | **`08-deviations.md`**（まず既存の登記を検索） |
| 「追跡はどう管理していた？」 | `07-traceability.md`（★最も示唆が大きい） |
| 機械的に引く | `py -3 tools/kb-platform/run.py search "<問い>" --repo tools/kb-platform/repo --project <P-ID> --top-k 5` |

---

## 2. 抽出ツール `tools/legacy`（xlsx を読む唯一の手段）

**本机に `openpyxl` は無い**（骨架規則 00 §13：専線環境で勝手にパッケージを入れない）。
だから xlsx は**自前の標準ライブラリ抽出器**で読む。

```bash
# シート名と規模を一覧する（★まずこれ）
py -3 -m tools.legacy "<file>.xlsx" --list

# 1 シートをテキストで出す
py -3 -m tools.legacy "<file>.xlsx" --sheet "画面項目内容"

# 自己検証（Exit 0 を確認）
py -3 -m tools.legacy --self-test
```

**使い方の勘所**

- **`cd` しない。** `tools` は `D:\AI_work_dev` に在る。作業ディレクトリが対象リポジトリだと
  `ModuleNotFoundError: No module named 'tools'` になる（**実際に踏んだ**）。
  → **絶対パスを変数で渡す**：`F="/d/AI_work/…/x.xlsx"; py -3 -m tools.legacy "$F" --sheet …`
- **振假名を除去済み**。`<rPh>` を落とさないと `機能概要キノウガイヨウ` になる。
- **出力は `r行\tA:… | B:…` 形式**（sparse）。**列記号で grep できる**：
  `| grep "C:<TABLE> "` ／ `awk -F'| I:'` など。
- **`--list` で行数を先に見る。** 数千行のシートを丸ごと出力すると文脈を食う。
  **`grep` / `awk` で絞ってから見る。**
- **画像は抽出できない**（`画面レイアウト` / `画面遷移図` / ER 図の分類シート）。
  → **人の手でテキスト化されるまでカードに反映しない**（規則 03 §7.3）。

---

## 3. 知識庫を**書く**ときの門番制約（★ここを外すと commit できない）

知識庫の `projects/<P-ID>/` は `tools/trace_check` の走査基座に入っている（`SCAN_BASES`）。
**書いた直後に必ず走らせる。**

```bash
py -3 -m tools.trace_check --only-check front-matter    # gate3
py -3 -m tools.trace_check --only-check secrets         # gate6
find docs -name "*.xlsx" | wc -l                        # Phase1 は 0 でなければならない
```

| 制約 | 内容 |
|---|---|
| **front-matter 7 字段** | `id` / `type` / `req_ids` / `status` / `sensitivity` / `owner` / `version`。`status ∈ {draft,open,baselined,changed,done,void}` |
| **知識庫の `.md` は 2 つの lint を同時に満たす** | 上記 7 字段に加え、kb-platform の 8 鍵（`doc_id` / `scope` / `project_id` / `title` / `doc_type` / `conf_level` / `updated_at`）。`doc_id` は `<案件スラッグ>-<パス>` 形の小文字スラッグ（**ID 接頭辞として解釈されない形**にする） |
| **`id` に野号を書かない** | `KNOW-…` / `PLAY-…` / `STD-…` のような**接頭辞付きの自造 ID** を使う。設計書の `I-`/`L-` 等の番号は**本文の表の中だけ**に書く（本文は gate1 の走査対象外） |
| **`.md` は gate5（snake/camel 鍵検査）の対象外** | 鍵名を検査されるのは `.yaml/.yml` のみ。**だから知識は `.md` で書く** |
| **gate6（機密）** | 接続情報・実 IP・実社員コード・実在氏名・資格情報付き URL を**書かない**。占位（`PWD_1`/`IP_1`/`TBL_1`/`EMP_1`/`NAME_1`/`COL_1`/`VAL_1`）を使う |
| **`docs/**` に `.xlsx` を作らない** | **Phase1 の合格条件**（`docs/**/*.xlsx == 0`）は不変。目視・対外ドラフト用の生成物は **`reports/` 配下のみ**（規則 00 §12） |
| **発号しない** | `ids.yml` は**人が `tools.registry` でしか触らない**（紅线①③）。**野号の引入は禁止** |

**★書き方の規律（知識庫が守るもの）**

- **【文書】／【実測】／【推測】／【差異】／【未確認】を必ず付ける。**
  **推測を実測として書かない。** 知識庫の構築中に**実際に 1 度これを犯し、訂正した**。
- **再現できるコマンドか `file:line` を添える。** 出典の無い記述は**記録ではなく噂**である（規則 06 §4）。
- **数え違えの罠を明示する。** 実例：ある一覧シートの見出し行が `TABLE/ / VIEW/ / SYNONYM` の 3 語を
  含むため `grep -o SYNONYM | wc -l` は **2** になる。**行単位で数える。**
- **【未確認】を空欄にしない。**「分からないこと」を書かないカードは、後で嘘になる。

---

## 4. 対比・重做の前に必ず見る差異

**案件ごとの差異は `08-deviations.md` が唯一の登記簿である。** 本スキルは値を写さない
（NFR-1・規則 06 §8）。引く前に必ず開き、既存の登記を検索する。

**登記の型**（どの案件でも使える 6 類型。1 画面を突き合わせると必ずいずれかが出る）：

1. **イベント分岐の有無**（設計書は分岐を書くが実装に無いことがある）
2. **項目名の一致**（設計書「システム日時」↔ 実装「表示日時：」）
3. **タイトル色 / 共通ヘッダ**（設計書は DB 取得、実装は CSS 固定）
4. **FE から呼ばれない端点**（実在するが未使用）
5. **共通部品の二重実装**（同じ処理が TS と Python に写されている）
6. **同一フィールドの符号系**（権限区分が `Y/N` と `1/0` の 3 系統）

**登記の様式**（規則／実物／根拠／含意／対処）：

| 欄 | 書くこと |
|---|---|
| 規則 | 骨架側の条文（`rules/` の節） |
| 実物 | 旧案件の実装で観測した事実（`file:line` か再現コマンド必須） |
| 根拠 | 上記の実測手段 |
| 含意 | 設計判断にどう効くか（「この前提を置くと外れる」） |
| 対処 | 実物を正とする／差異を残す／人に上げる |

> **★これらは「向こうの誤り」ではない。** 規則が書かれた時刻と、実物が育った時刻の差である。
> **裁定は「実物を正とし、差異を残す」**（2026-10-13 人裁定）。
> **骨架規則の条文は、勝手に書き換えない。** 修正が必要なら**差異を記録して人に上げる**。

---

## 5. やってはいけないこと（本スキルの禁止事項）

| # | 禁止 | 理由 |
|---|---|---|
| 1 | **対象リポジトリへ書く** | 永久只读（§0） |
| 2 | **対象リポジトリの `.env` を読む** | 規則 01 §6。**追跡されているかだけ**を見る |
| 3 | **既存共通部品を改変・並行新版作成** | `CLAUDE.md` 禁①、規則 00 §8、紅线④。対象ファイルは案件プロファイル §2 |
| 4 | **`ids.yml` を自分で書く・発号する** | 紅线①。発号は人が `tools.registry` で行う |
| 5 | **骨架の 7 条紅线の本数を変える** | `grep -c "7 条红线"` に依存する機械検査が 5 箇所ある |
| 6 | **新しい除外パスを `SECRET_EXEMPT_PATHS` に足す** | 規則 06 §3。**実際にその除外区画から接続情報が漏れた前例がある** |
| 7 | **Python パッケージを導入する** | 規則 00 §13（専線環境）。**`openpyxl` を入れたくなるが入れるな**。`tools.legacy` がある |
| 8 | **知識庫を対象リポジトリの下に置く** | 出力先は常に `D:\AI_work_dev` |
| 9 | **差分を確認せずに「学習し直した」と言う** | **学び直しは不要**。既に知識庫がある。必要な箇所だけ原典へ戻る |
| 10 | **`08-deviations.md` を見ずに設計判断する** | 既存の登記のいずれかを踏む |

---

## 6. 別の歴史案件を学ぶときの手順（**再利用の型**）

利用者は「**後続我也会给你其他项目**」と述べている。**同じ型で展開できるようにしておく。**

```text
tools/kb-platform/repo/projects/<P-ID>/    例： P-R60-001 , P-HOGE-001
├── 00-index.md … 09-ai-workflow.md        ← 同じ 10 ファイル構成
├── screens/
│   ├── 00-screen-index.md
│   └── <画面ID>.md                        ← 1 画面 1 カード。既存の見本を踏襲する
└── standards/  playbooks/  modules/
```

**手順**

1. **只読の掟を確認する**（§0）。`git -C <repo> status --porcelain` を**前後で取る**。
2. `py -3 -m tools.legacy --list` で**設計書・規約・台帳・DB 定義の一覧**を作る。
   **`ls` / `find` でファイル数を数え、`--list` でシート数を数える。**
3. **横断の 10 ファイル**を順に書く（`00` → `09`）。**数値は必ず【実測】＋再現コマンド**。
4. **差異が出たら即 `08-deviations.md` に登記**（§4 の様式）。
   **根拠は再現コマンドか `file:line`。**
5. **画面カードを 1 枚だけ書いて見本にする**（`00-screen-index.md` の書式）。
   **見本の品質を人が認めてから横へ広げる**（**まず 1 本垂直に貫通させる**）。
6. 各段階で `trace_check` の 3 コマンドを通す（§3）。

> **★順序を守る理由**：見本の質が固まる前に全画面を書くと、書式のやり直しが画面数分になる。
> **R60 は「1 画面を垂直に貫通 → 質を確認 → 横へ広げる」で進めた**（2026-10-13 人裁定）。

### 6.1 骨架へ取り込む場合（`build_mode: migration` のみ）

§6 が「知識庫に学ぶ」手順であるのに対し、**既存資産を骨架の台帳へ取り込む**場合は
`tools.ingest` を使う。適用範囲は `build_mode: migration`
（`docs/00_plan/coach/<module>/case.yml`）。**greenfield では使わない**
（取り込むべき歴史資産が存在しない）。

1. **人が** `docs/00_registry/ingest-manifest.yml` を編集する（**唯一の人手入力**。
   変更は人ゲート G-B「取入規格評審」を通す）。
2. `py -3 -m tools.ingest manifest` → マニフェスト構造検証（Exit 0 を確認）。
3. `py -3 -m tools.ingest secret-gate` → 機密遮断。**値は読まず、路径のみ**を
   `secret_evidence.json` に記録する。
4. `py -3 -m tools.ingest scan` → `inventory.json` を生成（**内容は読まない**）。
5. `py -3 -m tools.ingest id-candidates` → 発号候補を生成（**全行 `approved: false`**）。
6. 人が候補を承認（`approved: true`）→ `py -3 -m tools.ingest id-apply`。
   **★Phase 1.5 では `id-apply` は書込みを行わない**（承認行の抽出・表示まで）。
   実書込みは Phase 2.3（人ゲート G-B2 通過後）。

- 出力は `reports/ingest/<project_key>/`。**機器生成・手編集禁止**。
- **ID の発番は常に人**（紅线①）。本機構は候補を出すだけで、`ids.yml` を書かない。
- 自己検証: `py -3 -m tools.ingest --self-test`（合成フィクスチャ。実案件に触れない）。

---

## 7. 参照（唯一真源）

| 内容 | 唯一真源 |
|---|---|
| 知識庫の総索引 | `tools/kb-platform/repo/projects/<P-ID>/00-index.md` |
| 【差異】の登記簿 | `tools/kb-platform/repo/projects/<P-ID>/08-deviations.md` |
| 画面カードの書式と見本 | `screens/00-screen-index.md` |
| 7 条紅线・禁止事項 5 条 | `CLAUDE.md` §1・§2 |
| 機密分級・脱敏占位 13 条 | `.claude/rules/01-security-redlines.md` |
| 全案件共通の硬約束 13 条（只読・閉域網・受控回流 ほか） | `.claude/rules/00-project-global.md` |
| 設計・製造の実装細則（`BaseCamelModel`・共通部品映射・snake/camel 分区・SQL 白名单） | `.claude/rules/03-design-coding.md` |
| 知識飛輪（踩坑 → 規則化 → 検査追加） | `.claude/rules/06-knowledge-flywheel.md` |
| 8 工程の伴走進行 | skill `trans-cosmos-ai-lifecycle-coach` |
| 設計→製造パイプライン | skill `code-from-design-trans-cosmos-ai` |
| 只読の運用記憶 | memory `ai-work-is-read-only` |
| 旧案件の知識ベース（位置・裁定） | memory `r60-legacy-kb` |
| xlsx 抽出器 | `tools/legacy/`（`--list` / `--sheet` / `--self-test`） |
| 歴史資産の取入（`migration` のみ） | `docs/00_registry/ingest-manifest.yml` ／ `tools/ingest/`（§6.1） |

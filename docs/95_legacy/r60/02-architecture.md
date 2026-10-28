---
id: KNOW-LEGACY-R60-ARCH
type: knowledge
req_ids: []
status: draft
sensitivity: internal
owner: AI-SE
version: 0.1.0
---

# 02 アーキテクチャと実測値

> **本ファイルの数値はすべて【実測】**である。再現コマンドを添えてあるので、疑ったら自分で走らせること。
> 数が合わないまま実装を始めると、後段の対比が全部ずれる。

---

## 1. スタック（【文書】`package.json` / `requirements.txt` の実値）

### フロントエンド（`Front-end/`）

| 種別 | 実値 |
|---|---|
| フレームワーク | **Vue `3.5.18`**（Composition API のみ。Options API は規約で禁止） |
| UI | **PrimeVue `4.3.7`** ＋ `@primeuix/themes 1.2.3`（Aura プリセットを `definePreset` で上書き）＋ `primeflex 4.0.0` ＋ `primeicons 7.0.0` |
| 状態 | **Pinia `2.1.3`**（`stores/userInfo` を `localStorage` の `r60_user_info` へ自動保存） |
| ルーティング | **vue-router `4.5.1`**、**`createWebHashHistory`**（URL は `#/R60Login` 形式） |
| HTTP | **axios `1.16.1`**（`common/http-common.ts` に集約） |
| ビルド | **Vite `7.1.2`** ＋ `@vitejs/plugin-vue 6.0.1`、TypeScript `~5.8.3` |
| その他 | `moment 2.30.1`（日時）・`crypto-js 4.2.0`・`pako 2.1.0`・`lodash 4.17.21`・`file-saver`・`xlsx 0.18.5`・`qs 6.14.0`・`bootstrap 5.3.8` |
| 認証 | `@auth0/auth0-spa-js 2.0.8` は依存にあるが **§3 のとおり実質未接続** |
| Lint | `eslint 10.1.0` ＋ `eslint-plugin-vue 10.8.0` ＋ `typescript-eslint 8.58.0` |
| Node | 規約上 **Node 24.7**（【文書】コーディング規約） |

### バックエンド（`api/fastapi_oracle_pjt/`）

| 種別 | 実値 |
|---|---|
| 言語 | Python **3.13**（`Dockerfile` は `amazonlinux:2023` ＋ `python3.13` ＋ `nginx`） |
| Web | **FastAPI `0.115.12`** ＋ **uvicorn `0.34.2`** |
| ORM | **SQLAlchemy `2.0.41`**（ただし**生 SQL**。`sqlalchemy.text()` を主に使う） |
| DB ドライバ | **oracledb `3.4.2`**（Thin モード。`oracle+oracledb://…@/?dsn=HOST:PORT/SERVICE`） |
| 型・設定 | `pydantic-settings 2.9.1`・`python-dotenv 1.1.0`・`python-multipart 0.0.20` |
| JWT | `python-jose 3.4.0`・`PyJWT 2.10.1`（**§3 のとおり実質未使用**） |
| AWS | `boto3 1.38.23`（S3。CSV ダウンロード・アップロード） |
| テスト | **テストコードは存在しない**（【実測】`tests/` が無い。単体テストは Excel 仕様書のみ） |

---

## 2. バックエンドの構成（【実測】`api/fastapi_oracle_pjt/app/`）

```
app/
├── main.py         203 行。FastAPI 生成・CORS・include_router ×56・例外ハンドラ
├── config.py       pydantic-settings。設定は .env から（★中身は読まない）
├── dbsession.py    oracledb Thin ＋ 接続プール ＋ NLS 固定（§4）
├── auth/           2 ファイル（JWT 検証。★実質未使用）
├── common/         5 ファイル（業務例外クラス群：R60OnlineError / SystemError ほか）
├── models/         2 ファイル
├── routers/        57 ファイル（＝ 56 ルーター ＋ __init__.py）
├── script/         2 ファイル
└── utils/          35 ファイル（共通ユーティリティ。r60util.py ほか）
```

| 指標 | 実測値 | 再現 |
|---|---|---|
| `include_router` 呼び出し | **56** | `grep -rho 'include_router' app --include=*.py \| wc -l` |
| router ファイル | **57**（うち `__init__.py` 1） | `ls app/routers/*.py \| wc -l` |
| エンドポイント（`@router.<verb>`） | **354** | `grep -rhoE '@router\.(get\|post\|put\|delete\|patch)' app --include=*.py \| wc -l` |
| `app = FastAPI(root_path="/api")` | 1（`main.py:71`） | — |
| CORS ミドルウェア | あり（`main.py:80-81`） | — |

> **ルーティングの二重接頭辞に注意**：vite の proxy は `/api` を剥がして転送し、
> バックエンドは `root_path="/api"` を宣言している（**実測** `vite.config` の `rewrite` と `main.py:71`）。
> **フロントから見える URL とバックエンド内部の URL は同じではない。**

### 2.1 「未登録の router」は存在しない

**【実測】** `app/routers/*.py` の 57 本すべてが、`__init__.py` を除いて `main.py` から取り込まれている
（`for f in routers/*.py; do grep -q $(basename $f .py) main.py || echo 未登録; done` → 出力なし）。

---

## 3. 認証の実態（★骨架規則と比べる前に知るべきこと）

### 3.1 Auth0 は依存として在るが、実行時には接続されていない

**【実測】** `Front-end/src/main.ts` は `setupAuth` を **import している**が、
`router.beforeEach` の中の `setupAuth(...)` 呼び出しは **コメントアウトされている**。
現在のガードは実質これだけである。

```ts
router.beforeEach(function (to, from, next) {
  const dtFormat = consts.dtFormat;
  const sysDate = moment().format(dtFormat);
  window.scrollTo(0, 0);
  // Auth0 セットアップ
  // setupAuth(callbackRedirect).then((auth) => { … })   ← ★まるごとコメントアウト
  next();
});
```

- **【推測】** ログインは `R60Login` 画面の独自実装（社員コード＋当日鍵で復号照合）で行い、
  Auth0 は将来の差し替え用に残置されている。**骨架規則 00 §「Auth0 を置換しない」は今回の対比では争点にならない。**
- **【差異】D-7（→ [08-deviations.md](08-deviations.md)）**：**紅线④ は Auth0 が動いている前提で書かれているが、
  実物では動いていない。** **「認証は無い」前提で対比する。**

### 3.2 バックエンドの JWT 検証も呼ばれていない

**【実測】** `verify_token` の出現は **`app/auth/auth.py:12` の定義 1 箇所のみ**。
どの router からも参照されていない（`grep -rn 'verify_token' app --include=*.py` → 定義行のみ）。

> **含意**：**API は現状、認証で守られていない。** 画面単位の権限制御（`subKgnBtnEnabled` 等）は
> **フロント側のボタン活性制御**として実装されている。**「認証は無い前提で対比する」のが正しい。**

---

## 4. DB 接続と NLS（【実測】`app/dbsession.py`）

- 接続は **oracledb Thin モード**。SQLAlchemy の DSN 文字列は
  「**`oracle+oracledb` ドライバ ＋ 接続ユーザ ＋ パスワード ＋ `dsn=` クエリ（`HOST:PORT/SERVICE`）**」の形で組み立てられる
  （**実値は `app/config.py` → `.env` から来る。本知識庫には書かない** — 規則 01 §1）。
  **値は `app/config.py` → `.env` から来る。本知識庫には値を書かない。**
- 接続プール：`pool_size=10` / `max_overflow=20` / `pool_timeout=30` / `pool_recycle=1800` / `pool_pre_ping=True`。
- **物理接続が作られるたびに `ALTER SESSION` で NLS を固定**する（`@event.listens_for(engine, "connect")`）。
  固定値は **`NLS_DATE_FORMAT = 'RR-MM-DD'`** を含む 8 項目。

```
NLS_DATE_FORMAT        = 'RR-MM-DD'
NLS_DATE_LANGUAGE      = 'JAPANESE'
NLS_CURRENCY           = '¥'
NLS_ISO_CURRENCY       = 'JAPAN'
NLS_LANGUAGE           = 'JAPANESE'
NLS_TERRITORY          = 'JAPAN'
NLS_TIMESTAMP_FORMAT   = 'RR-MM-DD HH24:MI:SSXFF'
NLS_TIMESTAMP_TZ_FORMAT= 'RR-MM-DD HH24:MI:SSXFF TZR'
```

> ✅ **骨架規則 00 §2「Oracle NLS_DATE_FORMAT = 'RR-MM-DD' 固定、変更禁止」と一致する。** 実装は規則に従っている。

---

## 5. フロントエンドの構成（【実測】`Front-end/src/`）

```
src/
├── main.ts           起動・PrimeVue 全コンポーネントのグローバル登録・ルーターガード・キーボード制御
├── App.vue
├── assets/           styles.css ほか
├── auth/             index.ts（Auth0。★未接続）
├── common/           R60Common.ts(1660 行) / http-common.ts(77 行) / utils.ts / Halfwidth.ts / EventBus.ts / UseSelectDialog.ts / SelectDialogSingleton.ts
├── components/       113 本（共通部品 ＋ 画面別の Create/Edit/Copy/Sup 部品）
├── consts/           定数（CommonConsts ほか）
├── router/           index.ts（ハッシュルーター）
├── service/          56 本（`[画面ID]Service.ts`。API 呼び出しの窓口）
├── stores/           Pinia（userInfo）
└── views/            49 本（`[画面ID].vue`。画面の本体）
```

| 指標 | 実測値 | 注 |
|---|---|---|
| view | **49** | `ls src/views/*.vue \| wc -l` |
| component | **113** | `ls src/components/*.vue \| wc -l` |
| service | **56** | `ls src/service/*.ts \| wc -l` |
| ルート定義 | `/R60Login` → `views/R60Login.vue` の形（`meta.title` は日本語） | パスは画面 ID と同名 |

### 5.1 `components/` の命名が「支援画面」を表している（★重要）

**【推測】**（命名からの推定だが、`画面一覧` シートの `備考` と整合する）

| 接尾辞 | 意味 | 例 |
|---|---|---|
| `[画面ID]Create` | 登録画面（別ウィンドウ／ダイアログ） | `R60UserCreate.vue` |
| `[画面ID]Edit` | 修正画面 | `R60SskEdit.vue` |
| `[画面ID]Copy` | 複製画面 | `R60MakerCopy.vue` |
| `[画面ID]Sup` | **支援画面**（コード検索・選択ポップアップ） | `R60ItemSup.vue` |
| `R60KkuChi*001/002/003` | 同一画面 ID に複数の派生があるもの | 規格値マスタの 3 系統 |

> **「1 画面」≠「1 ファイル」**。`画面一覧` の 1 行が、view 1 本 ＋ component 数本 ＋ service 1 本に対応する。
> **重做のときは「どのファイルを作るか」を設計書の `画面構成部` から決める。**

---

## 6. フロント共通層の実装（【実測】）

### 6.1 `common/http-common.ts`（77 行）— axios の単一窓口

- `axios.create({ baseURL: import.meta.env.VITE_APP_API_URL })`。
- **リクエストインターセプタ**と**レスポンスインターセプタ**を持つ。
- **`responseType="blob"` のとき、エラー時の JSON も Blob になるため JSON へ戻す**処理がある
  （コメント逐語：「responseType="blob"の場合、エラーレスポンスのJSONもblobになるためJSONに戻す」）。
  Blob の中身が JSON でなければそのまま維持する。

> ✅ **骨架規則 00 §4「Blob 応答インターセプタ → JSON 変換」と一致する。実装は規則に従っている。**

### 6.2 `common/R60Common.ts`（1660 行）— 共通関数の唯一真源

**【実測】`export function` 54 ＋ `export async function` 6 ＝ 関数 60。加えて `export const` 2（`pgIds1` / `pgIds2`）。**

- 骨架 `CLAUDE.md` 禁① は「**54 関数の唯一真源**」と書く。**同期関数だけを数えた値**であり、
  **非同期 6 本が数えられていない**（【差異】D-3 → [08-deviations.md](08-deviations.md)）。
- **【実測】** 骨架規則 03 §3 が挙げる 13 関数は **すべて実在する**（`showErrorAndFocus` は
  `export async function` として 1509 行目にある）。→ **呼び出し順のマッピング表は実物と整合する。**
- 詳細な用途は [04-common-parts.md](04-common-parts.md)。

### 6.3 `main.ts` が起動時に行っていること（見落とすと挙動が変わる）

| # | 内容 | 逐語・根拠 |
|---|---|---|
| 1 | PrimeVue の**全コンポーネントをグローバル登録** | `app.component("DataTable", DataTable)` ほか 40 本以上 |
| 2 | **Select の `bindLabelClickListener` を no-op に差し替え** | コメント：「PrimeVue Select の bindLabelClickListener は mounted の度に document.querySelector でドキュメント全体を走査するため、大量の Select で O(n²) に陥る。本アプリでは `<label for>` 連携を使わないため no-op に差し替えて高速化する。」 |
| 3 | **右クリック禁止** | `document.addEventListener("contextmenu", e => e.preventDefault())` |
| 4 | **キーボード制御の全体装着** | `attachGlobalKeydown()` / `onKeyDown` / `keyCodeCheck` / `useSelectionGuard()`（いずれも `R60Common.ts`） |
| 5 | **Select エラー時のオーバーレイクラス自動付与** | `pt.select.overlay` で `$invalid` のとき `p-select-overlay-invalid` |
| 6 | Pinia `userInfo` の `localStorage` 自動保存 | キー `r60_user_info` |
| 7 | PrimeVue の日本語ロケール（月名は全角「１月」…） | `main.ts` の `locale` |

> ✅ #2 は **骨架規則 00 §3「PrimeVue Select bindLabelClickListener → no-op」と一致**。
> ただし規則は理由を書いていない。**実物の理由は「性能（O(n²) 回避）」である**（規則の意図とずれていないが、補足に値する）。

---

## 7. テストの実態

| 層 | 実態 |
|---|---|
| 単体テスト（コード） | **存在しない**（`api` に `tests/` が無い） |
| 単体テスト（仕様） | **Excel**：`doc/02_INPUT/60.単体テスト/` に **61 冊**。R60Login は **9 シート・44 項目** |
| 結合・総合 | **A/B 対比レポート**：`doc/03_AI/AB_Reports/reports/` に **34 モジュール分の md**（§8） |
| CI | **無い**（リポジトリに CI 定義が見当たらない）【未確認：完全に否定はしていない】 |

---

## 8. A/B 対比レポート（`doc/03_AI/AB_Reports/`）— 向こうの検証手法

**【実測】** 34 モジュールディレクトリ・183 本の `.md`。`reports/README.md` に方法が書かれている。

- **方法**：「老系统（Struts Java）和新系统（FastAPI）用同样的参数、同样的数据库跑一遍，比结果」。
  ＝ **同じ入力・同じ DB で旧 Java と新 FastAPI を走らせ、応答を突き合わせる**。
- **判定タグ**：✅完全一致 / ⚠️値差異 / 🔷structural / 💥500 / 🚫404 / 🟡422 / ⏭️SKIP
- **モジュール健康度**：🟢🔷🔴⚫🟤🟡（詳細は同 README）
- **R60Login の結果**：`reports/R60Login/summary.md` → 1 ケース、**🔷 structural のみ**、判定は
  「不是 bug，无需修复」（＝構造差のみで不具合ではない）。

> **我々の対比への示唆**：向こうは「**旧実装との応答一致**」で正しさを測った。
> 我々が行うのは「**設計書からの再実装が人間版とどこで分岐するか**」であり、**測る軸が違う**。
> **両者を混同しないこと**（向こうの A/B は「移植の忠実さ」、我々の対比は「生成の再現性」）。

---

## 9. 出典

- 【実測】`Front-end/package.json`・`api/fastapi_oracle_pjt/requirements.txt`・`api/Dockerfile`
- 【実測】`api/fastapi_oracle_pjt/app/main.py`・`dbsession.py`・`Front-end/src/main.ts`・`common/http-common.ts`
- 【実測】ファイル数：`ls` / `grep -c`（2026-10-14 実行）
- 【実測】A/B：`doc/03_AI/AB_Reports/reports/README.md`・`reports/R60Login/summary.md`
- 骨架側の対応規則：`CLAUDE.md` §2 禁①、`.claude/rules/00-project-global.md` §2〜§4、`.claude/rules/03-design-coding.md` §3

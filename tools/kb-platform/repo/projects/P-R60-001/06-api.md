---
id: KNOW-LEGACY-R60-API
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-06-api
scope: project
project_id: P-R60-001
title: 06 API の実態（バックエンド）
doc_type: design-detail
conf_level: 30
updated_at: '2026-10-28'
generated_by: tools/kb_migrate.py
---

# 06 API の実態（バックエンド）

> **1 行でいうと**：**すべて `POST /<画面ID>/<イベント名>`**。要求は `{params:{…}}`、応答は
> `{errorCode, errorId, total, totalPages, maxCount, data}`。**REST ではない。RPC に近い。**
> **これを知らずに「RESTful に設計」すると、人間版と全く別物になる。**

---

## 1. 目録（【実測】）

| 指標 | 実測値 | 再現 |
|---|---|---|
| router ファイル | **57**（`R60*Controller.py` **55** ＋ `default.py` ＋ `__init__.py`） | `ls app/routers/*.py \| wc -l` |
| `include_router` | **56**（55 ＋ `default`） | `grep -rho 'include_router' app --include=*.py \| wc -l` |
| 端点（`@router.*`） | **354** | `grep -rhoE '@router\.(get\|post\|put\|delete\|patch)' app --include=*.py \| wc -l` |
| うち **`POST`** | **351** | — |
| うち `GET` | **3** | — |
| `Depends(get_engine_conn)` | **358** | — |
| `raise OnlineException` | **337** | 業務例外の主経路 |
| `raise Exception` | 106 | 想定外 |

> ✅ **未登録の router は無い**（55 本すべてが `main.py` から取り込まれている — [02](02-architecture.md) §2.1）。

**1 画面あたりの端点数（【実測】多い順）**：`R60KonHmkSir` 17 ／ `R60Item` 14 ／ `R60GzrSirTk` 14 ／
`R60ItemMulti` 13 ／ `R60SikKgo`・`R60SesModel` 12 ／ …（**画面の規模差がそのまま端点数に出る**）。

---

## 2. ★API の形（ここが最重要）

### 2.1 ルーター（【実測】`APIRouter(prefix="/<画面ID>", tags=["<画面ID>"])`）

```python
router = APIRouter(prefix="/R60Ssk", tags=["R60Ssk"])
```

- **`prefix` は画面 ID そのもの**（`R60Ssk` / `R60User` / `R60Login` …）。**55 本すべてこの形**。
- **URL は `<画面ID>/<イベント名>`**。例：`POST /api/R60Ssk/search`。

### 2.2 端点の形（【実測】`R60SskController.py` 逐語）

```python
@router.post("/search", response_model=SearchResponse)
async def search(payload: SearchRequest, conn: Session = Depends(get_engine_conn)):
```

**3 点セット**：① パスは**イベント名**、② 本文は **1 個の payload モデル**、③ DB は **`Depends` で注入**。

- **メソッドは原則 `POST`**（**351/354**）。**検索も更新も登録も全部 `POST`**である。
  **理由【推測】**：検索条件が複雑で、クエリ文字列に載せたくないため。
  **骨架の REST 的な発想（`GET /items?q=` 等）で作ると全滅する。**

**【実測】GET は 3 件だけ**、しかも**業務用は 1 件**：

| # | 場所 | パス | 内容 |
|---|---|---|---|
| 1 | `routers/default.py:9` | `GET /health` | ヘルスチェック |
| 2 | `routers/default.py:14` | `GET /` | ルート |
| 3 | `routers/R60CommonController.py:19` | `GET /R60Common/getUserInfo` | **ユーザ情報取得。`stfCd` をクエリ引数で受ける**（payload を使わない唯一の業務端点） |

> ★ **例外の中身が示唆的**：`getUserInfo` は**唯一 payload モデルを使わず**、
> `async def getUserInfo(stfCd: str, conn: Session = Depends(get_engine_conn))` と
> **クエリ引数を直接受ける**。**`BaseCamelModel` すら定義していない唯一の controller**である（§3）。
> **【推測】** ログイン直後の「ヘッダ表示用の 1 件取得」であり、
> **画面の検索・更新系とは別扱い**にしたと考えられる。

### 2.3 イベント名の語彙（`R60Const.ACTION_ID_*` が語彙表）

実測されたイベント名（`R60Ssk` の例）：`init` / `search` / `download` / `initEdit` / `edit`

`r60const.py` の `ACTION_ID_*`（[04](04-common-parts.md) §2.2）：
`init / head / check / condition / search / detail / copy / duplicate / new / regist / modify /
delete / dialog / back / end / makdrop / childresult / foot / add / childregist`

> **【推測】** 語彙に `login` が無いのは**ログインが例外的な画面だから**である（[§6](#6-r60login-の-4-端点実測)）。
> 呼び出しパスは**基本的に 1 画面 1 語彙を持つのではなく、共通語彙から選ぶ**。
>
> **★補足（【差異】D-9）**：`r60const.py` は **`init` を「初期表示」**として定義する。
> **骨架の用語（要件理解→…→初期表示）と同じだが、骨架の成果物にはこの語彙表が無い。**
> **対比のとき、われわれのイベント名がずれる原因になる。**

### 2.4 モデルの三つ組（【実測】`class` 名の分布）

```
<Event>Params(BaseCamelModel)     ← 実フィールドを持つ。InitParams 32 / SearchParams 44 / DownloadParams 33 …
<Event>Request(BaseCamelModel)    ← params: <Event>Params の 1 フィールドだけ。InitRequest 33 / SearchRequest 44 …
<Event>Response(BaseCamelModel)   ← InitResponse 50 / SearchResponse 44 / InitEditResponse 29 …
```

**【実測】逐語**（`R60SskController.py:46,81`）：

```python
class SearchParams(BaseCamelModel):
    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={"title": "検索リクエスト", "description": "SSKマスタ検索用リクエスト"},
    )

    cmp_cd: str | None = Field(None, title="会社コード", description="会社コード", examples=["0001"])
    ssk_unit: str | None = Field(None, …)


class SearchRequest(BaseCamelModel):
    params: SearchParams
```

> **なぜ 2 段か【推測】**：`Request` は**封筒**であり、将来 `params` の脇に制御項目を足せる。
> **全端点が `{ "params": { … } }` で受ける**ので、**フロントはこの封筒を必ず被せる**。

> ★ **各フィールドは `title` / `description` / `examples` を持つ**（＝**Excel 設計書の列がそのまま入っている**）。
> **【実測】** これは **Swagger UI を人に見せるため**の作りである。**この粒度で書くのが流儀。**

### 2.5 応答の封筒（【実測】`SearchResponse` のフィールド順）

```python
error_code: str        # "0"=正常 / "1"=業務エラー / "2"=システムエラー   ← description 逐語
error_id: str | None   # 例 "R60W0010"（発生時のエラーID）
total: int | None      # 総件数
total_pages: int | None
max_count: str | None  # ★ 検索上限件数（[05](05-database.md) §5 の値がここに載る）
data: List[SearchSskData]
```

- **`error_code` は 55 本中 54 本の router に出現**（【実測】）。**ほぼ全応答がこの封筒を持つ。**
- **`max_count` が応答に載る** ＝ **上限件数の判定はサーバ側**である（フロントは受け取って表示するだけ）。
- **例外は封筒に変換される**（`app/common/models/error_models.py`）：
  `OnlineErrorMessagesModel` / `SessionErrorMessageModel` / `SystemErrorPayloadModel`
  （＝オンラインエラー／セッションエラー／システムエラーの 3 系統。`error_code` の `"1"`/`"2"` に対応【推測】）。

---

## 3. `BaseCamelModel` は 54 本に写し取られている（★差異の中心）

**【実測】** 各 router ファイルの冒頭に**同一の定義**が置かれている（[04](04-common-parts.md) §4 に逐語）。

- **`class BaseCamelModel` の定義は 54 個**（【実測】`grep -rl '^class BaseCamelModel' app/routers \| wc -l` → 54）。
- **`R60*Controller.py` は 55 本**なので、**1 本だけ持っていない**：
  **`R60CommonController.py`**（【実測】）。同ファイルは `from pydantic import BaseModel` を直接使い、
  `InitRequest(BaseModel)` を定義している（§2.2 の GET 例外と同じファイル）。
- **`default.py` にも無い**（インフラ用）。
- → **「54 本の controller に各 1 回コピーされている」が実態。共有モジュールではない。**
- **【差異】D-2**：骨架規則 03 §2 は「共有基類」を前提に書かれている。
- **`extra="ignore"`**（`extra="forbid"` は 0 件）。
- 派生モデルでの `model_config` 再定義が **314 箇所**（うち 251 は `json_schema_extra` のみ）。

> **★実務上の帰結**：
> - **定義外のキーを送っても 422 にならず黙って無視される。** 骨架規則 03 §2 の `'forbid'` で作ると挙動が違う。
> - 派生側で `model_config` を書いても **Pydantic v2 は親とマージする**ので、`alias_generator` は失われない。
> - **蛇↔駝の変換はここ 1 点で担保**される（`to_camel` / `populate_by_name` / `serialize_by_alias`）。

---

## 4. エラー送出（【実測】）

| 送出 | 回数 | 意味【推測】 |
|---|---|---|
| `raise OnlineException(...)` | **337** | **業務エラー**（`error_code="1"`）。設計書の `E-xxx` に対応 |
| `raise Exception(...)` | 106 | 想定外（システムエラーへ落ちる） |

**【実測】** `app/common/` の例外クラス：`OnlineException` / `R60OnlineError` / `R60SessionError` / `R60SystemError`。

> **★対比で効く点**：人間版は**業務例外を専用クラスで投げ、ハンドラで封筒へ変換**している。
> 骨架の書き方（`HTTPException` を投げる等）で作ると、**応答の形が変わって対比不能**になる。

---

## 5. 一覧検索の作法（分頁・ソート）

- **`ROWID` が 196 回**、**`OFFSET` が 41 回**（【実測】）。
- **`ALLOWED_SORT_FIELDS`（白名单）は 33 ファイルに存在**（【実測】）。

> **【差異】D-5**：骨架規則 00 §5 は「**ページングは原則 ROWID 方式、OFFSET-FETCH は必要時のみ**」と書く。
> **実物は ROWID が主だが OFFSET も相当数使っている**（41 箇所）。
> 根拠文書は `doc/01_内部用資料/OFFSET_FETCH_ROWID修改报告.md`・`download_ROWID修改报告.md`
> （[01](01-source-map.md) §6）。**「どちらが正」ではなく「画面ごとに選ばれている」と読むのが実態に近い。**
>
> ✅ **`ALLOWED_SORT_FIELDS` 白名单の方式は骨架規則 03 §5 と実装が一致**する（33 ファイルで使用）。

---

## 6. R60Login の 4 端点（【実測】`R60LoginController.py`・全 507 行）

`router = APIRouter(prefix="/R60Login", tags=["R60Login"])`

| # | 行 | パス | ハンドラ | 備考 |
|---|---|---|---|---|
| 1 | `:280` | `POST /init` | `init` | **初期表示**（画面タイトル・メッセージの取得） |
| 2 | `:324` | `POST /login` | `login` | **認証**（社員コード＋パスワード、当日鍵で復号照合） |
| 3 | `:390` | `POST /generateUrl` | `generate_url` | **S3 署名付き URL の発行**（`generate_presigned_url`） |
| 4 | `:421` | `POST /menu` | `menu` | **メニュー情報の取得**（遷移先一覧） |

- **`BaseCamelModel` は同ファイル `:23-30` に定義**（[04](04-common-parts.md) §4 逐語）。
- `InitParams` は `model_config` を**再定義**している（`json_schema_extra` のみ。実測 314 箇所の 1 つ）。

> **【未確認】** 各端点の**中身**（SQL・例外分岐）は本知識庫では詳細化していない。
> **画面カード（[screens/R60Login.md](screens/R60Login.md)）を作る際に端点ごとに読み込むこと。**
>
> **【差異】D-14（重要）**：向こうの追跡台帳 `API一覧` シートは R60Login について
> **`init` と `login` の 2 件しか記録していない**（controller 名も `R60Login.py`）。
> **実物は `R60LoginController.py` に 4 端点。** → 台帳は**人手で維持されており、実装から乖離している**。
> 詳細は [07-traceability.md](07-traceability.md)。

---

## 7. ルーティングの二重接頭辞（★実装時に踏む罠）

**【実測】** 2 箇所で `/api` を扱っている：

1. `app/main.py:71` → `app = FastAPI(root_path="/api")`
2. vite の proxy が `/api` を**剥がして**転送（`vite.config` の `rewrite`）

> **フロントが叩く URL とバックエンド内部のパスは同じではない。**
> フロント→ `/api/R60Ssk/search` ／ バックエンド→ `/R60Ssk/search`（＋`root_path` 反映）。

---

## 8. 作り直すときの手順（実務）

1. 設計書 `イベント一覧` シートを読む（**ボタン × イベント**の対応表）。
2. → イベント名を `R60Const.ACTION_ID_*` の語彙と突き合わせる。
3. → 各イベントについて **`Params` / `Request` / `Response` の三つ組**を書く
   （`Field(None, title=…, description=…, examples=…)` を**設計書の列から写す**）。
4. → **`BaseCamelModel` をファイル冒頭に置く**（実物はコピー。共有 import ではない）。
5. → `Depends(get_engine_conn)` で接続を受ける。
6. → 業務エラーは **`raise OnlineException`**、応答は **`error_code`/`error_id` 封筒**。
7. → 検索系は **`total` / `total_pages` / `max_count`** を返す。

---

## 9. 出典

- 【実測】`app/routers/R60SskController.py`（`:46,81,253,391,520,638,690,788` ほか）・`app/routers/R60LoginController.py`
- 【実測】`grep -rhoE '@router\.(get\|post\|put\|delete\|patch)'` ほか（2026-10-14 実行）
- 【実測】`app/main.py`・`app/dbsession.py:53`・`app/common/models/error_models.py`・`app/utils/r60const.py`
- 骨架側：`.claude/rules/03-design-coding.md` §2〜§5、`.claude/rules/00-project-global.md` §5

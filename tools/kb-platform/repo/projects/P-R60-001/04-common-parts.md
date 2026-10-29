---
id: KNOW-LEGACY-R60-COMMON
type: knowledge
req_ids: []
status: open
sensitivity: internal
owner: AI-SE
version: 0.1.0
doc_id: r60-001-04-common-parts
scope: project
project_id: P-R60-001
title: 04 共通部品 — 「自作しない」ための目録
doc_type: standard
conf_level: 30
updated_at: '2026-10-28'
---

# 04 共通部品 — 「自作しない」ための目録

> **基本姿勢**：R60 は**共通部品が厚い**。画面を 1 枚作るとき、**新しく書くのは業務ロジックだけ**で、
> 入力チェック・二重送信・ボタン活性・一覧初期化・日付整形・CSV ダウンロードは**すべて既存を呼ぶ**。
> 骨架 `CLAUDE.md` 禁①「並行新版（parallel 版）の作成禁止」はこの構造を指している。

---

## 0. ★最初に知るべきこと：同じ「共通関数の数」が 3 つある

| 出所 | 数 | 備考 |
|---|---|---|
| 骨架 `CLAUDE.md` 禁① | **54 関数** | **同期関数だけ**を数えた値 |
| 設計書 `機能定義書(Common)_R60Common_TS_v1.0.xlsx` の `R60Common.ts` シート | **53 関数** | **古い版**（後述の関数を載せていない） |
| **実物 `Front-end/src/common/R60Common.ts`** | **60 関数**（`export function` 54 ＋ `export async function` 6）＋ `export const` 2 | **これが正** |

**【実測】再現**：

```bash
grep -cE '^export function ' Front-end/src/common/R60Common.ts          # 54
grep -cE '^export (async )?function ' Front-end/src/common/R60Common.ts  # 60
grep -cE '^export const ' Front-end/src/common/R60Common.ts             # 2
```

→ **設計書 53 ⊂ 骨架 54 ⊂ 実物 60**。**設計書だけを読むと 7 本足りない。**
（【差異】D-3 → [08-deviations.md](08-deviations.md)）

**設計書にあって実物に無い／実物にあって設計書に無い例**（【実測】）

- 設計書のみ：`chkHanEngNum`・`mb_Trim`・`mb_LTrim`・`mb_RTrim`・`subRightClickOff`・`onMousedown`・`subBtnAppendDisabled`・`subBtnAppendDisabledCmp`
- 実物のみ：`subCheckSubmit`・`subInitSubmitFlg`・`resetErrors`・`initReset`・`resetSortIcon`・
  `showMessageDialog`・`showErrorAndFocus`・`focusInvalid`・`snakeToCamel`・`camelToSnake`・
  `convertKeysToCamel`・`convertKeysToSnake`・`attachGlobalKeydown`・`useSelectionGuard`・
  `unformat`・`formatWithCommas`・`unformatYMD`・`parseYMD`・`formatYMD`・`openModalDialog` 系

> **含意**：**対比のとき「設計書に無いから実装も無いはず」と推論してはならない。** 実装が先行している。

---

## 1. フロント：`Front-end/src/common/`

| ファイル | 行数 | 役割 |
|---|---|---|
| **`R60Common.ts`** | **1660** | **共通関数の唯一真源**（60 関数） |
| `http-common.ts` | 77 | **axios の単一窓口**（要求/応答インターセプタ。Blob→JSON 変換） |
| `utils.ts` | — | 補助（`export` は 1）【未確認：中身の詳細】 |
| `Halfwidth.ts` | — | `v-halfwidth` ディレクティブ（全角→半角の入力制御） |
| `EventBus.ts` | — | 画面間のイベント通知 |
| `UseSelectDialog.ts` / `SelectDialogSingleton.ts` | — | 支援画面（コード選択）ダイアログの共通制御 |

### 1.1 `R60Common.ts` の 60 関数（【実測】名前の全リスト）

**入力チェック系**

```
subCheckNumber / subCheckTelNo / subCheckAlphabetNumber / subCheckKanaByte / subCheckHalfKana
subCheckNumeric / subCheckHalfKanaAlphabetNumber / subCheckHalfKanaAlphabetNumberSign
byteCheck / checkHankaku / checkSpecialHankaku / chkHanEngNum2 / chkHanEngNum3 / chkHanEngNumMail
ckDate / ckDateYYYYMM / formatDateYYYYMM
kinsiStrCheck / kinsiMojiCheck / quotCheck            ← 禁止文字・引用符チェック
subCheckKgoCd
```

**入力制御・キーボード**

```
keyCodeCheck / onKeyDown / attachGlobalKeydown / useSelectionGuard   ← 全体装着される（main.ts）
```

**二度押し防止（★呼び出し順の要）**

```
subCheckSubmit / subSetSubmitFlg / subInitSubmitFlg
```

**ボタン活性制御**

```
subListBtnDisabled / subBtnDeleteDisabled / subBtnRegistDisabled / subDistKojo
subBtnDeleteDisabledCmp / subBtnRegistDisabledCmp / subDistKojoCmp
subKgnBtnEnabled
```

**画面制御・状態**

```
resetErrors / initReset / resetSortIcon / spreadResults / subResultListInit / subDataInit
showMessageDialog / showErrorAndFocus / focusInvalid
subDownload / subFileUpload / subOpenHelpWindow
```

**モーダル（支援画面）**

```
openModalDialog / openModalDialogSim / openModalDialogReturnsArray
```

**整形・変換**

```
snakeToCamel / camelToSnake / convertKeysToCamel / convertKeysToSnake
unformat / formatWithCommas / unformatYMD / parseYMD / formatYMD
```

**定数**：`export const pgIds1` / `pgIds2`（**支援画面の画面 ID 表**。`openModalDialog` に渡す `pgId` の出所）。

> ★ **骨架規則 03 §3 が挙げる 13 関数はすべて実在する**（【実測】）：
> `showMessageDialog` / `subCheckSubmit` / `subSetSubmitFlg` / `subInitSubmitFlg` / `spreadResults` /
> `resetErrors` / `subCheckAlphabetNumber` / `showErrorAndFocus` / `subDownload` / `subListBtnDisabled` /
> `subResultListInit` / `initReset` / `resetSortIcon`。
> **→ 規則 03 §3 のマッピング表は実装と整合している。**（`showErrorAndFocus` は
> `export async function` として 1509 行目にある。）

### 1.2 呼び出し順の定型（【実測】`main.ts` と各 view の構造から）

```
① subCheckSubmit()          … 二度押し中なら即 return
② resetErrors() / initReset() / resetSortIcon()   … 前回の残留を消す
③ 入力チェック（subCheckXxx → showErrorAndFocus）
④ subSetSubmitFlg()         … ロック ON
⑤ API 呼出（service 経由）
⑥ subResultListInit() / subListBtnDisabled()      … 成功時の後処理
⑦ finally { subInitSubmitFlg() }                  … 例外時も必ずロック解除
```

> **骨架規則 03 §3 の「呼び出し順の典型」と一致する**（規則：`subCheckSubmit` → `resetErrors`/`initReset`/
> `resetSortIcon` → `subSetSubmitFlg` → API → `subResultListInit`/`subListBtnDisabled` →
> `subInitSubmitFlg`(finally)）。**→ 規則は実装に基づいて書かれている。**

---

## 2. バック：`api/fastapi_oracle_pjt/app/utils/`（35 ファイル）

**【実測】`utils/*.py` は 35 本。`^class` は 0、`^def` は 19（`r60util.py` 単体）。**
側から機能別に分かれている：

| 分類 | ファイル |
|---|---|
| **総合ユーティリティ** | **`r60util.py`（386 行・19 関数）** — §2.1 |
| 定数 | **`r60const.py`（175 行）** — `R60Const` クラスに **ACTION_ID** 等の定数群。§2.2 |
| チェック | `r60check_utility.py`（**設計書 242 行**）・`r60string_util.py`（118）・`r60number_utility.py`（47） |
| CSV | `r60csv_util.py`（123）・`r60csv_download.py` |
| SQL 補助 | `r60get_select_column.py` / `r60yok_cd_tbl_access.py` |
| 権限 | `r60authority_mng_bean.py` |
| 排他・被参照 | `r60referred_chk_bean.py`（**被参照チェック**） |
| 緊急配信 | `r60emergency_send_ctl_bean.py` / `r60emergency_send_ctl_pkg.py` |
| 採番 | `r60get_plc_uki_knr_seq_pkg.py` |
| シミュレーション | `r60sim_util.py`（**設計書 318 行**＝最重量） |
| **業務別パッケージ** | `r60l270b.py` / `r60l550b_*.py` / `r60l610b.py` / `r60l620b.py` / `r60l630b.py` / `r60l640b.py` / `r60l790b.py` / `r60l820b.py` / `r60l830b.py` / `r60l860b.py` / `r60l870b.py` / `r60l880b.py` / `r60l890b.py` / `r60l900b.py` / `r60l910b.py` / `r60l930b.py` / `r60l940b.py` / `r60l960b.py` （**18 本**） |

> **【推測】** `r60l<数字>b.py` は**現行 PL/SQL のパッケージを 1 対 1 で移植したもの**。
> `pkg` が付くもの（`r60l550b_pkg.py`）と `bean` が付くもの（`r60l550b_bean.py`）で役割が分かれる。
> **業務固有の判定（排他・被参照・重複など）はここに閉じている可能性が高い。**
> **【未確認】** 中身は読んでいない。**使う前に必ず開くこと。**

### 2.1 `r60util.py` — 19 関数（【実測】名前の全リスト）

```
write_log / generate_presigned_url / get_s3_root_folder / get_s3_csv_folder / create_csv_s3_key
get_s3_csv_object_stream / pkg_proc / get_properties / chk_onl_flg / get_last_day / to_date
get_wday / chk_sim_request / get_default_value / get_title_color / get_yuso_hin_kbn
get_exception_stack_trace_info / get_cod_mes_info / get_system_date
```

| 関数 | 役割【推測】 |
|---|---|
| `write_log` | ログ出力 |
| `generate_presigned_url` / `get_s3_*` / `create_csv_s3_key` / `get_s3_csv_object_stream` | **S3**（CSV ダウンロード・アップロード） |
| `pkg_proc` | **PL/SQL パッケージ呼び出し**の入口 |
| `get_properties` | 設定値取得 |
| `chk_onl_flg` | **オンライン可否フラグのチェック**（`R60_SYSTEM_TBL.ONL_SIY_KHI_FLG` 系） |
| `get_last_day` / `get_wday` / `to_date` / `get_system_date` | 日付（**月末日**・**曜日**・変換・**システム日付**） |
| `chk_sim_request` | シミュレーション要求の判定 |
| `get_default_value` | 既定値取得 |
| `get_title_color` | **画面タイトルの背景色**（設計書の「背景色項目」に対応） |
| `get_yuso_hin_kbn` | 輸送品区分（業務） |
| `get_cod_mes_info` | **メッセージ管理情報の取得**（`R60_CODE_MES_M_TBL`） |
| `get_exception_stack_trace_info` | 例外スタックトレース整形 |

> ✅ **骨架 `CLAUDE.md` §2 禁①・規則 00 §8 は「`r60util.py` **31 クラス**」と書くが、実物は
> `^class` が 0・`^def` が 19 である。**（【差異】D-4 → [08-deviations.md](08-deviations.md)）
> **「31 クラス」は現行 Java/PL/SQL 側のクラス数を指していると推測される**（【推測】）。

### 2.2 `r60const.py` — `R60Const` クラスの ACTION_ID（★API イベント名の語彙）

**【実測】** `ACTION_ID_*` の形で定数化されている（該当は 20 個以上）。**API の「イベント」名はここが語彙の出所。**

```
init / head / check / condition / search / detail / copy / duplicate / new / regist / modify
delete / dialog / back / end / makdrop / childresult / foot / add / childregist
```

> **画面を 1 枚作るとき、API のイベント名はこの語彙から選ぶ。**
> 例：R60Login は `init` と `login`（`login` はここに無い固有イベント）。

---

## 3. バック：その他の層（【実測】）

| ディレクトリ | 本数 | 中身 |
|---|---|---|
| `app/common/` | 5 | **業務例外クラス群**：`r60_online_exception.py`（`OnlineException(Exception)`）・`r60_online_error.py`・`r60_session_error.py`・`r60_system_error.py`・`models/error_models.py` |
| `app/models/` | 2 | `models.py` / `r60_sim_info_model.py` |
| `app/auth/` | 2 | `auth.py`（`verify_token`）— **★実質未使用**（[02](02-architecture.md) §3.2） |
| `app/script/` | 2 | `sqs_connect.py` / `sqs_receiver.py`（**SQS**＝非同期連携） |

> **【推測】** `common/` の例外クラスは「オンラインエラー」「セッションエラー」「システムエラー」の
> **3 系統の異常**を表す。設計書の `E-xxx`（エラー）に相当する層。

---

## 4. `BaseCamelModel` の実物（★差異の中心）

**【実測】`app/routers/R60LoginController.py:23-30`** 逐語：

```python
class BaseCamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
        extra="ignore",
    )
```

| 論点 | 骨架規則 03 §2 | 実物 | 差異 |
|---|---|---|---|
| 定義場所 | 共有基類（1 箇所） | **54 の router ファイルに各 1 回**（55 本のうち `R60CommonController.py` だけ持たない） | **【差異】D-2** |
| `extra` の値 | **`'forbid'`** | **`"ignore"`** | **【差異】D-1** |
| 派生モデルでの再定義 | 「**再定義しない**」 | **314 箇所で再定義**（うち 251 は `json_schema_extra` の付与） | **【差異】D-6** |

- 【実測】`extra=` の分布：**`extra="ignore"` 128 回** ／ `extra="allow"` 1 回。
  **`extra="forbid"` は 0 回。**
- 【実測】`class X(BaseCamelModel)` は **1090 個**（56 router 合計）。
- **Pydantic v2 は親子の `model_config` をマージする**ため、派生側の再定義（`json_schema_extra` のみ）
  でも `alias_generator` 等は失われない。**ただし「再定義しない」という規則の文言とは異なる。**

> **★実務上の含意**：`extra="ignore"` である以上、**定義外の項目を送っても 422 にならず黙って落ちる**。
> 骨架規則どおり `'forbid'` で作ると、**人間版では通る要求が 422 で落ちる**。
> **対比の前にこの 1 点を必ず揃えること。**

---

## 5. 部品を使うときの順序（実務手順）

1. **設計書の `画面項目内容`** を読む（`種別(属性)` 列が「テキストボックス / ドロップダウン / ボタン…」）。
2. → **`共通部品利用ガイドライン` の該当シート**を開く（27 シートのうち 1 つ）。
3. → **`R60Common.ts` の該当関数**を確認する（§1.1 の分類から引く）。
4. → **`機能定義書(Common)`** で引数の意味と戻り値を確認する
   （`R60Common_TS` は `機能概要`／引数／返却値 の 3 段で書かれている）。
5. **自作が要るのは、ここまでのどれにも当たらない業務ロジックだけ。**

---

## 6. 出典

- 【実測】`Front-end/src/common/*`（`R60Common.ts` の export 数をコマンドで計数）、`Front-end/src/main.ts`
- 【実測】`api/fastapi_oracle_pjt/app/{utils,common,models,auth,script,routers}/*`
- 【文書】`doc/02_INPUT/50.設計書/2-041-F_機能定義書(Common)_{R60Common_TS,R60Common_python,R60Util_python}_v1.0.xlsx`
- 【実測】設計書の関数名索引：`py -3 -m tools.legacy <同書> --sheet R60Common.ts | grep 'B:関数名'`（→ 53 件）
- **★未読**：`R60Util_python` 設計書には **`.env` というシートがある**（13 行）。**環境設定値の定義であるため、
  memory の掟に従って開いていない。** 必要な場合は人が確認する。
- 骨架側：`CLAUDE.md` §2 禁①、`.claude/rules/00-project-global.md` §8、`.claude/rules/03-design-coding.md` §2〜§3

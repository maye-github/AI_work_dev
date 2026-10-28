---
id: RULE-003
type: design-coding
req_ids: [SPEC-FR-2, SPEC-C-TECH-1, SPEC-C-TECH-2, SPEC-C-TECH-4]
status: draft
sensitivity: internal
owner: AI-SE
version: 0.1.0
---

# 設計・製造 実装細則（BaseCamelModel / R60Common 映射 / snake-camel 分区 / SQL 白名单）

## 1. 適用範囲
**Summary**: Vue3 + `<script setup>` + TypeScript + PrimeVue（フロント）と FastAPI + Pydantic + SQLAlchemy + oracledb Thin（バック）のスタックにおける、製造工程の 4 つの固定実装細則を規定する。
**適用条件**: 本案 §2（`BaseCamelModel`）・§4（命名分区）・§5（SQL 白名单）は**全案件共通**。§3（R60Common.ts 映射表）は **`migration` 案件に限る**（再利用すべき既存資産がある場合のみ）。`greenfield` 案件では §3 を適用せず、共通部品は工程 04/05 で新規定義する（参照: spec.md Constraints Technical 1/2/4）。
- 参照: 落地篇 PPT S9-S17（製造工程）/ SKILL.md Step 3-4

---

## 2. `BaseCamelModel` の 4 行 `model_config` 固定写法（Pydantic v2）
**Summary**: API 入出力の snake↔camel 変換は `BaseCamelModel` の `model_config` **4 行固定**で行う。
下のコードは**骨架の推奨実装**（`greenfield` はこれをそのまま新規定義してよい）。
**既に `BaseCamelModel` を持つ案件（`migration`）では、その 4 行を変えない**——
禁止の実体は案件プロファイル（`docs/01_context/case-profile-<案件>.yaml` §2 禁②）にある。
```python
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BaseCamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,   # snake_case → camelCase を自動別名生成
        populate_by_name=True,      # 別名(camel)/原名(snake)どちらでも受入可
        serialize_by_alias=True,    # 応答は別名(camel)で出力（TS 接口層期待形に一致）
        extra='forbid',             # 未定義項目は 422 で拒否（余剰入力の混入防止）
    )
```
- 期待挙動: 要求(camel) → `populate_by_name` で snake 字段へ束縛 → 応答は `serialize_by_alias` で camel へ復元。
- `extra='forbid'` により、定義外の入力は静黙無視されず 422 で顕在化する（改定・項目追加の検知）。
- 派生モデルでは `model_config` を**再定義しない**（継承で 4 行を継承）。

---

## 3. `R60Common.ts` 関数呼び出し 签名映射表（**`migration` 案件に限る**）
**Summary**: **本節は `build_mode: migration` かつ案件プロファイルが再利用資産を宣言している場合にのみ適用する。** 製造では既存 R60Common.ts の関数を**そのまま呼び出す**。新規類似関数の自作は禁止（禁止事項①）。
**`greenfield` の場合**: 呼び出し先の既存関数が存在しないため、本表は適用しない。必要な共通部品は工程 04（框架構築）で一覧化し、工程 05 で本案件の資産として新規定義する。定義後の改変禁止は、その新規定義した資産に対して働く。
下記は呼び出し順で特に重要な **13 関数**の用途・使用場面を固定する。

> **単一ソース（NFR-1）**: 代表関数の**全リスト（16 関数）は `.claude/skills/code-from-design-trans-cosmos-ai/SKILL.md` §3.5 が唯一の定義**である。
> 本表はそのうち**呼び出し順で特に重要な 13 件を抜粋**したもの。関数を追加・変更する場合は
> **SKILL.md §3.5 のみを更新**し、本表は「抜粋の範囲を変えるときだけ」触る（両方に別々の定義を書かない）。
> `R60Common.ts` 全体の関数数は 54（`CLAUDE.md` §2 禁①）。
| # | 関数名 | 用途（機能） | 使用場面 | 備考 |
|---|--------|--------------|----------|------|
| 1 | `showMessageDialog` | メッセージダイアログ表示 | エラー/情報通知の全般 | ボタンイベント内から呼ぶ |
| 2 | `subCheckSubmit` | 二度押し防止チェック | 全ボタンイベントの先頭 | 戻り値で処理続行可否判定 |
| 3 | `subSetSubmitFlg` | 二度押し防止フラグ ON | API 呼出直前 | 呼び出し中ロック |
| 4 | `subInitSubmitFlg` | 二度押し防止フラグ OFF | API 呼出 finally ブロック | 例外時も必ず解放 |
| 5 | `spreadResults` | 条件/結果領域のスプレッド表示 | 条件部⇔結果部の toggle 関数 | レイアウト切替 |
| 6 | `resetErrors` | エラー状態リセット | 検索実行の前 | 前回エラーの消去 |
| 7 | `subCheckAlphabetNumber` | 半角英数字チェック | コード項目（例: エリアコード）入力チェック | NG 時は ⑧で通知 |
| 8 | `showErrorAndFocus` | エラー表示 + フォーカス移動 | 入力チェック NG 時 | 項目特定してフォーカス |
| 9 | `subDownload` | CSV ファイルダウンロード | doDownload 関数（BLOB 応答は JSON 変換経由） | ボタン活性条件に注意 |
| 10 | `subListBtnDisabled` | 一覧画面ボタン活性/非活性制御 | 検索成功後 | 権限・自工/他工フラグと組合せ |
| 11 | `subResultListInit` | 結果一覧初期化 | 検索成功後 | 明細テーブル再構築 |
| 12 | `initReset` | スクロール/ページャ初期化 | 検索実行の前 | 先頭頁へ戻す |
| 13 | `resetSortIcon` | ソートアイコン初期化 | 検索実行の前 | 並び順表示のリセット |
- 呼び出し順の典型: `subCheckSubmit` → `resetErrors`/`initReset`/`resetSortIcon` → `subSetSubmitFlg` → API → `subResultListInit`/`subListBtnDisabled` → `subInitSubmitFlg`(finally)。

---

## 4. snake / camel 命名分区規則（gate5 判定）
**Summary**: 命名は**区層で厳格に分離**する。**YAML/MD 定義層と Python は snake_case**、**TS/接口層は camelCase**。定義層に camel が混入（例: `cmpCd`）すると `trace_check` gate5 で打回。本ルールは spec.md Constraints Technical 1/2 の I-ID 定義と TS 接口契約の橋渡しを保証する。
| # | snake_case（Python/定義層） | camelCase（TS/接口層） | 日本語 | 分区境界 |
|---|-----------------------------|-------------------------|--------|----------|
| 1 | `cmp_cd` | `cmpCd` | 会社コード | YAML/Python ⇔ TS |
| 2 | `jig_cd` | `jigCd` | 事業場コード | YAML/Python ⇔ TS |
| 3 | `ara_cd` | `araCd` | エリアコード | YAML/Python ⇔ TS |
| 4 | `ara_nm` | `araNm` | エリア名 | YAML/Python ⇔ TS |
| 5 | `ksn_dat` | `ksnDat` | 更新日時（排他） | YAML/Python ⇔ TS |
| 6 | `rev_no` | `revNo` | 改訂番号（排他） | YAML/Python ⇔ TS |
| 7 | `send_sts` | `sendSts` | 送信ステータス | YAML/Python ⇔ TS |
| 8 | `del_flg` | `delFlg` | 削除フラグ | YAML/Python ⇔ TS |
| 9 | `reg_sts` | `regSts` | 登録ステータス | YAML/Python ⇔ TS |
| 10 | `jig_hyj_seq` | `jigHyjSeq` | 事業場表示順 | YAML/Python ⇔ TS |

### 4.1 適用ルール
- **YAML/MD 定義層**: 字段定義は snake_case。front-matter 7 字段も全て snake_case。
- **Python（routers / models / r60util）**: 変数・DB カラム束縛は snake_case。
- **TS / 接口層（Service / Vue）**: API 字段・型定義は camelCase（`BaseCamelModel` が変換を担保）。
- **混写禁止**: 定義層に camel（`cmpCd`）が現れた場合、または TS 層に snake（`cmp_cd`）が現れた場合は gate5 で **打回**。
- 境界の唯一の変換点は `BaseCamelModel` の `alias_generator=to_camel` とする（手書き変換コードの散在禁止）。

---

## 5. SQL 白名单注入防護（ALLOWED_SORT_FIELDS）
**Summary**: ソート項目をリクエストから動的に受ける場合、SQL 断片へ**直接文字列連結してはならない**。許可項目を `ALLOWED_SORT_FIELDS` の**白名单**で限定し、白名单外は固定ソート `JIG_HYJ_SEQ` へフォールバックする。
```python
ALLOWED_SORT_FIELDS = {"CMP_CD", "JIG_CD", "ARA_CD"}


def build_order_by(sort_field: str | None) -> str:
    # 白名单ヒット時のみ項目名を採用（識別子のため bind 不可、白名单で担保）
    if sort_field and sort_field.upper() in ALLOWED_SORT_FIELDS:
        return f"ORDER BY {sort_field.upper()}, ROWID"
    # 白名单外・未指定は固定ソートへフォールバック（順序安定 + ROWID で一意化）
    return "ORDER BY JIG_HYJ_SEQ, ROWID"
```
### 5.1 規約
- 許可ソート項目は `CMP_CD` / `JIG_CD` / `ARA_CD` の 3 項目のみ。追加は設計変更（CR）を要する。
- それ以外（値の不正・未指定含む）は `JIG_HYJ_SEQ` 昇順 + `ROWID` の固定ソートにフォールバック。
- 値のバインドには必ずプレースホルダ（`:cmp_cd` 等）を用い、f-string 連結で値そのものを埋め込まない。
- ページングは原則 `ROWID` 方式（OFFSET-FETCH は doc/01 の報告書に基づく必要時のみ）。参照: spec.md Constraints Technical 2。
- 動的列は `sort_field` のみを白名单化対象とし、他は固定列リストで発行する。

---

## 6. 製造工程チェックリスト（Claude Code 実行前後）
- [ ] `BaseCamelModel` の 4 行 `model_config` に改変がない
- [ ] R60Common.ts / r60util.py を改変していない（並行新版を作っていない）
- [ ] 呼び出す共通関数は §3 のマッピング表に準拠している
- [ ] snake/camel の分区を守っている（定義層 snake・接口層 camel）
- [ ] ソート指定は `ALLOWED_SORT_FIELDS` 白名单経由、それ以外は `JIG_HYJ_SEQ` 固定
- [ ] 製造後に `py -3 -m tools.trace_check --strict` を実行し `Exit 0`

---

## 7. 決定性（冪等性）と人による二重確認（社内実績 SDS2 の取入）
**Summary**: 社内実績（SDS2）が明示した 4 つの制約を製造工程の規約に落とす。
**出所は要件源 PPT ではない**（登録: `ppt-deviation-register.md` §2）。
詳細と原典の逐語は `docs/90_knowledge/internal/sds2-lessons.md` §1 が唯一の定義。

### 7.1 生成・再実行は冪等でなければならない
- **同じ設計入力（D/L/E）から生成されるコードと差分は、何度生成しても同一**であること。
- 非冪等になりやすい箇所は**明示して固定する**:
  - 現在時刻・乱数・UUID・セッション ID を出力へ埋め込まない（必要なら引数として注入する）。
  - `set` / `dict` の反復順に依存した出力を作らない（順序を明示的にソートする）。
  - 生成し直すたびにファイル全体の差分が出る整形（改行コード・末尾空白・インデント幅）を混入させない。
- **根拠（SDS2 逐語・要旨）**: 「冪等性が担保されておらず、同じ指示でも同様のテストコードが生成されるとは限らず、
  一貫性の保証が難しい」。**生成物が毎回変わるなら、レビューと差分追跡が成立しない。**

### 7.2 複雑な機能は人による二重確認を必須とする
- 「複雑」の判定基準（いずれか 1 つでも該当）:
  分岐が 3 段以上 / 状態遷移を伴う / 排他制御を伴う / 外部連携（API・バッチ・メール）を伴う /
  DB の複数表をまたぐ更新。
- 該当する製造物は、**設計者以外の人が diff を読む**（红线③の設計評審・コードレビューを省略できない）。
- **根拠（SDS2 逐語・要旨）**: 「AI のハルシネーション：複雑な機能の場合チェック漏れが発生する可能性があり、
  **最終的には人の目による再確認（ダブルチェック）が必要**」。

### 7.3 図表に依存する仕様は、人がテキスト化してから製造へ回す
- 画像（ピクチャ）や Excel 内の図表に依存する仕様は、**AI が正確に読み取れない場合がある**。
- 該当箇所は製造前に、人が**機読源（`.md` / `.yaml`）へテキスト化**する。
  **図のまま製造工程へ投入しない。**
- これは規則 00 §11（機読源が唯一真源）と同じ方向の規約である。
- **根拠（SDS2 逐語・要旨）**: 「インプットの制限：設計書のフォーマットに依存し、
  画像や Excel 内の図表などを正確に読み取れない場合がある」。

### 7.4 複雑な機能は分割して生成する（入力上限とコスト）
- 1 回の入力には**トークン上限**がある。複雑な機能を一括投入すると**生成失敗が多発**する。
- 分割の単位は**画面または API エンドポイント**とする（1 画面 1 生成を既定とする）。
- 生成がまったく利用できない結果を返した場合、**同じプロンプトを再投入しない**。
  入力を分割するか、参照ソース（既存の類似実装）を明示してから再実行する。
- **根拠（SDS2 逐語・要旨）**: 「Token 制限で、一括生成できない」「インプット情報多過ぎで、生成失敗も多発」
  「マトリクス複雑の場合、生成失敗可能性がある」。

### 7.5 §6 チェックリストへの追加 4 項
- [ ] 生成物に現在時刻・乱数・順序不定の反復が混入していない（§7.1）
- [ ] 複雑判定に該当する製造物は、設計者以外が diff を読んだ（§7.2）
- [ ] 図表に依存する仕様は、製造前に機読源へテキスト化された（§7.3）
- [ ] 複雑な機能は分割して生成した（1 画面 1 生成が既定）（§7.4）

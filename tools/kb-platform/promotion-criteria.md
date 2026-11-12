# 案件知識 → 会社級への昇格判定（結案時）

> この 1 枚が**判定の唯一の入口**である。手順の実行は `tools.kb_promote`、規則の運用は
> `kb-policy.md` §4〜§6。ここは「**どれを上げてよいか**」を人が判断するためのチェックリスト。

## 1. 原則（1 文）

**「別の顧客・別のシステムへ持って行っても成立するか。」**
成立する → 会社級へ昇格。成立しない → 案件級に残す。

## 2. 判定チェックリスト（5 項・すべて満たすものだけ昇格）

| # | 判定 | 満たさない例（案件級に残す） |
|---|---|---|
| 1 | **顧客非依存**：顧客名・システム名・画面名・表名・関数名・行番号を含まない | `R60_AREA_M_TBL` の列一覧、`R60Common.ts` の関数一覧 |
| 2 | **出所がある**：どの原本・どの節から来たかを言える（`source_files` / `source_project`） | 「たぶんこう運用している」 |
| 3 | **実績がある**：**2 案件目で使われた**、または使う予定が具体的にある | 1 案件でしか使っていない独自手順 |
| 4 | **形が再利用できる**：雛形・規約・用語のいずれかとして切り出せる | ある画面の業務フロー固有の分岐 |
| 5 | **匿名化済み**：`tools.kb_promote check <file>` が 0 件 | 実在の顧客名・人名・接続情報が残っている |

> **1 案件目で上げない**（`kb-policy.md` §5）。1 案件で「通用する」と思ったものが
> 2 案件目で通用しないことは多い。実績の無いまま上げると、会社級が「各案件の置き場」になる。

## 3. 何を昇格するか（3 種類）

| 種類 | 何を残すか | 何を捨てるか | コマンド |
|---|---|---|---|
| **雛形（template）** | 見出し・表の見出し行・リスト記号・コードフェンスの言語 | 段落・表の本体・コードの中身 → `<…>` | `kb_promote skeleton` |
| **用語（glossary）** | 2 案件目でも通じる語と定義 | その案件だけの略語 | `kb_promote init-glossary` → 結案時に選別 |
| **規約（standard）** | 条文（〜とする／〜しない） | 案件固有の値・例外 | `kb_promote candidates --types standard` |

## 4. 結案時の手順（人が実行する）

```bash
# 0. レビュー表を作る（読むだけ。建議＋理由＋勾选欄。移送はしない）
py -3 -m tools.kb_promote review --project <P> --as <人>
#    → reports/promote-review-<P>.md
#    §0 会社級に今あるもの（doc_type 別）／§1 候補と建議／§3 脱敏の残件
#    人が「勾选」欄に x を入れる → 勾选した行だけが計画に載る
py -3 -m tools.kb_promote review --project <P> --as <人> --plan-out reports/promote-plan-<P>.yaml

# 1. 候補を出す（読むだけ。判定はしない）
py -3 -m tools.kb_promote candidates --project <P> --types template,glossary,standard

# 2. 匿名化の下書き（原本は書き換えない。出力は reports/ の外）
py -3 -m tools.kb_promote draft <対象.md>

# 3. 匿名化体检（0 件になるまで直す）
py -3 -m tools.kb_promote check <file>

# 4. 計画 YAML を書く（file / to / doc_id / source_project）
py -3 -m tools.kb_promote plan --from-plan plan.yaml      # 検証だけ

# 5. 移送（会社の責任者のみ）
py -3 -m tools.kb_promote apply --from-plan plan.yaml --by <人> --apply
py -3 -m tools.kb_local ingest --prune

# 6. 結案（その案件の PM のみ）
py -3 -m tools.kb_promote close --project <P> --apply
```

**`plan` で 1 件でも不備があれば 1 件も動かない。** 移送と結案は書き込み直前に `kb_acl` で権限を検査する。

## 5. 結案記録（`CLOSED.md`）に残るもの

| 人が確認する 4 項 | 機械がやった 4 項 |
|---|---|
| 結案評議会 | 移送（件数） |
| 候補抽出 | `scope` 変更（project → company） |
| 匿名化 | `source_project` 記録 |
| KB 責任人承認 | 読み取り専用の印 |

**読み取り専用は OS 権限ではなく「印」。** 再開するときは削除せず、理由と日付を追記する。

## 6. 昇格しなかったものの扱い

- **案件級に残す**（消さない）。同じ案件を再開したときの根拠になる。
- **形だけ残す**（雛形化）ことはできる。中身は案件固有のまま。
- **捨ててよいのは**、原本（`sources/`）から再生成できる派生物だけ。原本は消さない。

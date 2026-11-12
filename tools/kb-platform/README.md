# tools/kb-platform — 知識庫の入口（この 1 枚から読む）

> 実装は上流 `D:\AI_platform\kb-platform` の写し（`VENDORED.md`）。**我々の差分は `tools/kb_local/` に置く**。
> このファイルは「どこに何があり、どう使うか」だけを示す。規則の本文は `kb-policy.md`。

## 1. 置き場所

```
tools/kb-platform/
├── repo/                    … 知識の実体（索引の対象）
│   ├── company/             … 会社級（27 篇）
│   │   ├── templates/       … 雛形（基本設計 14 節・詳細設計・用語集）
│   │   ├── patterns/        … パターン（画面・交付・審査・開発・howto）
│   │   ├── standards/       … 規約（コーディング・要求・テスト・内部実績）
│   │   └── glossary/        … 用語
│   ├── projects/            … 案件級
│   │   └── <P-ID>/
│   │       ├── sources/     … **人が原本を置く**（AI は生成しない・編集しない）
│   │       ├── extracted/   … 原本からの機械抽出（`status: draft`）
│   │       ├── knowledge/   … AI が整理した案件知識（5 節の型・人の確認後 open）
│   │       ├── modules/ standards/ screens/ review/ playbooks/ …
│   │       └── sources/README.md
│   └── eval/golden.yaml     … 検索品質の評価問題
├── data/kb.sqlite3          … 索引（`ingest` で再生成できる派生物）
├── node-map.yaml            … **節点 → 必読条目（唯一真源）**
├── constraints.yaml         … **知識が要求する「形」の機械検査（節点 2/3/5）**
├── promotion-criteria.md    … **結案時の昇格判定（唯一の入口）**
├── knowledge-template.md    … `knowledge/` の 1 篇の型
├── knowledge_exempt.txt     … 型検査の遡及免除（理由必須）
├── kb-policy.md             … 運用規則（入れるもの・権限・昇格）
├── owners.yaml              … 誰がどの範囲を更新できるか
├── company-README.md / projects-README.md … 各層の説明
└── VENDORED.md / UPSTREAM-SYNC.md        … 上流との関係
```

## 2. 使われ方（3 つだけ）

### ① 節点で自動的に引く（**AI に探させない**）

```bash
py -3 -m tools.kb_local node-brief --node 5
```

`node-map.yaml` の必読条目を**抜粋付きで出力**する。コーチはこれをそのまま実行体のプロンプトに貼り、
承認前に次で検査する（必読条目が `kb_refs` に無ければ不合格）。

```bash
# ① 必読条目を引いたか
py -3 -m tools.kb_refs check <承認版> --node N --require-node

# ② 使用記録（doc_id / 参照した節 / 反映先）が実在の節を指しているか
py -3 -m tools.kb_refs check <承認版> --node N --require-usage

# ③ 知識が要求する形になっているか（節点 2/3/5）
py -3 -m tools.kb_local check-constraints --node N <承認版|コードディレクトリ>
#   節点2/3 = 承認版の .md ／ 節点5 = コードのディレクトリ
```

- **①** は「引いたか」、**②** は「その節が原文に実在するか」、**③** は「成果物が知識の型どおりか」を見る。
- 3 つとも承認前の門（`SKILL.md` §5）で走る。**内容の正しさは見ない**——そこは人が読む。

### ② 新しい案件を入れる（原本 → 知識）

```bash
py -3 -m tools.kb_local project-init --id P-XXX-001 --name "案件名" --by <PM>
#   sources/ に原本を置く（xlsx/docx/pdf/md/txt）
py -3 -m tools.kb_local import --scan --project P-XXX-001 --by <PM>   # → extracted/（draft）
#   人が原本と突き合わせて draft → open
#   AI が knowledge-template.md の型で knowledge/ を書く
py -3 -m tools.kb_local check-knowledge
py -3 -m tools.kb_local lint && py -3 -m tools.kb_local ingest --prune
```

### ③ 結案時に会社級へ昇格する

```bash
py -3 -m tools.kb_promote candidates --project <P> --types template,glossary,standard
py -3 -m tools.kb_promote check <file>     # 匿名化 0 件まで
py -3 -m tools.kb_promote plan --from-plan plan.yaml
py -3 -m tools.kb_promote apply --from-plan plan.yaml --by <人> --apply
py -3 -m tools.kb_promote close --project <P> --apply
```

判定基準は `promotion-criteria.md`（5 項チェック）。**1 案件目では上げない。**

## 3. 日常の検査

```bash
py -3 -m tools.kb_local lint            # 字段・doc_type・scope
py -3 -m tools.kb_local check-knowledge # knowledge/ の型と出典
py -3 -m tools.kb_local ingest --prune  # 索引の更新
py -3 -m tools.kb_local eval            # 検索品質（recall@5 ≥ 0.85）
```

## 4. 触ってはいけないもの

- `repo/company/` の上流デモ 3 篇（`source_project: upstream-demo`）— `company-README.md` §2
- `repo/projects/<P-ID>/` の `generated_by: tools.kb_migrate.py` が付いた `.md` — 再生成で上書きされる
- `VENDORED.md` が「上流と逐字一致」と定めたコード — 差分は `tools/kb_local/` に置く

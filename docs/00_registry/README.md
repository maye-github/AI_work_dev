---
id: REGISTRY-README
type: knowledge
req_ids: []
status: draft
sensitivity: internal
owner: AI-SE
version: 1.0.0
---

# このディレクトリの読み方（ID 台帳まわり）

「台帳（台帳＝登記簿）」とは、**条目順に記録した原簿**のことである。
叙述文ではなく、**1 行 1 件**で積み上がる。このディレクトリには台帳が 4 冊ある。

| ファイル | 何の台帳か | 書き手 | 読むとき |
|---|---|---|---|
| `ids.yml` | **ID 台帳**。R/F/I/D/L/E/TC/IT/CR/BUG/Q の唯一の発号口 | `py -3 -m tools.registry`（**唯一の書込み口**） | 「この番号は発号済みか」を確かめるとき |
| `traceability.yml` | **追跡行列**（要件→機能→項目→設計→ロジック→エラー→テスト） | `py -3 -m tools.registry trace --write`（**生成物。手で編集しない**） | 影響範囲を引くとき（`tools.impact` が読む） |
| `glossary.yml` | **用語辞書**（中日英）。対外 Excel の用語源 | 人が追記 | 用語を決めるとき |
| `ingest-manifest.yml` | **取入マニフェスト**（旧案件のどこを読むか） | 人が記入 | 旧案件を取り込むとき |

## 3 つの性質（なぜ手で触らないか）

1. **書込み口が 1 つ**。`ids.yml` を直接編集すると、連番・親リンク・`used_by` の整合が崩れ、
   以降の `verify` が通らなくなる。
2. **只増不改**。番号は消さない・再利用しない。無効化は `status: void` で明示する。
3. **権威記録**。「発号したか」はこの台帳で決まる。チャットや記憶ではない。

## ただし、台帳は現実より古くなり得る

旧案件（R60）は Excel の台帳を人手で維持しており、**実装から乖離していた**。
その実測と教訓は `docs/95_legacy/r60/07-traceability.md` にある（「台帳に無いから実装も無い、と推論してはならない」）。

だから本骨架は、台帳を信じるのではなく**突き合わせる**：

```bash
py -3 -m tools.registry verify      # 台帳自身の整合（連番・親リンク・used_by の実在）
py -3 -m tools.registry trace       # 台帳と追跡行列のずれ
py -3 -m tools.trace_check --strict # 6 道の門（gate1 野号 / gate2 閉包 / gate3 front-matter …）
```

## よくある誤解

- **「台帳に無い番号を使った」＝野号**。成果物に書く前に `registry alloc` で発号する。
- **「台帳を直せば辻褄が合う」は誤り**。直すのは成果物側か、`CR` を起票して上流から。
- **`traceability.yml` を手で並べ替えない**。次の `trace --write` で上書きされる。

gen_formal — 機読成果物 → 日文正式 Excel の二重化ツール
=========================================================

【二つの入口】

  (1) gen_excel — 列定義の検証（既定は dry-run）
      実行:
        py -3 -m tools.gen_formal.gen_excel --dry-run --module R-101
      出力:
        [gen_formal] field_count=56 | output_columns=ara_cmp_list_56items.csv
        reports/gen_formal_columns_R101.json
      I-ID の数と列名を突き合わせるだけで、.xlsx は作らない。

  (2) book — 機読源 Markdown を「基本設計書（画面編）」体裁の .xlsx へ描く
      実行（dry-run。既定。何も書かない）:
        py -3 -m tools.gen_formal.book --md <file.md>
      実行（生成。目視・対外用）:
        py -3 -m tools.gen_formal.book --md <file.md> --out reports/<...>.xlsx
        py -3 -m tools.gen_formal.book --md <file.md> --out reports/x.xlsx --sheets 画面項目内容

      - md の `## N. 見出し` を 1 シートにする。シート名と順序は `book.SHEET_PLAN` が唯一の定義。
      - 前半 8 シートは参考書 `50.設計書/画面設計書/*.xlsx` と同じ名前に揃える
        （変更履歴 / 画面概要 / 画面遷移図 / 画面レイアウト / 画面項目内容 / イベント一覧 /
         業務処理説明 / 処理モジュール）。
        参考書の最終シート `R60LoginAction` は Struts 固有のため置かず、`処理モジュール` にする。
      - 参考書の**業務内容は写さない**。中身は md にあるものだけ。
        顧客の会社名・ロゴ・ページフッタ・雛形図形も複製しない。
      - 体裁（結合幅・塗り `99CCFF/CCECFF/CCFFFF`・罫線・フォント `Meiryo UI`・A4 横向）は
        `book.py` が唯一の定義。md 側に体裁を書かない。
      - 生成は冪等：同じ md からはバイト単位で同じ .xlsx が出る（zip の時刻と
        docProps/core.xml を固定している）。**生成物を手で編集しない**（次回生成で消える）。

【(3) auto — 更新された基本設計書を自動で描き直す（Stop フック）】

  実行（通常はフックが呼ぶ。手で走らせても同じ）:
    py -3 -X utf8 tools/gen_formal/auto.py
    py -3 -X utf8 tools/gen_formal/auto.py --dry-run   # 対象を表示するだけ
    py -3 -X utf8 tools/gen_formal/auto.py --force     # 時刻に関係なく全部描き直す

  - 対象: `tutorial/<case>/<節点>/` で**最も番号の大きい**「基本設計書」md（例 `05_承認版_…`）。
    01・04 などの旧稿は履歴なので自動対象外（見たいときは --force）。
  - 出力: `reports/_auto/<case>/<節点>/<stem>_预览版.xlsx`。**md より新しければ何もしない**（stat 2 回）。
    名前に `_预览版` を付けるのは、目視用の下書きであって顧客交付物ではないと分かるようにするため
    （ユーザー指示 2026-10-22）。顧客へ出す正式版は節点8 で `_正式版` を付けて別に出す。
  - 呼び出し元: `.claude/settings.json` の **Stop フック**（1 ターン終了ごと）。
    「機読源を直したのに Excel が古い」状態を残さないため（ユーザー指示 2026-10-22）。
  - 失敗してもターンを止めない（常に exit 0。原因は stderr）。

【出力先の制限（重要）】
  - `docs/**` へは書けない。`book` は出力パスに `docs` を含むと Exit 2 で拒否する。
    CP-R-3（Phase1 の合格条件）は `docs/**/*.xlsx == 0` であり、これは変わっていない。
  - 目視用・対外ドラフト用の .xlsx は `reports/` 配下（gitignore 区）にだけ置く。
  - Phase2 で顧客テンプレートへ接続する段になったら、出力先は案件の納品先へ変わる。
    その時点で本節を改訂する。

【単一ソース原則（NFR-1）】
  列名の唯一の発号元は docs/00_registry/ids.yml の I-ID。
  物理列名は docs/30_detail_design/D-043-R60Area.yaml が存在すればそちらを優先する。
  日文正式 Excel を手で編集してはならない。必ず機読源 → 変換で生成する。

【Phase2 でやること】
  - 顧客指定の日文 Excel テンプレート（templates/ 配下に配置）を読み込む
  - 会社ロゴ等の装飾は顧客テンプレート側で持つ（本ツールでは扱わない）
  - 整合チェック: 生成物の列数・列順が I-ID 定義と一致することを trace_check gate4 で再検証
  - 【受控回流】生成 Excel の正文は読み取り専用（シート保護／セル保護）とし、
    別シート「指摘シート／レビュー欄」を行番号・R-ID 付きで添付する。
    対日案件では顧客が Excel に直接赤字で修正を入れるのが常態のため、
    禁止ではなく出口を用意する：顧客は指摘シートにのみ記入 → AI はその欄だけを読んで
    機読源（.md/.yaml）を修正 → Excel を再生成。
    正文が改変されないため二重化も diff 逆推も発生しない（FR-3／NFR-1 を維持）。

【templates/】
  Phase1 では空ディレクトリ。Phase2 で顧客テンプレート（.xlsx）をここに置く。

ここに案件の原資料を置く（Excel / Word / PDF / md / txt）。
AI はこのフォルダを生成しない・編集しない（人が置くだけ）。

置いたあと:
    py -3 -m tools.kb_local import --scan --project P-R60-001 --by <案件の責任者>

抽出結果は同じ案件の `extracted/` に出る（status: draft。検索に出ない）。
原本と突き合わせて問題なければ status を open に変え、ingest --prune する。

★ 原本（.xlsx / .docx / .pdf）は git に入らない（gitignore 済）。
★ この README.txt は索引対象ではない（索引は .md だけ）。
★ 2026-11-09 以降、抽出結果はこのフォルダではなく `extracted/` に出す（原本と生成物を混ぜない）。

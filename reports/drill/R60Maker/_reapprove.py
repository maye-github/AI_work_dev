"""節点1〜5 の再承認を n0N.yml に記録する（承認者は Li・2026-11-10）。"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

NOTE = (
    "  2026-11-10: **再承認（Li）。** 前回承認（2026-11-05/06）の後に次の 2 点が変わったため。\n"
    "  　① 番号の振り直し（R-202／F-202／D-207〜212／L-212〜222／E-213〜224／I-322〜354／Q-239〜335）。\n"
    "  　② 承認版へ「知識ベースの使用記録」節を追加し、kb_refs を node-map と一致させた。\n"
    "  承認前の 4 条件を実測: blockers 空／`trace_check --strict` 全 PASS（orphans=0）／\n"
    "  `kb_refs --require-node --require-usage` OK／`check-constraints` OK（定義のある節点のみ）。\n"
)

for i in range(1, 6):
    p = "docs/00_plan/coach/R60Maker/n%02d.yml" % i
    t = open(p, encoding="utf-8").read()
    t = t.replace("state: awaiting_review\n", "state: approved\n", 1)
    # approved_at を今日へ
    t = t.replace('approved_at: "2026-11-05"', 'approved_at: "2026-11-10"')
    t = t.replace('approved_at: "2026-11-06"', 'approved_at: "2026-11-10"')
    if "approved_by:\n  - \"Li\"" not in t:
        print("!! node %d: approved_by が想定と違う" % i)
    t = t.rstrip("\n") + "\n" + NOTE
    open(p, "w", encoding="utf-8").write(t)
    print("node %d -> approved（Li / 2026-11-10）" % i)

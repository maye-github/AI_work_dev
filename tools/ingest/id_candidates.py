"""発号**候補**の生成。発号はここでは行わない（红线①③）。

本モジュールは候補を提案するだけで、`docs/00_registry/ids.yml` を書かない。
書き込みは `id-apply` サブコマンドのみであり、かつ人が `approved: true` と
記入した行だけを対象とする。

生成される候補は **全行 `approved: false`** である。
「機械が作った候補が、そのまま登録済み ID になる」経路を作らないための設計。
"""

from __future__ import annotations

# 1 モジュールあたりの提案幅（Phase 3 の prefix_plan と整合）
SUGGESTED_WIDTH = {"R": 1, "F": 1, "I": 100, "L": 10, "E": 20, "TC": 30}


def propose_candidates(module_assets: dict[str, list[str]], prefix_plan: dict | None = None) -> dict:
    """PGM 併合表から発号候補を提案する。

    Args:
        module_assets: `{pgm: [rel, ...]}`（`merge_by_pgm` の出力）
        prefix_plan:   マニフェストの `prefix_plan`（任意）。

    Returns:
        ``{"schema_version", "approved_count": 0, "modules": [...]}``
        各 module は ``{"module", "evidence": [...], "proposals": [...]}`` を持ち、
        proposals の各行は ``approved: false`` かつ ``assigned: null`` である。
    """
    width = dict(SUGGESTED_WIDTH)
    if prefix_plan and isinstance(prefix_plan.get("block_width"), dict):
        width.update({k: v for k, v in prefix_plan["block_width"].items() if isinstance(v, int)})

    modules = []
    for pgm, rels in sorted(module_assets.items()):
        if pgm == "_unassigned":
            continue
        proposals = [
            {
                "prefix": prefix,
                "count": count,
                "assigned": None,
                "approved": False,
                "approved_by": None,
                "note": "人ゲート G-B2 で承認された行のみ id-apply が登録する",
            }
            for prefix, count in width.items()
        ]
        modules.append(
            {
                "module": pgm,
                "evidence": sorted(rels),
                "proposals": proposals,
            }
        )

    return {
        "schema_version": "1",
        "generated_by": "tools.ingest id-candidates",
        "approval_required": True,
        "human_gate": "G-B2 発号承認",
        "approved_count": 0,
        "modules": modules,
    }


def approved_rows(candidates: dict) -> list[dict]:
    """`approved: true` かつ `assigned` が埋まっている行だけを抽出する（id-apply の入力）。"""
    rows = []
    for module in candidates.get("modules", []):
        for proposal in module.get("proposals", []):
            if proposal.get("approved") is True and proposal.get("assigned"):
                rows.append({**proposal, "module": module.get("module")})
    return rows

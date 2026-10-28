"""trans-cosmos-ai AI 全流程骨架 - 変更影響面の分析。

なぜ必要か
----------
R-101 の業務ルールが 1 つ変わったとき、**下流のどれを作り直し、どれを見直すか**は
人の記憶に依存していた。追跡マトリクス（`traceability.yml`）は存在するのに、
**引く道具が無かった**。本ツールはそれを引く。読むだけで、何も書かない。

3 つのグラフ源（どれが強いか、ではなく、どれが何を捕まえるか）
----------------------------------------------------------------
- `declared`（宣言辺）: `docs/00_registry/traceability.yml` の
  `forward_links` / `back_links` と、`ids.yml` 各条目の `related_ids`。
  **人が「これは繋がっている」と宣言した辺**。
- `discovered`（発見辺）: `docs/**` の本文を走査し、ID を実際に引用している箇所から
  見つけた辺。**宣言されていないのに実際に依存している**辺 ＝ `related_ids` の**漏記**。
  漏記は追跡閉ループの穴であり、警告として出す（`--strict` で不合格）。
- `indirect`（遠隔）: 2 跳以上の伝遞閉包。1 跳は「直接」、2 跳以上は「波及」。

**辺の向きの規約**: `related_ids: [X]` は「この条目は X に依存する」を意味する
（`registry.py` の阻塞判定と同じ規約）。したがって `X` が変われば当該条目が影響を受ける。

使い方::

    py -3 -m tools.impact R-101
    py -3 -m tools.impact R-101 --direction down --depth 2
    py -3 -m tools.impact D-043 --json reports/impact_D-043.json
    py -3 -m tools.impact --self-test

終了コード: 0 = 成功 / 1 = 対象 ID が台帳に無い、または `--strict` かつ発見辺あり / 2 = 引数誤り。

依存は標準ライブラリ ＋ pyyaml のみ（NFR-6）。機密の実値を書かない（gate6 は `tools/**/*.py` も走査する）。
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import deque
from pathlib import Path

from .gen_formal.gen_excel import _id_sort_key
from .paths import find_root, reconfigure_stdout, rel
from .trace_check import ID_RE, Repo

# 表示ラベル（下流＝作り直す側、上流＝見直す側）
LABEL_DOWN = "下流（作り直しが必要になり得る）"
LABEL_UP = "上流（見直しが必要になり得る）"


# --------------------------------------------------------------------------
# グラフ構築
# --------------------------------------------------------------------------

def build_graphs(repo: Repo):
    """(down, up, declared) を返す。

    `down[a] = {b, ...}` は「a が変わると b が影響を受ける」。
    `declared` は宣言辺の集合（タプル (上流, 下流)）。
    """
    down: dict[str, set[str]] = {}
    up: dict[str, set[str]] = {}
    declared: set[tuple[str, str]] = set()

    def add_edge(parent: str, child: str) -> None:
        if parent == child:
            return
        down.setdefault(parent, set()).add(child)
        up.setdefault(child, set()).add(parent)
        declared.add((parent, child))

    for parent, children in (repo.forward or {}).items():
        for child in (children or []):
            add_edge(str(parent), str(child))
    for child, parents in (repo.back or {}).items():
        for parent in (parents or []):
            add_edge(str(parent), str(child))
    for key, entry in repo.ids.items():
        if not isinstance(entry, dict):
            continue
        for ref in (entry.get("related_ids") or []):
            # 「この条目は ref に依存する」→ ref が上流
            add_edge(str(ref), str(key))

    return down, up, declared


def bfs_levels(adj: dict, start: str, max_depth: int | None = None) -> dict[str, int]:
    """start からの跳数（start 自身は 0）。max_depth は「何跳まで辿るか」。"""
    levels = {start: 0}
    queue = deque([start])
    while queue:
        cur = queue.popleft()
        depth = levels[cur]
        if max_depth is not None and depth >= max_depth:
            continue
        for nxt in sorted(adj.get(cur, ())):
            if nxt not in levels:
                levels[nxt] = depth + 1
                queue.append(nxt)
    return levels


def topo_order(nodes, down: dict) -> list[str]:
    """下流部分グラフの位相順（上流が先）。循環は安定順で末尾へ回す。"""
    nodes = set(nodes)
    indegree = {n: 0 for n in nodes}
    for n in nodes:
        for child in down.get(n, ()):
            if child in nodes:
                indegree[child] += 1
    ready = sorted((n for n in nodes if indegree[n] == 0), key=_id_sort_key)
    out: list[str] = []
    while ready:
        cur = ready.pop(0)
        out.append(cur)
        for child in sorted(down.get(cur, ()), key=_id_sort_key):
            if child in nodes:
                indegree[child] -= 1
                if indegree[child] == 0:
                    ready.append(child)
        ready.sort(key=_id_sort_key)
    # Kahn で拾い切れなかった分（循環）は安定順で末尾へ
    out.extend(sorted(nodes - set(out), key=_id_sort_key))
    return out


# --------------------------------------------------------------------------
# 発見辺（宣言されていない参照）
# --------------------------------------------------------------------------

def collect_references(repo: Repo) -> dict[str, set[str]]:
    """`owner_id -> {引用されている ID}` を返す。

    引用元の ID はそのファイルの front-matter `id`。**台帳に登録済みの ID だけ**を残す
    （教学号段 `R-201` 等の未登録 ID が結果を汚すのを防ぐ）。
    """
    refs: dict[str, set[str]] = {}
    for path in repo.iter_docs():
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        found = {f"{m.group(1)}-{m.group(2)}" for m in ID_RE.finditer(text)}
        found &= set(repo.ids)
        if not found:
            continue
        if path.suffix == ".md":
            front, _ = repo.parse_front_matter(path)
        else:
            doc = repo._load(path)
            front = doc if isinstance(doc, dict) else None
        owner = str((front or {}).get("id") or "")
        if not owner or owner not in repo.ids:
            continue
        found.discard(owner)
        if found:
            refs.setdefault(owner, set()).update(found)
    return refs


def undeclared_refs(target: str, refs: dict[str, set[str]], down: dict) -> list[dict]:
    """target を引用しているのに、**宣言グラフ上で全く繋がっていない**相手。

    「直接の辺が無い」では判定しない。下流の成果物が根の要求を引用するのは正しい姿であり、
    それは傳遞閉包が既に覆っている（例: `D-043` が `R-101` を引用するのは、
    `R-101 → F-042 → D-043` の辺があるからで、漏記ではない）。
    ここで捕まえたいのは**どちら向きにも辿り着けない孤立した依存**だけである。
    """
    out: list[dict] = []
    for owner, cited in sorted(refs.items()):
        if target not in cited or owner == target:
            continue
        if target in bfs_levels(down, owner) or owner in bfs_levels(down, target):
            continue
        out.append({"owner": owner, "cited": target})
    return out


# --------------------------------------------------------------------------
# 分析本体
# --------------------------------------------------------------------------

def analyze(repo: Repo, target: str, *, direction: str = "both",
            depth: int | None = None) -> dict:
    down, up, declared = build_graphs(repo)
    ids = repo.ids

    down_levels = bfs_levels(down, target, depth) if direction in ("both", "down") else {}
    up_levels = bfs_levels(up, target, depth) if direction in ("both", "up") else {}
    down_levels.pop(target, None)
    up_levels.pop(target, None)

    refs = collect_references(repo)
    discovered = undeclared_refs(target, refs, down)

    order = topo_order({target} | set(down_levels), down) if down_levels else [target]

    def describe(level_map: dict[str, int]) -> list[dict]:
        rows = []
        for key in sorted(level_map, key=_id_sort_key):
            entry = ids.get(key) or {}
            stale = entry.get("stale")
            rows.append({
                "id": key,
                "hops": level_map[key],
                "status": str(entry.get("status") or ""),
                "name": str(entry.get("name") or ""),
                "stale": bool(stale),
                "stale_trigger": str((stale or {}).get("trigger") or "") if isinstance(stale, dict) else "",
            })
        return rows

    return {
        "target": target,
        "target_status": str((ids.get(target) or {}).get("status") or ""),
        "direction": direction,
        "depth": depth,
        "downstream": describe(down_levels),
        "upstream": describe(up_levels),
        "indirect_down": [r for r in describe(down_levels) if r["hops"] >= 2],
        "order": order,
        "discovered": discovered,
        "graph_sizes": {"down_edges": sum(len(v) for v in down.values()),
                        "up_edges": sum(len(v) for v in up.values()),
                        "declared_edges": len(declared)},
    }


def _fmt_node(row: dict) -> str:
    marks = []
    if row["hops"] >= 2:
        marks.append(f"+{row['hops']}")
    if row["stale"]:
        marks.append(f"STALE←{row['stale_trigger'] or '?'}")
    if row["status"] == "void":
        marks.append("void")
    suffix = f"   [{', '.join(marks)}]" if marks else ""
    name = f"  {row['name']}" if row["name"] else ""
    return f"    {row['id']}{name}{suffix}"


def render(result: dict, *, root: Path) -> None:
    target = result["target"]
    print(f"[impact] 対象: {target}"
          f"（status={result['target_status'] or '未知'}）"
          f"  方向={result['direction']}  深さ={result['depth'] or '無制限'}")
    print()

    down = result["downstream"]
    up = result["upstream"]

    if down:
        print(f"  ▼ {LABEL_DOWN}: {len(down)} 件")
        for row in down:
            print(_fmt_node(row))
    else:
        print(f"  ▼ {LABEL_DOWN}: なし")
    print()

    if up:
        print(f"  ▲ {LABEL_UP}: {len(up)} 件")
        for row in up:
            print(_fmt_node(row))
    else:
        print(f"  ▲ {LABEL_UP}: なし")
    print()

    if result["order"] and len(result["order"]) > 1:
        print("  ↻ 推奨の作り直し順（上流が先。この順で承認を取ると手戻りが少ない）:")
        for i, key in enumerate(result["order"], 1):
            print(f"      {i}. {key}")
        print()

    stale_rows = [r for r in down + up if r["stale"]]
    if stale_rows:
        print("  ⚠ 既に失効（stale）と記録されている節点:")
        for row in stale_rows:
            print(f"      {row['id']}  引き金={row['stale_trigger'] or '?'}")
        print()

    if result["discovered"]:
        print(f"  ⚠ 宣言グラフ上で孤立した参照（related_ids の漏記候補）: {len(result['discovered'])} 件")
        for item in result["discovered"]:
            print(f"      {item['owner']} は本文で {item['cited']} を引用しているが、"
                  f"どちら向きにも追跡辺が無い")
        print("      → 追跡辺を宣言するか、依存が無いなら引用を消す。判断は人が行う。")
        print("      → もし {target} が変わって {owner} が古くなったのなら、その記録はこれ:".format(
            target=result["target"], owner="<引用元>"))
        for item in result["discovered"]:
            print(f"        py -3 -m tools.registry mark-stale {item['owner']} "
                  f"--reason \"<理由>\" --trigger {item['cited']} --by <人>")
        print()

    stale_target = result["target"]
    if result["downstream"]:
        print(f"  ▶ 次にやること（人が判断し、人が実行する）:")
        print(f"      1. 失効を記録する（まだなら）:")
        print(f"         py -3 -m tools.registry mark-stale {stale_target} "
              f"--reason \"<変更内容>\" --trigger <上流> --by <人>")
        print(f"      2. 上の順で作り直し、承認を得る")
        print(f"      3. 作り直しが終わった節点は失効を解除する:")
        print(f"         py -3 -m tools.registry clear-stale <ID>")
    else:
        print("  ▶ 下流はありません。この ID 単独の変更として扱えます。")


# --------------------------------------------------------------------------
# self-test（合成ツリー。実在の台帳には一切触れない）
# --------------------------------------------------------------------------

_SYNTHETIC_IDS = """\
registry:
  prefixes:
    R: "Requirements"
    Q: "Quality"
    F: "Functional"
    I: "Item"
    D: "Data"
    L: "Logic"
    E: "Error"
    TC: "Test Case"
    CR: "Change Request"
    BUG: "Bug"
ids:
  R-101:
    status: baselined
    name: "合成要求"
    used_by: docs/10_requirements/R-101-x.yaml
  F-042:
    status: baselined
    name: "合成機能"
    r_id: R-101
  D-043:
    status: baselined
    name: "合成データ"
    f_id: F-042
  L-014:
    status: draft
    name: "合成ロジック"
    d_id: D-043
  I-201:
    status: open
    name: "合成項目"
    f_id: F-042
  Q-001:
    status: open
    name: "合成質問"
    block: true
    answer: null
    origin_key: "Q:合成:1"
    related_ids:
    - L-014
  CR-001:
    status: open
    name: "合成変更票"
prefix_count_summary:
  R: 1
  Q: 1
  F: 1
  I: 1
  D: 1
  L: 1
  E: 0
  TC: 0
  CR: 1
  BUG: 0
"""

_SYNTHETIC_TRACE = """\
meta:
  root: R-101
forward_links:
  R-101: [F-042]
  F-042: [D-043, I-201]
  D-043: [L-014]
back_links:
  F-042: [R-101]
  D-043: [F-042]
  L-014: [D-043]
"""


def self_test(verbose: bool = True) -> tuple[bool, list[str]]:
    import tempfile

    failures: list[str] = []
    checks: list[str] = []

    def check(label: str, condition: bool) -> None:
        if condition:
            checks.append(label)
        else:
            failures.append(label)

    with tempfile.TemporaryDirectory(prefix="tcai-impact-selftest-") as tmp:
        root = Path(tmp)
        reg = root / "docs" / "00_registry"
        reg.mkdir(parents=True)
        (reg / "ids.yml").write_text(_SYNTHETIC_IDS, encoding="utf-8")
        (reg / "traceability.yml").write_text(_SYNTHETIC_TRACE, encoding="utf-8")

        # (a) 宣言グラフ上で繋がっている引用（L-014 は R-101 の下流）。
        #     → 漏記として**出てはいけない**。
        mod = root / "docs" / "30_detail_design"
        mod.mkdir(parents=True)
        (mod / "L-014-x.yaml").write_text(
            "id: L-014\ntype: detail_design\nreq_ids:\n- R-101\nstatus: draft\n"
            "sensitivity: internal\nowner: AI-SE\nversion: 0.1.0\n"
            "note: \"上流 R-101 の業務ルールに依存する\"\n",
            encoding="utf-8",
        )
        # (b) どちら向きにも辿れない引用（CR-001 は孤立している）。
        #     → 漏記として**出なければならない**。
        plan = root / "docs" / "00_plan"
        plan.mkdir(parents=True)
        (plan / "CR-001-x.md").write_text(
            "---\nid: CR-001\ntype: change_request\nreq_ids:\n- R-101\nstatus: open\n"
            "sensitivity: internal\nowner: AI-SE\nversion: 0.1.0\n---\n\n"
            "# 合成変更票\n\nR-101 の業務ルール変更に伴う起案（追跡辺は未宣言）。\n",
            encoding="utf-8",
        )

        repo = Repo(root)
        check("repo: 合成台帳を読める", len(repo.ids) == 7)

        down, up, declared = build_graphs(repo)
        check("declared: forward/back が下流辺になる", "F-042" in down.get("R-101", set()))
        # Q-001 の related_ids は L-014 を指す → 「Q-001 は L-014 に依存する」
        check("declared: related_ids は『参照先が上流』の辺になる",
              "Q-001" in down.get("L-014", set()) and "L-014" in up.get("Q-001", set()))

        levels = bfs_levels(down, "R-101")
        check("bfs: R-101 の下流に F-042/D-043/L-014 が入る",
              {"F-042", "D-043", "L-014"} <= set(levels))
        check("bfs: 跳数が正しい（R-101→F-042→D-043→L-014）",
              levels["F-042"] == 1 and levels["D-043"] == 2 and levels["L-014"] == 3)
        check("bfs: 深さ制限が効く", set(bfs_levels(down, "R-101", 1)) == {"R-101", "F-042"})

        order = topo_order({"R-101", "F-042", "D-043", "L-014"}, down)
        check("topo: 上流が先に来る", order.index("R-101") < order.index("F-042") < order.index("L-014"))

        refs = collect_references(repo)
        check("discovered: L-014 の引用が拾われる", "R-101" in refs.get("L-014", set()))
        check("discovered: CR-001 の引用が拾われる", "R-101" in refs.get("CR-001", set()))
        found = undeclared_refs("R-101", refs, down)
        check("discovered: 孤立した CR-001 -> R-101 が出る",
              any(x["owner"] == "CR-001" for x in found))
        check("discovered: 傳遞で繋がる L-014 -> R-101 は**出ない**（誤検知しない）",
              not any(x["owner"] == "L-014" for x in found))
        check("discovered: 宣言済みの F-042 -> R-101 は出ない",
              not any(x["owner"] == "F-042" for x in found))

        result = analyze(repo, "R-101", direction="both", depth=None)
        ids_down = {r["id"] for r in result["downstream"]}
        check("analyze: 下流に F-042/D-043/L-014/I-201",
              {"F-042", "D-043", "L-014", "I-201"} <= ids_down)
        check("analyze: 遠隔（2 跳以上）が分離される",
              {"D-043", "L-014"} <= {r["id"] for r in result["indirect_down"]})
        check("analyze: F-042 は 1 跳なので遠隔に入らない",
              "F-042" not in {r["id"] for r in result["indirect_down"]})
        check("analyze: 推奨順の先頭は R-101", result["order"][0] == "R-101")
        check("analyze: 上流は空（根なので）", result["upstream"] == [])
        check("analyze: 孤立参照だけが discovered に残る",
              [x["owner"] for x in result["discovered"]] == ["CR-001"])

        result2 = analyze(repo, "L-014", direction="both", depth=None)
        check("analyze: L-014 の上流に R-101 が入る",
              "R-101" in {r["id"] for r in result2["upstream"]})
        check("analyze: L-014 の下流に Q-001 が入る（阻塞の可視化）",
              "Q-001" in {r["id"] for r in result2["downstream"]})

        result3 = analyze(repo, "R-101", direction="down", depth=1)
        check("analyze: down 指定で上流が空になる", result3["upstream"] == [])
        check("analyze: depth=1 で 1 跳のみ",
              {r["id"] for r in result3["downstream"]} == {"F-042"})

        check("analyze: 未登録 ID は status が空", analyze(repo, "R-999")["target_status"] == "")

    if verbose:
        for label in checks:
            print(f"  ok   {label}")
        for label in failures:
            print(f"  FAIL {label}")
        print(f"[impact] self-test: {len(checks)} passed, {len(failures)} failed")
    return (not failures), failures


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="impact",
        description="変更影響面（下流／上流／推奨の作り直し順）を読むだけのツール。何も書かない。",
    )
    ap.add_argument("id", nargs="?", help="起点の ID（例: R-101）")
    ap.add_argument("--direction", choices=["both", "down", "up"], default="both")
    ap.add_argument("--depth", type=int, default=None, help="辿る跳数（既定: 無制限）")
    ap.add_argument("--strict", action="store_true",
                    help="宣言辺の無い参照（related_ids の漏記候補）があれば非ゼロ終了")
    ap.add_argument("--json", nargs="?", const="-", help="結果を JSON で書く（'-' で標準出力）")
    ap.add_argument("--root", help="リポジトリルート（既定: 自動探索）")
    ap.add_argument("--self-test", action="store_true", help="合成ツリーでの自己検証")
    return ap


def main(argv: list[str] | None = None) -> int:
    reconfigure_stdout()
    args = build_parser().parse_args(argv)

    if args.self_test:
        ok, _ = self_test()
        return 0 if ok else 1

    if not args.id:
        build_parser().print_help()
        return 2
    if args.depth is not None and args.depth < 1:
        print("[impact] --depth は 1 以上を指定してください", file=sys.stderr)
        return 2

    root = Path(args.root).resolve() if args.root else find_root()
    if not (root / "docs" / "00_registry" / "ids.yml").is_file():
        print(f"[impact] ids.yml が見つかりません: {root}", file=sys.stderr)
        return 2

    repo = Repo(root)
    if args.id not in repo.ids:
        print(f"[impact] 台帳に未登録の ID です: {args.id}", file=sys.stderr)
        return 1

    result = analyze(repo, args.id, direction=args.direction, depth=args.depth)
    render(result, root=root)

    if args.json:
        payload = json.dumps(result, ensure_ascii=False, indent=2)
        if args.json == "-":
            print(payload)
        else:
            out = Path(args.json)
            if not out.is_absolute():
                out = root / out
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(payload, encoding="utf-8")
            print(f"[impact] report -> {rel(root, out)}")

    if args.strict and result["discovered"]:
        print(f"[impact] --strict: 宣言辺の無い参照が {len(result['discovered'])} 件あります。",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

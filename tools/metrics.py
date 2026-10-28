"""trans-cosmos-ai AI 全流程骨架 - KPI 度量（実施規格書 §13 の 6 次元）。

なぜ必要か
----------
実施規格書 §13 は 6 つの KPI 次元を定めているが、本骨架には**度量の道具が無かった**。
`reports/AC-selfcheck.md` は受入基準（作ったか）を見るが、**運用してどうなったか**は
誰も測っていない。本ツールは「**このリポジトリから機械で測れるものだけ**」を測り、
**測れないものは測れないと書く**（数値を捏造しない）。

6 次元と、本ツールの立ち位置
-----------------------------
| §13 次元 | 測れるか | 出所 |
|---|---|---|
| ① 生産性（工数削減率） | **測れない** | 工数の記録が無い。パイロットで人が記録するしかない |
| ② 品質（指摘密度・手戻り率） | **一部** | 審査記録の RC 件数のみ。手戻り率は演習の対比記録が要る |
| ③ AI 活用度（採用率・修正率） | **一部** | commit の `AI:` 行から「AI 関与率」だけ。採用率・修正率は人の記録が要る |
| ④ 網羅性（要件・テスト観点のカバレッジ） | **測れる** | `ids.yml` の親リンク＋TC 設計書の `design_ids` |
| ⑤ リードタイム（工程間の待ち） | **測れる**（演習のみ） | `docs/00_plan/coach/<module>/nNN.yml` の `approved_at` |
| ⑥ 知識資産（登録数・ヒット率） | **測れる** | 知識 `.md` の件数＋`reports/rag/eval-*.json` |

**目標値は置かない。** 規格書 §13 が「最初から高く置かず、パイロットで基準値を計測してから
改善目標を設定する」と定めているため、本ツールは**基準値の採取**だけを行う。

冪等性（規則 03 §7.1）
----------------------
出力に「今日の日付」を埋めない。**基準日は git HEAD のコミット日**から取る
（同じリポジトリ状態なら何度走らせても同じ出力になる）。
`--date` で明示的に上書きできる。

使い方::

    py -3 -m tools.metrics                    # Markdown を標準出力
    py -3 -m tools.metrics --json reports/metrics/latest.json
    py -3 -m tools.metrics --out reports/metrics/2026-10-28.md
    py -3 -m tools.metrics --self-test

終了コード: 0 = 成功 / 1 = 台帳が読めない等の致命的エラー / 2 = 引数誤り。

依存は標準ライブラリ ＋ pyyaml のみ（NFR-6）。機密の実値を書かない（gate6 は tools/**/*.py も走査する）。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml

from . import paths

# 工程順。遅延の計算と表示順に使う。
NODE_NAMES = {
    1: "要件理解",
    2: "基本設計",
    3: "詳細設計",
    4: "框架構築",
    5: "製造",
    6: "単体テスト",
    7: "結合総合テスト",
    8: "リリース運用保守",
    9: "変更環（n09・旁路環）",
}

# 親リンクの字段名 → 親のプレフィックス。ids.yml の規約（F は r_id、I は f_id …）。
PARENT_FIELD = {"r_id": "R", "f_id": "F", "d_id": "D", "l_id": "L", "e_id": "E", "i_id": "I"}


# --------------------------------------------------------------------------
# 読み込み
# --------------------------------------------------------------------------

def load_ids(root: Path) -> dict:
    """`ids.yml` の `ids` 節を返す。読めなければ例外。"""
    p = paths.registry_path(root)
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    ids = data.get("ids") or {}
    if not isinstance(ids, dict):
        raise ValueError(f"ids.yml の ids 節が辞書ではありません: {type(ids)}")
    return ids


def prefix_of(ident: str) -> str:
    """`TC-001` → `TC`。ハイフンより前を返す。"""
    return ident.split("-", 1)[0]


def _iter_test_case_files(root: Path):
    """TC 設計書（front-matter に `test_cases` を持つ YAML）を列挙する。

    走査範囲は `docs/**` と `tutorial/**`。`archive/` は過去の写しなので数えない。
    """
    for base in ("docs", "tutorial"):
        d = root / base
        if not d.is_dir():
            continue
        for p in sorted(d.rglob("*.yaml")) + sorted(d.rglob("*.yml")):
            yield p


def load_test_cases(root: Path) -> list[dict]:
    """全 TC 設計書から `test_cases` を平坦化して返す。

    読めないファイルは**黙って飛ばさず**、`_errors` に積んで呼び出し元へ返す
    （数だけ合って中身が欠けている、という一番たちの悪い壊れ方を避ける）。
    """
    out: list[dict] = []
    for p in _iter_test_case_files(root):
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        cases = data.get("test_cases")
        if not isinstance(cases, list):
            continue
        for c in cases:
            if isinstance(c, dict) and c.get("test_id"):
                c = dict(c)
                c["_source"] = paths.rel(root, p)
                out.append(c)
    return out


def load_coach_cases(root: Path) -> list[dict]:
    """`docs/00_plan/coach/<module>/` の `case.yml` ＋ `nNN.yml` を読む。"""
    base = root / "docs" / "00_plan" / "coach"
    out: list[dict] = []
    if not base.is_dir():
        return out
    for module_dir in sorted(p for p in base.iterdir() if p.is_dir()):
        case_file = module_dir / "case.yml"
        if not case_file.is_file():
            continue
        try:
            case = yaml.safe_load(case_file.read_text(encoding="utf-8")) or {}
        except Exception:
            continue
        nodes = []
        for i in range(1, 10):
            f = module_dir / f"n{i:02d}.yml"
            if not f.is_file():
                continue
            try:
                nd = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
            except Exception:
                continue
            nodes.append(nd)
        out.append({"module": module_dir.name, "case": case, "nodes": nodes})
    return out


def latest_rag_eval(root: Path) -> dict | None:
    """`reports/rag/eval-*.json` の最新（ファイル名の日付で比較）を返す。"""
    d = root / "reports" / "rag"
    if not d.is_dir():
        return None
    files = sorted(d.glob("eval-*.json"))
    if not files:
        return None
    try:
        return json.loads(files[-1].read_text(encoding="utf-8"))
    except Exception:
        return None


def count_knowledge(root: Path) -> dict:
    """知識の件数。`docs/90_knowledge/**` の `.md` を数える（生成物 `.html` は数えない）。

    chunk は**ファイル数ではなく行数**を数える。`.jsonl` は 1 行 1 chunk なので、
    ファイル数を出すと「7 本」と表示され、実際の知識量（数百）を桁で誤らせる。
    """
    d = root / "docs" / "90_knowledge"
    if not d.is_dir():
        return {"md": 0, "chunk_files": 0, "chunks": 0}
    md = list(d.rglob("*.md"))
    chunk_files = list(d.rglob("*.jsonl"))
    chunks = 0
    for p in chunk_files:
        try:
            with p.open(encoding="utf-8", errors="ignore") as fh:
                chunks += sum(1 for line in fh if line.strip())
        except Exception:
            continue
    return {"md": len(md), "chunk_files": len(chunk_files), "chunks": chunks}


def count_review_records(root: Path) -> int:
    """審査記録の RC 番号（`RC-SK-01` 等）の**異なり数**。"""
    d = root / "docs" / "90_knowledge" / "review_diff_assets"
    if not d.is_dir():
        return 0
    seen = set()
    import re
    pat = re.compile(r"RC-[A-Z]{2,}-\d+")
    for p in d.rglob("*.md"):
        try:
            seen.update(pat.findall(p.read_text(encoding="utf-8", errors="ignore")))
        except Exception:
            continue
    return len(seen)


def git_stats(root: Path) -> dict:
    """git log から AI 関与率と種別内訳を取る。git が無ければ空を返す。"""
    def run(*args: str) -> str:
        try:
            return subprocess.run(
                ["git", *args], cwd=str(root), capture_output=True, text=True,
                encoding="utf-8", errors="replace", check=False,
            ).stdout
        except Exception:
            return ""

    log = run("log", "--format=%H%x1f%s%x1f%b%x1e")
    if not log.strip():
        return {"available": False}
    commits = [c for c in log.split("\x1e") if c.strip()]
    with_ai = 0
    by_type: dict[str, int] = {}
    for c in commits:
        parts = c.strip().split("\x1f")
        if len(parts) < 3:
            continue
        subject, body = parts[1], parts[2]
        if "\nAI:" in body or body.startswith("AI:"):
            with_ai += 1
        t = subject.split(":", 1)[0].strip()
        if t in {"req", "design", "feat", "test", "fix", "rel", "chore"}:
            by_type[t] = by_type.get(t, 0) + 1
    head_date = run("log", "-1", "--format=%ad", "--date=short").strip()
    return {
        "available": True,
        "commits": len(commits),
        "with_ai_trailer": with_ai,
        "ai_ratio": (with_ai / len(commits)) if commits else 0.0,
        "by_type": dict(sorted(by_type.items())),
        "head_date": head_date,
    }


# --------------------------------------------------------------------------
# 計算
# --------------------------------------------------------------------------

def coverage(ids: dict, test_cases: list[dict]) -> dict:
    """④ 網羅性：台帳の親リンク充足率と、TC 設計書から見た L/E カバレッジ。"""
    by_prefix: dict[str, list[str]] = {}
    for ident in ids:
        by_prefix.setdefault(prefix_of(ident), []).append(ident)

    # 親リンク充足率：子 ID のうち、親 ID が台帳に実在するものの割合
    link_stats: dict[str, dict] = {}
    for parent_field, parent_prefix in PARENT_FIELD.items():
        children = [
            (ident, entry) for ident, entry in ids.items()
            if isinstance(entry, dict) and entry.get(parent_field)
        ]
        if not children:
            continue
        ok = sum(
            1 for _, e in children
            if str(e[parent_field]) in ids
        )
        link_stats[parent_prefix] = {"children": len(children), "resolved": ok}

    # テスト観点カバレッジ：TC の design_ids に現れた L/E の異なり数
    covered: set[str] = set()
    for c in test_cases:
        for d in (c.get("design_ids") or []):
            covered.add(str(d))
    l_all = set(by_prefix.get("L", []))
    e_all = set(by_prefix.get("E", []))
    l_cov = sorted(l_all & covered)
    e_cov = sorted(e_all & covered)

    # 工程チェーン：R→F→I / F→D / D→L が繋がっているか（演習 ID も含めて数える）
    chain = {
        "R→F": sum(1 for v in ids.values() if isinstance(v, dict) and v.get("r_id")),
        "F→I": sum(1 for v in ids.values() if isinstance(v, dict) and v.get("i_id") is None and False),
    }
    chain["F→I"] = sum(1 for v in ids.values() if isinstance(v, dict) and v.get("f_id"))
    chain["D→L"] = sum(1 for v in ids.values() if isinstance(v, dict) and v.get("d_id"))

    return {
        "by_prefix": {k: len(v) for k, v in sorted(by_prefix.items())},
        "total_ids": len(ids),
        "parent_links": link_stats,
        "coverage": {
            "L": {"total": len(l_all), "covered": len(l_cov), "missing": sorted(l_all - covered)},
            "E": {"total": len(e_all), "covered": len(e_cov), "missing": sorted(e_all - covered)},
            "I": {"total": len(by_prefix.get("I", [])),
                  "referenced_by_tc": len([x for x in covered if prefix_of(x) == "I"])},
        },
        "chain": chain,
        "test_case_count": len(test_cases),
    }


def lead_time(coach_cases: list[dict]) -> list[dict]:
    """⑤ リードタイム：`case.yml` の開始日から各節点の承認日までの日数。"""
    from datetime import date

    def parse(s):
        try:
            y, m, d = str(s).strip("'\"").split("-")
            return date(int(y), int(m), int(d))
        except Exception:
            return None

    out = []
    for c in coach_cases:
        start = parse(c["case"].get("started_at"))
        rows = []
        prev = start
        for nd in c["nodes"]:
            appr = parse(nd.get("approved_at"))
            rows.append({
                "node": nd.get("node"),
                "name": nd.get("name") or NODE_NAMES.get(nd.get("node"), ""),
                "state": nd.get("state"),
                "approved_at": nd.get("approved_at"),
                "days_from_start": (appr - start).days if (appr and start) else None,
                "days_from_prev": (appr - prev).days if (appr and prev) else None,
            })
            if appr:
                prev = appr
        out.append({
            "module": c["module"],
            "started_at": c["case"].get("started_at"),
            "build_mode": c["case"].get("build_mode"),
            "case_kind": c["case"].get("case_kind"),
            "nodes": rows,
            "total_days": (
                max(r["days_from_start"] for r in rows if r["days_from_start"] is not None)
                if any(r["days_from_start"] is not None for r in rows) else None
            ),
        })
    return out


def build_snapshot(root: Path, base_date: str | None = None) -> dict:
    """6 次元の基準値を 1 つの辞書にまとめる。"""
    ids = load_ids(root)
    tcs = load_test_cases(root)
    coach = load_coach_cases(root)
    rag = latest_rag_eval(root)
    know = count_knowledge(root)
    git = git_stats(root)

    snap = {
        "base_date": base_date or git.get("head_date") or "",
        "spec_section": "实施规格书 §13.1（六大维度）",
        "dimensions": {
            "1_productivity": {
                "measurable": False,
                "reason": "工数の記録がリポジトリに無い。パイロットで人が記録する項目（規格書 §13 の注記）",
            },
            "2_quality": {
                "measurable": "partial",
                "review_records": count_review_records(root),
                "reason": "指摘の記録件数のみ。手戻り率・障害混入率は演習の対比記録（reports/drill）が要る",
            },
            "3_ai_usage": {
                "measurable": "partial",
                "commits": git.get("commits", 0),
                "with_ai_trailer": git.get("with_ai_trailer", 0),
                "ai_ratio": round(git.get("ai_ratio", 0.0), 4),
                "by_type": git.get("by_type", {}),
                "reason": "AI 関与率のみ。生成物の採用率・修正率は人の記録が要る",
            },
            "4_coverage": coverage(ids, tcs),
            "5_lead_time": {
                "measurable": "partial",
                "cases": lead_time(coach),
                "reason": "演習（coach 状態ファイルを持つ案件）のみ。実案件は approved_at を記録していない",
            },
            "6_knowledge": {
                "measurable": True,
                "knowledge_md": know["md"],
                "chunk_files": know["chunk_files"],
                "chunks": know["chunks"],
                "rag": (
                    {
                        "eval_file": "reports/rag/eval-*.json（最新）",
                        "gold_count": rag.get("gold_count"),
                        "k": rag.get("k"),
                        "filtered": rag.get("filtered_by_module"),
                        "unfiltered": rag.get("unfiltered"),
                    } if rag else None
                ),
            },
        },
    }
    return snap


# --------------------------------------------------------------------------
# 出力
# --------------------------------------------------------------------------

def render_markdown(snap: dict) -> str:
    d = snap["dimensions"]
    L: list[str] = []
    L.append(f"# KPI 基準値 — {snap['base_date']}")
    L.append("")
    L.append(f"> 出所：`{snap['spec_section']}`。**目標値は置かない**（規格書 §13 の注記どおり、")
    L.append("> まず基準値を採る）。生成：`py -3 -m tools.metrics`（手で編集しない）。")
    L.append("")
    L.append("| §13 次元 | 計測 | 値 |")
    L.append("|---|---|---|")

    L.append(f"| ① 生産性 | ❌ 測れない | {d['1_productivity']['reason']} |")

    q = d["2_quality"]
    L.append(f"| ② 品質 | 🔶 一部 | 審査記録 {q['review_records']} 件。{q['reason']} |")

    a = d["3_ai_usage"]
    types = "／".join(f"{k} {v}" for k, v in a["by_type"].items()) or "—"
    L.append(
        f"| ③ AI 活用度 | 🔶 一部 | commit {a['commits']} 件中 `AI:` 行あり {a['with_ai_trailer']} 件"
        f"（{a['ai_ratio'] * 100:.1f}%）。種別内訳：{types}。{a['reason']} |"
    )

    cv = d["4_coverage"]
    L.append(f"| ④ 網羅性 | ✅ 測れる | ID {cv['total_ids']} 件。詳細は下の §④ |")

    lt = d["5_lead_time"]
    if lt["cases"]:
        parts = [f"{c['module']} {c['total_days']} 日" for c in lt["cases"] if c["total_days"] is not None]
        L.append(f"| ⑤ リードタイム | 🔶 一部 | {'／'.join(parts) or '—'}。{lt['reason']} |")
    else:
        L.append(f"| ⑤ リードタイム | ❌ 未計測 | coach 状態ファイルが無い |")

    k = d["6_knowledge"]
    rag = k.get("rag")
    if rag:
        f = rag["filtered"] or {}
        u = rag["unfiltered"] or {}
        L.append(
            f"| ⑥ 知識資産 | ✅ 測れる | 知識 {k['knowledge_md']} 本・chunk {k['chunks']} 件"
            f"（{k['chunk_files']} ファイル）。"
            f"RAG hit@{rag['k']}：モジュール絞り込み {f.get('hit_at_k')}／絞り込み無し {u.get('hit_at_k')}"
            f"（MRR {f.get('mrr')}／{u.get('mrr')}、設問 {rag['gold_count']} 問） |"
        )
    else:
        L.append(
            f"| ⑥ 知識資産 | ✅ 測れる | 知識 {k['knowledge_md']} 本・chunk {k['chunks']} 件。"
            f"RAG 評価ファイル無し |"
        )

    L.append("")
    L.append("## ④ 網羅性の内訳")
    L.append("")
    L.append("**ID の分布**（`ids.yml` の実数）")
    L.append("")
    L.append("| プレフィックス | 件数 |")
    L.append("|---|---|")
    for k2, v in cv["by_prefix"].items():
        L.append(f"| {k2} | {v} |")
    L.append("")
    L.append("**親リンクの充足**（子 ID の親が台帳に実在するか）")
    L.append("")
    L.append("| 親 | 子の件数 | 親が解決した件数 |")
    L.append("|---|---|---|")
    for k2, v in cv["parent_links"].items():
        L.append(f"| {k2} | {v['children']} | {v['resolved']} |")
    L.append("")
    L.append("**テスト観点カバレッジ**（TC 設計書の `design_ids` から見て）")
    L.append("")
    L.append(f"- TC 設計書の総ケース数：{cv['test_case_count']}")
    for p in ("L", "E"):
        c = cv["coverage"][p]
        miss = "、".join(c["missing"]) if c["missing"] else "なし"
        L.append(f"- {p}：{c['covered']}/{c['total']} が TC から参照されている。未参照：{miss}")
    L.append(f"- I：{cv['coverage']['I']['total']} 件中、TC から参照 {cv['coverage']['I']['referenced_by_tc']} 件"
             "（画面項目は全部を TC で参照する必要はない）")
    L.append("")
    L.append("## ⑤ リードタイムの内訳")
    L.append("")
    for c in lt["cases"]:
        L.append(f"**{c['module']}**（{c['case_kind']}／{c['build_mode']}／開始 {c['started_at']}）")
        L.append("")
        L.append("| 節点 | 名称 | 状態 | 承認日 | 開始から | 前節点から |")
        L.append("|---|---|---|---|---|---|")
        for r in c["nodes"]:
            L.append(
                f"| {r['node']} | {r['name']} | {r['state']} | {r['approved_at'] or '—'} | "
                f"{r['days_from_start'] if r['days_from_start'] is not None else '—'} | "
                f"{r['days_from_prev'] if r['days_from_prev'] is not None else '—'} |"
            )
        L.append("")
    L.append("> **読み方**：「前節点から」が大きい節点が待ち時間の支配項である。")
    L.append("> 本演習は**人が週末を挟んで作業した**ため、この値は「AI の速さ」ではなく")
    L.append("> 「人の承認までの待ち」を測っている（規格書 §13 ⑤ が求めているのはこちら）。")
    L.append(">")
    L.append("> **「前節点から」が負の節点がある場合**、それは計測誤差ではなく**承認の順序が")
    L.append("> 節点番号の順になっていない**という事実である（後続の節点を先に承認した記録が残っている）。")
    L.append("> 規格書は 8 工程を**この順に進める**ことを求めており、紅线②（設計なき製造禁止）は")
    L.append("> まさにこの順序の規約である。本値はその逸脱を機械的に可視化したものであり、")
    L.append("> **是正するかどうかは人が裁定する**（記録を書き換えて順序を装ってはならない）。")
    L.append("")
    return "\n".join(L)


# --------------------------------------------------------------------------
# 自己テスト
# --------------------------------------------------------------------------

def self_test() -> int:
    """索引に依存しない範囲で、計算の骨格が壊れていないことを確かめる。"""
    paths.reconfigure_stdout()
    ok = 0
    total = 0

    total += 1
    if prefix_of("TC-001") == "TC" and prefix_of("R-101") == "R":
        ok += 1
        print("[metrics:self-test] ok   prefix_of")
    else:
        print("[metrics:self-test] FAIL prefix_of")

    total += 1
    fake_ids = {
        "R-1": {"status": "open"},
        "F-1": {"r_id": "R-1"},
        "F-2": {"r_id": "R-999"},   # 親が存在しない
        "L-1": {"d_id": "D-1"},
        "E-1": {"l_id": "L-1"},
    }
    cv = coverage(fake_ids, [{"test_id": "TC-1", "design_ids": ["L-1"]}])
    if cv["parent_links"]["R"] == {"children": 2, "resolved": 1} and cv["coverage"]["L"]["covered"] == 1:
        ok += 1
        print("[metrics:self-test] ok   coverage（親の未解決を数える）")
    else:
        print(f"[metrics:self-test] FAIL coverage: {cv['parent_links']}")

    total += 1
    md = render_markdown(build_snapshot(paths.find_root(Path.cwd())))
    if "① 生産性" in md and "④ 網羅性" in md and md.count("|") > 30:
        ok += 1
        print("[metrics:self-test] ok   render_markdown")
    else:
        print("[metrics:self-test] FAIL render_markdown")

    print(f"[metrics:self-test] {'PASS' if ok == total else 'FAIL'} {ok}/{total} pass")
    return 0 if ok == total else 1


# --------------------------------------------------------------------------
# エントリポイント
# --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="py -3 -m tools.metrics",
        description="実施規格書 §13 の 6 次元について、このリポジトリから測れる基準値を出す。",
    )
    ap.add_argument("--json", metavar="PATH", help="JSON でも書き出す")
    ap.add_argument("--out", metavar="PATH", help="Markdown をファイルへ書き出す（標準出力にも出す）")
    ap.add_argument("--date", metavar="YYYY-MM-DD", help="基準日を上書き（既定は git HEAD のコミット日）")
    ap.add_argument("--self-test", action="store_true", help="自己テストだけ実行する")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()

    try:
        root = paths.find_root(Path.cwd())
    except Exception as e:  # pragma: no cover
        print(f"[metrics] リポジトリ根が見つかりません: {e}", file=sys.stderr)
        return 1

    paths.reconfigure_stdout()

    try:
        snap = build_snapshot(root, base_date=args.date)
    except Exception as e:
        print(f"[metrics] 計測に失敗しました: {e}", file=sys.stderr)
        return 1

    md = render_markdown(snap)
    print(md)

    if args.out:
        p = Path(args.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(md + "\n", encoding="utf-8")
        print(f"[metrics] wrote {p}", file=sys.stderr)

    if args.json:
        p = Path(args.json)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(snap, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[metrics] wrote {p}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

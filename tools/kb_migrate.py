"""旧案件知識を kb-platform の project scope へ移す（2026-10-29 の 1 回限りの移設器）。

背景
----
`docs/95_legacy/r60/` の 76 件を `tools/kb-platform/repo/projects/P-R60-001/` へ移し、
知識庫の正本にする（ユーザー拍板: reports/audit/kb-integration/03_拍板记录_2026-10-29.md）。

移設元 `docs/95_legacy/r60/` は移設後に削除した。**移設済みの現在の用途は
「モジュールカードの YAML 正本から、同ディレクトリの `.md` ビューを作り直す」ことだけ**である（§本体の分岐を参照）。

移設のとき、**1 ファイルが 2 つの lint を同時に満たす**ように front matter を合成する。

- 骨架 gate3 が要求する 7 字段: id / type / req_ids / status / sensitivity / owner / version
- kb-platform が要求する 8 鍵: doc_id / scope / title / doc_type / version / status / conf_level / updated_at

`status` は両者が共有するが語彙が違う。骨架の語彙（draft/open/baselined/changed/done）を
そのまま書き、kb 側は「どの状態を検索対象にするか」を kbkit/retrieval.py の
`DEFAULT_RETRIEVABLE` で持つ（2026-10-29 に追加）。ここで `active` へ変換してはならない
——変換すると骨架の状態機が壊れる。

生成物
------
- `.md`: front matter を合成してコピー
- `.yaml`（モジュールカード）: そのままコピー（正本）。同ディレクトリに `.md` の表形式ビューを生成
- `.jsonl`（検索摘要）: モジュールごとに 1 篇の `.md` へまとめる（摘要本文は改変しない）

使い方
------
    py -3 -m tools.kb_migrate            # 下見（何がどこへ行くかだけ出す）
    py -3 -m tools.kb_migrate --apply    # 実行
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

SRC_REL = "docs/95_legacy/r60"  # 移設元（1 回限りの移設器。実行後は存在しない）
DST_REL = "tools/kb-platform/repo/projects/P-R60-001"
PROJECT_ID = "P-R60-001"
ROOT = Path(__file__).resolve().parent.parent

# パスの形 → kb の doc_type（pipeline.py の DOC_TYPES のいずれか）
DOC_TYPES: list[tuple[str, str]] = [
    ("screens/", "design-basic"),
    ("modules/", "design-detail"),
    ("chunks/", "glossary"),
    ("review/", "decision"),
    ("howto/", "howto"),
    ("02-architecture", "design-detail"),
    ("05-database", "design-detail"),
    ("06-api", "design-detail"),
    ("03-conventions", "standard"),
    ("04-common-parts", "standard"),
    ("07-traceability", "standard"),
    ("08-deviations", "decision"),
    ("module-selection", "decision"),
    ("learning-plan", "decision"),
]
DEFAULT_DOC_TYPE = "howto"

CONF_MAP = {"public": 10, "internal": 30, "confidential": 40}
DEFAULT_CONF = 30

# モジュールカードの種別 → 日本語の見出し
ARTIFACT_LABEL = {
    "01-fields": "項目定義（フィールド辞書）",
    "02-api": "API 契約",
    "03-logic": "業務ロジック",
    "04-errors": "エラー一覧",
    "05-tests": "単体テスト観点",
    "06-review": "レビュー指摘と処置",
}


# --------------------------------------------------------------------------
# 補助
# --------------------------------------------------------------------------

def git_date(rel_path: str) -> str:
    """最終コミット日（YYYY-MM-DD）。今日の日付は使わない（冪等性・規則 03 §7.1）。"""
    import subprocess

    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%ad", "--date=short", "--", rel_path],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        ).stdout.strip()
    except OSError:
        return ""
    return out or "1970-01-01"


def split_fm(text: str) -> tuple[dict, str]:
    """先頭 `---` で囲まれた front matter を切り出す（無ければ空 dict）。"""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    head = text[3:end]
    body = text[end + 4 :]
    if body.startswith("\r\n"):
        body = body[2:]
    elif body.startswith("\n"):
        body = body[1:]
    try:
        meta = yaml.safe_load(head) or {}
    except yaml.YAMLError:
        meta = {}
    if not isinstance(meta, dict):
        meta = {}
    return meta, body


def dump_fm(meta: dict) -> str:
    return "---\n" + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False, default_flow_style=False) + "---\n"


def slug_for(rel: str) -> str:
    import re

    s = rel.lower()
    s = re.sub(r"\.(md|ya?ml)$", "", s)
    s = re.sub(r"/", "-", s)
    s = re.sub(r"[^a-z0-9-]", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return f"r60-001-{s}"


def doc_type_for(rel: str) -> str:
    for pat, dt in DOC_TYPES:
        if pat in rel:
            return dt
    return DEFAULT_DOC_TYPE


def title_of(body: str, fallback: str) -> str:
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("# "):
            t = line[2:].strip()
            if len(t) >= 4:
                return t
    return fallback if len(fallback) >= 4 else f"[{fallback}] 知識"


def merged_fm(meta: dict, rel: str, source_rel: str, fallback_title: str, body: str) -> dict:
    """骨架 7 字段を残したまま kb の必須鍵を足す。"""
    out: dict = {}
    # 骨架 7 字段を先に（順序は gate3 の読みやすさのため）
    for k in ("id", "type", "req_ids", "status", "sensitivity", "owner", "version"):
        if k in meta:
            out[k] = meta[k]
    out.setdefault("id", "KNOW-LEGACY-" + slug_for(rel).upper().replace("-", "-"))
    out.setdefault("type", "knowledge")
    out.setdefault("req_ids", [])
    out.setdefault("status", "draft")
    out.setdefault("sensitivity", "internal")
    out.setdefault("owner", "AI-SE")
    out.setdefault("version", "0.1.0")
    # kb の必須鍵
    out["doc_id"] = slug_for(rel)
    out["scope"] = "project"
    out["project_id"] = PROJECT_ID
    out["title"] = title_of(body, fallback_title)
    out["doc_type"] = doc_type_for(rel)
    out["conf_level"] = CONF_MAP.get(str(out["sensitivity"]), DEFAULT_CONF)
    out["updated_at"] = git_date(source_rel)
    return out


def yaml_to_markdown(data: dict, level: int = 2) -> list[str]:
    """YAML を表形式の Markdown にする。**1 行 = 1 チャンク**になる形を優先する。"""
    lines: list[str] = []
    if not isinstance(data, dict):
        lines.append("```yaml")
        lines.append(yaml.safe_dump(data, allow_unicode=True, sort_keys=False).rstrip())
        lines.append("```")
        return lines

    scalars = {str(k): v for k, v in data.items() if not isinstance(v, (dict, list))}
    lists = {str(k): v for k, v in data.items() if isinstance(v, list)}
    dicts = {str(k): v for k, v in data.items() if isinstance(v, dict)}

    if scalars:
        lines.append("| 項目 | 値 |")
        lines.append("|---|---|")
        for k, v in scalars.items():
            lines.append(f"| {k} | {_cell(v)} |")
        lines.append("")

    for k, v in dicts.items():
        lines.append(f"{'#' * level} {k}")
        lines.append("")
        if all(not isinstance(x, (dict, list)) for x in v.values()):
            lines.append("| 項目 | 値 |")
            lines.append("|---|---|")
            for kk, vv in v.items():
                lines.append(f"| {kk} | {_cell(vv)} |")
            lines.append("")
        else:
            lines.extend(yaml_to_markdown(v, min(level + 1, 6)))
            lines.append("")

    for k, v in lists.items():
        lines.append(f"{'#' * level} {k}")
        lines.append("")
        rows = [{str(k): val for k, val in x.items()} for x in v if isinstance(x, dict)]
        plain = [x for x in v if not isinstance(x, dict)]
        if rows:
            cols: list[str] = []
            for r in rows:
                for ck in r:
                    ck = str(ck)
                    if ck not in cols:
                        cols.append(ck)
            lines.append("| " + " | ".join(cols) + " |")
            lines.append("|" + "|".join(["---"] * len(cols)) + "|")
            for r in rows:
                lines.append("| " + " | ".join(_cell(r.get(c, "")) for c in cols) + " |")
            lines.append("")
        for x in plain:
            lines.append(f"- {_cell(x)}")
        if plain:
            lines.append("")
    return lines


def _cell(v) -> str:
    if isinstance(v, (dict, list)):
        s = json.dumps(v, ensure_ascii=False)
    else:
        s = "" if v is None else str(v)
    s = s.replace("\r", " ").replace("\n", " ").replace("|", "\\|")
    return s.strip()


def write_view(yaml_path: Path, view_path: Path, dst_root: Path) -> None:
    """モジュールカード YAML から、検索用の表形式 Markdown を作る。"""
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    module = str(data.get("module") or yaml_path.parent.name)
    atype = str(data.get("artifact_type") or yaml_path.stem)
    label = ARTIFACT_LABEL.get(yaml_path.stem, atype)
    rel_for_slug = view_path.relative_to(dst_root).as_posix()
    body = "\n".join(
        [
            f"# {module} — {label}",
            "",
            f"> 正本は同ディレクトリの `{yaml_path.name}`。本ファイルは検索用の可読表現であり、",
            "> 手で編集しない（`py -3 -m tools.kb_migrate --apply` で作り直す）。",
            "",
        ]
        + yaml_to_markdown(
            {str(k): v for k, v in data.items() if k not in ("source", "module", "artifact_type")}
        )
    )
    fm = merged_fm(
        {
            "id": str(data.get("id") or "") + "-VIEW",
            "type": "knowledge",
            "req_ids": [],
            "status": data.get("status", "draft"),
            "sensitivity": data.get("sensitivity", "internal"),
            "owner": data.get("owner", "AI-SE"),
            "version": data.get("version", "0.1.0"),
        },
        rel_for_slug,
        yaml_path.as_posix(),
        f"{module} {label}",
        body,
    )
    view_path.parent.mkdir(parents=True, exist_ok=True)
    view_path.write_text(dump_fm(fm) + "\n" + body, encoding="utf-8", newline="\n")


# --------------------------------------------------------------------------
# 本体
# --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="旧案件知識を kb-platform の project scope へ移設する")
    ap.add_argument("--apply", action="store_true", help="実行する（既定は下見）")
    args = ap.parse_args(argv)

    src = ROOT / SRC_REL
    dst = ROOT / DST_REL
    if not src.is_dir():
        # 移設済み。YAML 正本はすでに dst にあるので、ビューだけを作り直す。
        views = [p for p in sorted(dst.rglob("*.yaml"))]
        if args.apply:
            for yp in views:
                write_view(yp, yp.with_suffix(".md"), dst)
        verb = "再生成しました" if args.apply else "再生成します（--apply で実行）"
        print(f"[kb_migrate] 移設済み。モジュールビュー {len(views)} 件を{verb}")
        return 0

    plan: list[tuple[str, str, str]] = []  # (種別, 元, 先)
    written = 0

    for path in sorted(src.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(src).as_posix()
        if rel.startswith("chunks/"):
            continue  # 別途、摘要としてまとめる
        if rel.startswith("review_diff_assets/"):
            rel = "review/" + rel[len("review_diff_assets/") :]
        if path.suffix == ".md":
            plan.append(("md", path.relative_to(ROOT).as_posix(), (dst / rel).relative_to(ROOT).as_posix()))
        elif path.suffix in (".yaml", ".yml"):
            plan.append(("yaml", path.relative_to(ROOT).as_posix(), (dst / rel).relative_to(ROOT).as_posix()))
            view_rel = Path(rel).with_suffix(".md").as_posix()
            plan.append(("view", path.relative_to(ROOT).as_posix(), (dst / view_rel).relative_to(ROOT).as_posix()))
        else:
            plan.append(("copy", path.relative_to(ROOT).as_posix(), (dst / rel).relative_to(ROOT).as_posix()))

    # chunks/*.jsonl → モジュールごとに 1 篇
    chunk_dir = src / "chunks"
    if chunk_dir.is_dir():
        for jl in sorted(chunk_dir.glob("*.jsonl")):
            plan.append(("digest", jl.relative_to(ROOT).as_posix(), (dst / "chunks" / f"{jl.stem}.md").relative_to(ROOT).as_posix()))

    print(f"[kb_migrate] 移設 {len(plan)} 件（{SRC_REL} → {DST_REL}）")
    if not args.apply:
        for kind, s, d in plan:
            print(f"  {kind:6s} {s}  ->  {d}")
        print("[kb_migrate] 下見のみ。実行するには --apply")
        return 0

    for kind, s, d in plan:
        sp = ROOT / s
        dp = ROOT / d
        dp.parent.mkdir(parents=True, exist_ok=True)
        if kind == "md":
            meta, body = split_fm(sp.read_text(encoding="utf-8"))
            rel_for_slug = dp.relative_to(dst).as_posix()
            fm = merged_fm(meta, rel_for_slug, s, sp.stem, body)
            dp.write_text(dump_fm(fm) + "\n" + body.lstrip("\n"), encoding="utf-8", newline="\n")
        elif kind == "yaml":
            dp.write_bytes(sp.read_bytes())
        elif kind == "view":
            write_view(sp, dp, dst)
        elif kind == "digest":
            rows = [json.loads(x) for x in sp.read_text(encoding="utf-8").splitlines() if x.strip()]
            module = sp.stem
            parts = [f"# {module} — 検索摘要（{len(rows)} 条）", "",
                     "> 各節は検索用に書かれた摘要であり、原文のスライスではない。",
                     "> 正本は `screens/` と `modules/` 側。", ""]
            for r in rows:
                parts.append(f"## {r.get('title') or r.get('chunk_id')}")
                parts.append("")
                if r.get("chunk_id"):
                    parts.append(f"`{r['chunk_id']}` / `{r.get('artifact_type', '')}`")
                    parts.append("")
                parts.append(str(r.get("text", "")).strip())
                parts.append("")
            body = "\n".join(parts)
            rel_for_slug = dp.relative_to(dst).as_posix()
            fm = merged_fm(
                {"id": f"KNOW-LEGACY-R60-CHUNKS-{module.upper()}", "type": "knowledge", "req_ids": [],
                 # `open` にする: `draft` は kb の DEFAULT_RETRIEVABLE に含まれず**検索に出ない**。
                 # 既存の 7 篇も `open` であり、生成し直しても状態が変わらないよう合わせてある。
                 "status": "open", "sensitivity": "internal", "owner": "AI-SE", "version": "0.1.0"},
                rel_for_slug, s, f"{module} 検索摘要", body,
            )
            dp.write_text(dump_fm(fm) + "\n" + body, encoding="utf-8", newline="\n")
        else:
            dp.write_bytes(sp.read_bytes())
        written += 1

    print(f"[kb_migrate] 書き出し {written} 件")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

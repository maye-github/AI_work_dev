"""本骨架の知識 `.md` を、社内知識基盤 `kb-platform` が読める形へ書き出す。

なぜ必要か
----------
実施規格書 §10.2 ② の「知識庫」は、本骨架では `docs/90_knowledge/` の `.md` 群でしかない。
一方、社内には既に `D:\\AI_platform\\kb-platform`（front matter ＋ chunk ＋ 索引 ＋ 検索 API）がある。
**同じ知識を二つの流儀で持つと、どちらが正か分からなくなる**（NFR-1）。

そこで本ツールは**片方向の変換器**として置く:

    機読源（本リポジトリの .md）──変換──▶ kb-platform の repo/ 配下（派生物）

- **正本は本リポジトリ**。kb-platform 側の `.md` は**手で編集しない**（次回書き出しで消える）。
- kb-platform の要求（`kbkit/pipeline.py` の `REQUIRED_KEYS`）は 8 個:
  `doc_id` / `scope` / `title` / `doc_type` / `version` / `status` / `conf_level` / `updated_at`
  （＋ `scope=project` のとき `project_id` が必須で、配置先に `projects/<project_id>/` を含むこと）。
- 本リポジトリの front-matter は 7 字段（`id`/`type`/`req_ids`/`status`/`sensitivity`/`owner`/`version`）。
  **字段名が違う**ので、機械的に対応付けるのが本ツールの仕事。

対応表
------
| kb-platform | 本リポジトリ | 備考 |
|---|---|---|
| `doc_id` | `id` | そのまま（`KNOW-LEGACY-R60-*`） |
| `scope` | — | 常に `project`（案件固有知識のため） |
| `project_id` | — | 既定 `P-R60-001`（`--project-id` で変更） |
| `title` | 本文の最初の `# 見出し` | 無ければファイル名 |
| `doc_type` | パスから決定 | 下の `DOC_TYPE_BY_PATH` |
| `version` | `version` | そのまま |
| `status` | `status` | `draft/open→draft`、`baselined/done→active`、`changed→review`、`void→deprecated` |
| `conf_level` | `sensitivity` | `internal→30`（案件）／`public→10`／`confidential→40`。既定 30 |
| `updated_at` | **git の最終コミット日** | 今日の日付を埋めない（冪等性・規則 03 §7.1） |
| `owner` | `owner` | 任意字段。あれば写す |

使い方::

    py -3 -m tools.kb_export                          # 何が書き出されるか一覧（書かない）
    py -3 -m tools.kb_export --out reports/kb-export   # 実際に書き出す（ステージング）
    py -3 -m tools.kb_export --out <dir> --kb D:/AI_platform/kb-platform
                                                      # 書き出して kb-platform の lint を回す
    py -3 -m tools.kb_export --self-test

**`--kb` は lint を回すだけで、kb-platform の repo/ へは書き込まない。**
書き込み先は `--out` で指定した場所だけである。`ingest` は人が判断してから実行する。

終了コード: 0 = 成功／1 = 読み取り・書き出しの失敗／2 = 引数誤り／3 = lint が指摘を返した。

依存は標準ライブラリ ＋ pyyaml のみ（NFR-6）。機密の実値を書かない（gate6 は tools/**/*.py も走査する）。
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

from . import paths

# 対象は「歴史案件の消化後知識」。生の抽出物（reports/legacy-raw）は対象外
# （案件が特定できる実データを含むため。01-security-redlines.md §10）。
DEFAULT_SOURCE = "docs/90_knowledge/legacy-r60"

# パスの形 → kb-platform の doc_type（pipeline.py の DOC_TYPES のいずれか）
DOC_TYPE_BY_PATH: list[tuple[str, str]] = [
    (r"screens/", "design-basic"),
    (r"02-architecture", "design-detail"),
    (r"05-database", "design-detail"),
    (r"06-api", "design-detail"),
    (r"03-conventions", "standard"),
    (r"04-common-parts", "standard"),
    (r"07-traceability", "standard"),
    (r"08-deviations", "decision"),
    (r"module-selection", "decision"),
]
DEFAULT_DOC_TYPE = "howto"

# 本リポジトリの status → kb-platform の status
STATUS_MAP = {
    "draft": "draft",
    "open": "draft",
    "baselined": "active",
    "done": "active",
    "changed": "review",
    "void": "deprecated",
}

# 本リポジトリの sensitivity → kb-platform の conf_level
# 10 公開 / 20 社内 / 30 案件 / 40 機密
CONF_MAP = {"public": 10, "internal": 30, "confidential": 40}
DEFAULT_CONF = 30

KB_REQUIRED = ["doc_id", "scope", "title", "doc_type", "version", "status", "conf_level", "updated_at"]

# ---- 以下は kb-platform `kbkit/pipeline.py` の lint 規則の写し ----
# 本家の lint は `numpy` を要求するため、numpy の無い環境では回せない。
# 規則が変わったら**本家を正として**この写しを直すこと（写しは従）。
KB_SCOPES = {"company", "project"}
KB_STATUSES = {"draft", "review", "active", "deprecated"}
KB_DOC_TYPES = {
    "standard", "pattern", "glossary", "requirement",
    "design-basic", "design-detail", "test", "decision",
    "incident", "howto",
}
KB_CONF_LEVELS = {10, 20, 30, 40}
KB_MIN_TITLE = 4


# --------------------------------------------------------------------------
# 補助
# --------------------------------------------------------------------------

def _git_date(root: Path, rel_path: str) -> str:
    """そのファイルの最終コミット日（YYYY-MM-DD）。無ければ空。

    **今日の日付を使わない。** 同じリポジトリ状態からは何度書き出しても同じ結果にするため
    （規則 03 §7.1 の冪等性）。
    """
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%ad", "--date=short", "--", rel_path],
            cwd=str(root), capture_output=True, text=True, encoding="utf-8",
            errors="replace", check=False,
        ).stdout.strip()
        return out
    except Exception:
        return ""


def _title_of(body: str, fallback: str) -> str:
    """本文の最初の `# ` 見出し。無ければファイル名。"""
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("# "):
            return s[2:].strip()
    return fallback


def _doc_type_of(rel_posix: str) -> str:
    for pat, dtype in DOC_TYPE_BY_PATH:
        if re.search(pat, rel_posix):
            return dtype
    return DEFAULT_DOC_TYPE


def _quote(v: str) -> str:
    """kb-platform の front matter パーサは YAML サブセットなので、
    先頭が `-` や `[` の値だけ引用する（それ以外は素のまま置く）。"""
    if not v:
        return '""'
    if v[0] in "-[{\"'":
        return '"' + v.replace('"', "") + '"'
    return v


# --------------------------------------------------------------------------
# 変換
# --------------------------------------------------------------------------

def build_entries(root: Path, source: str, project_id: str) -> list[dict]:
    """ソース配下の `.md` を読み、kb-platform 用の 1 文書ずつに組み替える。"""
    src = root / source
    if not src.is_dir():
        raise FileNotFoundError(f"知識のソースがありません: {source}")

    entries: list[dict] = []
    for p in sorted(src.rglob("*.md")):
        rel_posix = p.relative_to(root).as_posix()
        rel_in_src = p.relative_to(src).as_posix()
        text = p.read_text(encoding="utf-8")

        meta: dict = {}
        body = text
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                try:
                    meta = yaml.safe_load(parts[1]) or {}
                except Exception:
                    meta = {}
                body = parts[2]

        doc_id = str(meta.get("id") or "").strip()
        if not doc_id:
            doc_id = "KNOW-" + re.sub(r"[^A-Za-z0-9]+", "-", rel_in_src).strip("-").upper()

        status_raw = str(meta.get("status") or "draft").strip()
        sens = str(meta.get("sensitivity") or "internal").strip()

        fm = {
            "doc_id": doc_id,
            "scope": "project",
            "project_id": project_id,
            "title": _title_of(body, p.stem),
            "doc_type": _doc_type_of(rel_in_src),
            "version": str(meta.get("version") or "0.1.0"),
            "status": STATUS_MAP.get(status_raw, "draft"),
            "conf_level": CONF_MAP.get(sens, DEFAULT_CONF),
            "updated_at": _git_date(root, rel_posix) or "1970-01-01",
        }
        if meta.get("owner"):
            fm["owner"] = str(meta["owner"])

        entries.append({
            "source": rel_posix,
            "target": f"projects/{project_id}/{rel_in_src}",
            "fm": fm,
            "body": body.lstrip("\n"),
        })
    return entries


def render_entry(entry: dict) -> str:
    """front matter ＋ 本文の 1 本のテキストへ。"""
    lines = ["---"]
    for k in KB_REQUIRED:
        lines.append(f"{k}: {_quote(str(entry['fm'][k]))}")
        # project_id は REQUIRED_KEYS には無いが、scope=project のとき本家 lint が要求する
        if k == "scope" and entry["fm"].get("project_id"):
            lines.append(f"project_id: {_quote(str(entry['fm']['project_id']))}")
    if "owner" in entry["fm"]:
        lines.append(f"owner: {_quote(entry['fm']['owner'])}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines) + "\n" + entry["body"]


def write_entries(entries: list[dict], out_dir: Path, project_id: str) -> int:
    """ステージング先へ書き出す。

    **消すのは `out_dir/projects/<project_id>/` の 1 本だけ。**
    `--out` に kb-platform の `repo/` を誤って指しても、他の案件の文書は消えない
    （`repo/` ごと rmtree すると他人の知識を消す事故になる）。
    """
    proj_dir = out_dir / "projects" / project_id
    if proj_dir.exists():
        shutil.rmtree(proj_dir)
    for e in entries:
        dest = out_dir / e["target"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(render_entry(e), encoding="utf-8")
    return len(entries)


def local_lint(repo_dir: Path) -> list[str]:
    """kb-platform `pipeline.lint` の規則を写した検査（numpy 不要）。

    本家と**同じ規則**を同じ順で見る。違うのは実装だけで、判定は同じになるはずである。
    `--kb` を付ければ本家を回すので、numpy がある環境ではそちらを正とすること。
    """
    issues: list[str] = []
    root = repo_dir
    seen_ids: dict[str, str] = {}
    for p in sorted(root.rglob("*.md")):
        rel = p.relative_to(root).as_posix()
        if rel.startswith("eval/") or rel.startswith("."):
            continue
        text = p.read_text(encoding="utf-8")
        if not text.startswith("---"):
            issues.append(f"{rel}: front matter がありません")
            continue
        parts = text.split("---", 2)
        if len(parts) < 3:
            issues.append(f"{rel}: front matter を解析できません")
            continue
        try:
            meta = yaml.safe_load(parts[1]) or {}
        except Exception as e:
            issues.append(f"{rel}: front matter を解析できません: {e}")
            continue
        body = parts[2]

        for k in KB_REQUIRED:
            if meta.get(k) in (None, ""):
                issues.append(f"{rel}: 必須キー '{k}' がありません")

        doc_id = str(meta.get("doc_id") or "")
        if doc_id:
            if doc_id in seen_ids:
                issues.append(f"{rel}: doc_id '{doc_id}' が {seen_ids[doc_id]} と重複")
            seen_ids[doc_id] = rel
            if not doc_id.replace("-", "").isalnum():
                issues.append(f"{rel}: doc_id は英数字とハイフンのみ: '{doc_id}'")

        if meta.get("scope") not in KB_SCOPES:
            issues.append(f"{rel}: scope は {sorted(KB_SCOPES)} のいずれか: {meta.get('scope')!r}")
        if meta.get("doc_type") not in KB_DOC_TYPES:
            issues.append(f"{rel}: doc_type が不正: {meta.get('doc_type')!r}")
        if meta.get("status") not in KB_STATUSES:
            issues.append(f"{rel}: status が不正: {meta.get('status')!r}")
        try:
            if int(meta.get("conf_level")) not in KB_CONF_LEVELS:
                issues.append(f"{rel}: conf_level は {sorted(KB_CONF_LEVELS)} のいずれか")
        except (TypeError, ValueError):
            issues.append(f"{rel}: conf_level が整数ではありません")

        title = str(meta.get("title") or "")
        if len(title) < KB_MIN_TITLE:
            issues.append(f"{rel}: title が短すぎます: {title!r}")

        pid = meta.get("project_id")
        if meta.get("scope") == "project":
            if not pid:
                issues.append(f"{rel}: scope=project には project_id が必須です")
            elif f"projects/{pid}/" not in rel:
                issues.append(f"{rel}: project_id '{pid}' と配置先ディレクトリが不一致")
        elif meta.get("scope") == "company" and pid:
            issues.append(f"{rel}: scope=company に project_id は指定できません")

        if not body.strip():
            issues.append(f"{rel}: 本文が空です")
    return issues


def run_kb_lint(kb_path: Path, repo_dir: Path) -> tuple[int, str]:
    """kb-platform の `lint` を回す（読み取りのみ）。"""
    run_py = kb_path / "run.py"
    if not run_py.is_file():
        return 2, f"kb-platform の run.py が見つかりません: {run_py}"
    proc = subprocess.run(
        [sys.executable, str(run_py), "lint", "--repo", str(repo_dir)],
        cwd=str(kb_path), capture_output=True, text=True,
        encoding="utf-8", errors="replace", check=False,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


# --------------------------------------------------------------------------
# 自己テスト
# --------------------------------------------------------------------------

def self_test() -> int:
    paths.reconfigure_stdout()
    ok = total = 0

    total += 1
    if _doc_type_of("screens/R60Area.md") == "design-basic" and _doc_type_of("09-ai-workflow.md") == "howto":
        ok += 1
        print("[kb_export:self-test] ok   doc_type の対応")
    else:
        print("[kb_export:self-test] FAIL doc_type の対応")

    total += 1
    if STATUS_MAP["baselined"] == "active" and STATUS_MAP["void"] == "deprecated" and CONF_MAP["internal"] == 30:
        ok += 1
        print("[kb_export:self-test] ok   status / conf_level の対応")
    else:
        print("[kb_export:self-test] FAIL status / conf_level の対応")

    total += 1
    fake = {
        "source": "x.md",
        "target": "projects/P-X/x.md",
        "fm": {
            "doc_id": "KNOW-X", "scope": "project", "project_id": "P-X",
            "title": "t", "doc_type": "howto", "version": "0.1.0",
            "status": "draft", "conf_level": 30, "updated_at": "2026-01-01",
        },
        "body": "# t\n\n本文\n",
    }
    text = render_entry(fake)
    # kb-platform のパーサと同じ規則（最初の `:` で分割）で読み戻せることを確かめる
    got = {}
    for line in text.split("---")[1].strip().splitlines():
        k, _, v = line.partition(":")
        got[k.strip()] = v.strip()
    if all(k in got for k in KB_REQUIRED) and got.get("project_id") == "P-X" and got["conf_level"] == "30":
        ok += 1
        print("[kb_export:self-test] ok   render_entry が 8 字段＋project_id を出す")
    else:
        print(f"[kb_export:self-test] FAIL render_entry: {sorted(got)}")

    print(f"[kb_export:self-test] {'PASS' if ok == total else 'FAIL'} {ok}/{total} pass")
    return 0 if ok == total else 1


# --------------------------------------------------------------------------
# エントリポイント
# --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="py -3 -m tools.kb_export",
        description="本骨架の知識 .md を kb-platform が読める形へ書き出す（既定は下見）。",
    )
    ap.add_argument("--source", default=DEFAULT_SOURCE, help=f"知識のソース（既定 {DEFAULT_SOURCE}）")
    ap.add_argument("--out", metavar="DIR", help="書き出し先。省略すると一覧を出すだけで書かない")
    ap.add_argument("--project-id", default="P-R60-001", help="kb-platform の案件 ID（既定 P-R60-001）")
    ap.add_argument("--kb", metavar="DIR",
                    help="kb-platform のルート。指定すると本家 lint を回す（numpy が必要）")
    ap.add_argument("--check", action="store_true",
                    help="書き出した後、本家 lint の規則を写した検査を回す（numpy 不要）")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()

    root = paths.find_root(Path.cwd())
    paths.reconfigure_stdout()

    try:
        entries = build_entries(root, args.source, args.project_id)
    except Exception as e:
        print(f"[kb_export] 読み取りに失敗しました: {e}", file=sys.stderr)
        return 1

    print(f"# kb-platform 書き出し — {args.source} → projects/{args.project_id}/")
    print()
    print(f"対象 {len(entries)} 本。")
    print()
    print("| # | 出力先 | doc_id | doc_type | status | conf | updated_at |")
    print("|---|---|---|---|---|---|---|")
    for i, e in enumerate(entries, 1):
        f = e["fm"]
        print(f"| {i} | `{e['target']}` | `{f['doc_id']}` | {f['doc_type']} | {f['status']} | {f['conf_level']} | {f['updated_at']} |")
    print()

    if not args.out:
        print("> 下見のみ（`--out` を付けると書き出します）。", file=sys.stderr)
        return 0

    out = Path(args.out)
    n = write_entries(entries, out, args.project_id)
    print(f"[kb_export] {n} 本を書き出しました: {out}", file=sys.stderr)

    if args.check:
        issues = local_lint(out)
        if issues:
            print(f"[kb_export] 規則検査: {len(issues)} 件の指摘", file=sys.stderr)
            for i in issues:
                print("  - " + i, file=sys.stderr)
            return 3
        print("[kb_export] 規則検査: PASS（8 字段・列挙値・配置・本文、すべて本家 lint と同規則）",
              file=sys.stderr)

    if args.kb:
        code, text = run_kb_lint(Path(args.kb), out)
        print(f"[kb_export] kb-platform lint（exit {code}）:", file=sys.stderr)
        print(text, file=sys.stderr)
        if code != 0:
            return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""知識ベースの更新・削除権限を検査する。

権限モデル（`owners.yaml` が正本・`kb-policy.md` §3 が運用）
----------------------------------------------------------
- **会社級** `repo/company/**` … 会社の責任者だけが更新・削除できる
- **案件級** `repo/projects/<P>/**` … その案件の責任者（PM）だけが更新・削除できる
- **結案済み**（`projects/<P>/CLOSED.md` がある）… 読み取り専用。誰も更新・削除できない

使い方
------
    py -3 -m tools.kb_acl show                       # 権限表を表示（只读）
    py -3 -m tools.kb_acl verify                     # owners.yaml の形を検査
    py -3 -m tools.kb_acl check --by <人> --from-git # 変更予定ファイルを git から取って検査
    py -3 -m tools.kb_acl check --by <人> --changed tools/kb-platform/repo/company/x.md

★ 本ツールの強制力には限界がある。**リポジトリへの直接書き込みを物理的に止めるものではない。**
  止めるのは 2 層で行う：
    1. 本ツール（＋ CI / pre-commit）… 変更を検出して落とす
    2. Git のブランチ保護 ＋ CODEOWNERS … マージを止める（サーバ側の設定）
  どちらか片方だけでは「うっかり」は防げても「故意」は防げない。両方そろえて初めて統制になる。

★ 承認は人がする（紅線③）。本ツールは「その人がその範囲の責任者か」を見るだけで、
  「その変更が妥当か」は見ない。妥当性はレビューで担保する。
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
KB = "tools/kb-platform"
OWNERS_REL = f"{KB}/owners.yaml"
REPO_REL = f"{KB}/repo"


def _owners_path(root: Path) -> Path:
    return root / OWNERS_REL


def load_owners(root: Path) -> dict:
    path = _owners_path(root)
    if not path.is_file():
        raise SystemExit(f"[kb_acl] 権限表がありません: {OWNERS_REL}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise SystemExit(f"[kb_acl] 権限表を読めません: {exc}")
    if not isinstance(data, dict):
        raise SystemExit("[kb_acl] 権限表の形式が不正です")
    data.setdefault("company", {})
    data.setdefault("projects", {})
    return data


def classify(rel: str) -> tuple[str | None, str | None]:
    """変更ファイルの属する範囲を返す。(scope, project_id)。

    scope … `company` / `project` / `owners` / None（統制対象外）
    """
    rel = rel.replace("\\", "/").lstrip("./")
    if rel == OWNERS_REL:
        return "owners", None
    if rel.startswith(f"{REPO_REL}/company/"):
        return "company", None
    rest = rel[len(f"{REPO_REL}/projects/"):] if rel.startswith(f"{REPO_REL}/projects/") else ""
    if rest:
        return "project", rest.split("/", 1)[0]
    return None, None


def project_closed(root: Path, project: str) -> bool:
    return (root / REPO_REL / "projects" / project / "CLOSED.md").exists()


def allowed_projects(user: str, root: Path) -> set[str]:
    """`user` が**読める**案件の集合（読権限）。

    - 案件の `owner` と `members` に載っている人が読める
    - **会社の責任者（と代理）は全案件を読める**（統制の最終責任者なので当然）
    - それ以外は会社級だけ（案件級は 1 件も返らない）
    """
    owners = load_owners(root)
    projects = owners["projects"] or {}
    if not user:
        return set()
    company_owner = owners["company"].get("owner")
    delegates = set(owners["company"].get("delegates") or [])
    if company_owner and (user == company_owner or user in delegates):
        return set(projects.keys())

    out: set[str] = set()
    for name, info in projects.items():
        members = set(info.get("members") or [])
        if info.get("owner"):
            members.add(info["owner"])
        if user in members:
            out.add(name)
    return out


def check(changed: list[str], by: str, root: Path) -> list[str]:
    """違反の一覧を返す（空なら合格）。"""
    owners = load_owners(root)
    company_owner = owners["company"].get("owner")
    delegates = owners["company"].get("delegates") or []
    problems: list[str] = []

    for rel in changed:
        scope, project = classify(rel)
        if scope is None:
            continue
        if not by:
            problems.append(f"{rel}: 操作者の識別子がありません（--by）")
            continue

        if scope == "owners":
            if not company_owner:
                problems.append(f"{rel}: 会社級の責任者が未任命（owners.yaml を誰も更新できない）")
            elif by != company_owner:
                problems.append(f"{rel}: 権限表は会社の責任者だけが更新できます（{by} ≠ {company_owner}）")
            continue

        if scope == "company":
            if not company_owner:
                problems.append(f"{rel}: 会社級の責任者が未任命（`owners.yaml` company.owner）")
            elif by != company_owner and by not in delegates:
                problems.append(
                    f"{rel}: 会社級は会社の責任者だけが更新・削除できます（{by} は対象外）"
                )
            continue

        # scope == "project"
        info = (owners["projects"] or {}).get(project) or {}
        if project_closed(root, project):
            problems.append(
                f"{rel}: 案件 {project} は結案済み（読み取り専用）。"
                "再開するときは CLOSED.md に理由と日付を追記し、人が裁定する"
            )
            continue
        owner = info.get("owner")
        if not owner:
            problems.append(f"{rel}: 案件 {project} の責任者が未任命（`owners.yaml` projects.{project}.owner）")
        elif by != owner:
            problems.append(
                f"{rel}: 案件 {project} は案件責任者だけが更新・削除できます（{by} ≠ {owner}）"
            )
    return problems


def verify(root: Path) -> list[str]:
    """権限表そのものの形を検査する。"""
    owners = load_owners(root)
    issues: list[str] = []
    company = owners["company"]
    if not isinstance(company, dict):
        issues.append("`company` は辞書であること")
    elif "owner" not in company:
        issues.append("`company.owner` が無い（未任命なら null を明示する）")
    for name, info in (owners["projects"] or {}).items():
        if not isinstance(info, dict):
            issues.append(f"`projects.{name}` は辞書であること")
            continue
        if "owner" not in info:
            issues.append(f"`projects.{name}.owner` が無い（未任命なら null を明示する）")
        status = info.get("status", "open")
        if status not in {"open", "closed"}:
            issues.append(f"`projects.{name}.status` は open / closed のいずれか")
        closed_marker = project_closed(root, name)
        if status == "closed" and not closed_marker:
            issues.append(f"`projects.{name}` は status: closed だが CLOSED.md が無い")
        if status == "open" and closed_marker:
            issues.append(f"`projects.{name}` に CLOSED.md があるのに status: open")
    return issues


def _git_changed(root: Path) -> list[str]:
    """git から変更ファイル一覧を取る。

    ★ `text=True` だけでは Windows で cp932 解釈になり、日本語・中国語のパスで落ちる。
      必ず `encoding="utf-8"` を明示する（git は UTF-8 でパスを出す）。
    """
    def run(args: list[str]) -> str:
        return subprocess.run(
            args, cwd=root, capture_output=True, check=True,
            encoding="utf-8", errors="replace",
        ).stdout

    try:
        out = run(["git", "diff", "--name-only", "HEAD"])
        untracked = run(["git", "ls-files", "--others", "--exclude-standard"])
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"[kb_acl] git から変更を取れません: {exc}")
    return [line for line in (out + "\n" + untracked).splitlines() if line.strip()]


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    ap = argparse.ArgumentParser(prog="tools.kb_acl", description="知識ベースの更新・削除権限")
    ap.add_argument("--root", default=str(ROOT))
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("show", help="権限表を表示（只读）")
    sub.add_parser("verify", help="owners.yaml の形を検査")

    c = sub.add_parser("check", help="変更ファイルが権限内かを検査")
    c.add_argument("--by", default="", help="操作者の識別子（紅線③）")
    c.add_argument("--changed", nargs="*", default=None, help="変更ファイル（リポジトリ相対）")
    c.add_argument("--from-git", action="store_true", help="git の変更一覧を使う")

    args = ap.parse_args(argv)
    root = Path(args.root).resolve()

    if args.cmd == "show":
        owners = load_owners(root)
        company = owners["company"]
        print("[kb_acl] 権限表")
        print(f"  会社級 (repo/company/**)        : {company.get('owner') or '未任命'}")
        if company.get("delegates"):
            print(f"    代理                          : {', '.join(company['delegates'])}")
        for name, info in sorted((owners["projects"] or {}).items()):
            mark = " [結案・読み取り専用]" if project_closed(root, name) else ""
            members = set(info.get("members") or [])
            if info.get("owner"):
                members.add(info["owner"])
            who = ", ".join(sorted(members)) if members else "（読める人はいない）"
            print(f"  案件級 {name:<12} 更新: {info.get('owner') or '未任命':<6} 読取: {who}{mark}")
        return 0

    if args.cmd == "verify":
        issues = verify(root)
        if issues:
            print(f"[kb_acl] 権限表に {len(issues)} 件の問題:")
            for issue in issues:
                print(f"  - {issue}")
            return 1
        print("[kb_acl] 権限表 OK")
        return 0

    # check
    changed = args.changed if args.changed is not None else (_git_changed(root) if args.from_git else [])
    if not changed:
        print("[kb_acl] 検査対象がありません（--changed か --from-git）", file=sys.stderr)
        return 2
    problems = check(changed, args.by, root)
    governed = [(rel, *classify(rel)) for rel in changed]
    governed = [g for g in governed if g[1] is not None]
    if problems:
        print(f"[kb_acl] 権限違反 {len(problems)} 件（統制対象 {len(governed)} 件 / 全 {len(changed)} 件）:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"[kb_acl] OK（統制対象 {len(governed)} 件 / 全 {len(changed)} 件。操作者: {args.by or '未指定'}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

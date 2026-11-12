"""`tools/kb_local` の CLI。上流 `run.py` の CLI に `--module` / `--scope` と節評価を足したもの。

    py -3 -m tools.kb_local search "..." --project P-R60-001 --module R60Ssk
    py -3 -m tools.kb_local eval
    py -3 -m tools.kb_local lint
    py -3 -m tools.kb_local ingest --prune     # 上流 run.py へ委譲 → 退避表を追従
    py -3 -m tools.kb_local stats              # 上流 run.py へそのまま委譲
    py -3 -m tools.kb_local extra report       # 出处（source_project）と req_ids の有無

なぜ「上流 CLI を使わない」のか
------------------------------
上流の `search` は `status = 'active'` の文書しか拾わず、`lint` は骨架の状態語彙
（`open` / `baselined` / …）を知らない。我々の文書はその語彙で書かれているため、
上流 CLI をそのまま叩くと **検索 0 件・lint NG** になる。差分はこの層だけに置く。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

from tools.kb_local import _bootstrap
from tools.kb_local._bootstrap import _pipeline, _retrieval  # noqa: F401
from tools.kb_local.evaluation import evaluate, format_report
from tools.kb_local.retrieval import search

VENDOR = _bootstrap.VENDOR
DEFAULT_REPO = VENDOR / "repo"
DEFAULT_DB = VENDOR / "data" / "kb.sqlite3"
DEFAULT_GOLDEN = VENDOR / "repo" / "eval" / "golden.yaml"

#: 上流の実装をそのまま使うコマンド（我々の差分が要らないもの）。
#: `ingest` は委譲したあとに退避表を追従させるため、`cmd_ingest` で包む。
DELEGATED = {"stats"}


def _out(text: str = "") -> None:
    print(text)


def _effective_user(as_user: str | None) -> tuple[str | None, str]:
    """実際に使う操作者と、その出所を返す。

    `--as` が無ければ `whoami.txt`（端末に 1 回だけ設定した名前）を使う。
    **どちらも無ければ「制限なし」ではなく会社級だけ**——既定は拒否のまま。
    """
    if as_user:
        return as_user, "--as"
    from tools.kb_local import whoami

    saved = whoami.get(_bootstrap.ROOT)
    if saved:
        return saved, "whoami"
    return None, ""


def _resolve_allowed(as_user: str | None,
                     allow_all: bool) -> tuple[set[str] | None, str | None, str]:
    """(読める案件の集合, 実効の操作者, 出所) を返す（**既定は拒否**）。

    - `--as <人>` / `whoami` … その人が所属する案件だけ（会社級は常に見える）
    - `--all`                … 制限なし（管理者。測定・保守のための明示的な逃げ道）
    - どちらも無い            … **会社級だけ**。案件級は 1 件も返らない
    """
    if as_user and allow_all:
        raise SystemExit("[kb_local] --as と --all は同時に指定できません")
    if allow_all:
        return None, None, "--all"
    user, source = _effective_user(as_user)
    if not user:
        return set(), None, ""
    from tools.kb_acl import allowed_projects

    return allowed_projects(user, _bootstrap.ROOT), user, source


def _describe_scope(user: str | None, source: str, allow_all: bool,
                    allowed: set[str] | None) -> str:
    if allow_all:
        return "制限なし（--all）"
    if user:
        names = ", ".join(sorted(allowed or [])) or "（どの案件にも所属していない）"
        origin = "whoami" if source == "whoami" else "--as"
        return f"{user}（{origin}）の所属案件: {names} ＋ 会社級"
    return "会社級のみ（誰も名乗っていない）"


def _upstream_main(argv: list[str]) -> int:
    """上流 `run.py` の `main()` を、書き換えずに呼ぶ。"""
    spec = importlib.util.spec_from_file_location("kb_upstream_run", VENDOR / "run.py")
    if spec is None or spec.loader is None:
        raise SystemExit(f"上流 CLI を読み込めません: {VENDOR / 'run.py'}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.main(argv)


def cmd_lint(rest: list[str]) -> int:
    """上流 lint を、状態語彙と文書種別を広げた状態で実行する（出力は上流と同一）。"""
    with _bootstrap.wider_statuses(), _bootstrap.wider_doc_types():
        return _upstream_main(["lint", *rest])


def cmd_ingest(rest: list[str]) -> int:
    """上流 ingest に委譲し、成功したら退避表（kb_doc_extra）を追従させる。

    退避表は我々の持ち物であり上流は知らないため、ingest の後に必ず同期を打つ。
    これを忘れると、front matter に書いた `source_project` / `req_ids` が
    索引から落ちたままになる（出处の検査が「空だから合格」に見える）。
    """
    from tools.kb_local import index_extra

    rc = _upstream_main(["ingest", *rest])
    if rc != 0:
        return rc
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--repo", default=str(DEFAULT_REPO))
    known, rest_args = ap.parse_known_args(rest)
    stats = index_extra.sync(Path(known.repo), Path(known.db))
    _out(
        f"[kb_local] 退避表を追従: {stats['written']}/{stats['indexed']} 件"
        f"（source_project {stats['with_source']} 件 / req_ids {stats['with_req']} 件）"
    )
    return 0


def cmd_extra(rest: list[str]) -> int:
    """出处（source_project）と要求紐付け（req_ids）の退避表を扱う。"""
    from tools.kb_local import index_extra

    ap = argparse.ArgumentParser(prog="tools.kb_local extra",
                                 description="出处と req_ids の退避表")
    ap.add_argument("action", nargs="?", choices=["sync", "report"], default="report")
    ap.add_argument("--self-test", action="store_true", help="合成データで自己検証する")
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--repo", default=str(DEFAULT_REPO))
    args = ap.parse_args(rest)

    if args.self_test:
        return index_extra._self_test()

    if args.action == "sync":
        stats = index_extra.sync(Path(args.repo), Path(args.db))
        _out(f"[extra] sync: {stats['written']}/{stats['indexed']} 件"
             f"（source_project {stats['with_source']} / req_ids {stats['with_req']}）")
        return 0

    rep = index_extra.report(Path(args.db))
    _out(f"[extra] 退避表 {rep['total']} 件（会社級 {rep['company_total']} / 案件級 {rep['project_total']}）")
    _out(f"  会社級の source_project: {rep['company_with_source']}/{rep['company_total']} 件")
    _out(f"  req_ids あり: {rep['with_req']} 件")
    if rep["company_missing"]:
        _out(f"  未記入 {len(rep['company_missing'])} 件（ガイド §2.2④「有出处」）:")
        for doc_id in rep["company_missing"][:20]:
            _out(f"    - {doc_id}")
        if len(rep["company_missing"]) > 20:
            _out(f"    … 他 {len(rep['company_missing']) - 20} 件")
    if rep["company_invalid"]:
        _out(f"  形が不正 {len(rep['company_invalid'])} 件（案件 ID か "
             f"{'/'.join(sorted(index_extra.LEGAL_SOURCE_MARKERS))} のいずれか）:")
        for doc_id, value in rep["company_invalid"][:20]:
            _out(f"    - {doc_id}: {value!r}")
    _out("  ※ 案件級条目の出処は `project_id` が持つ（`source_project` は書かない）")
    return 0


def cmd_search(rest: list[str]) -> int:
    from kbkit.embedder import get_embedder
    from kbkit.retrieval import build_context
    from kbkit import store

    ap = argparse.ArgumentParser(prog="tools.kb_local search", description="検索")
    ap.add_argument("query")
    ap.add_argument("--project", default=None, help="案件ID（例: P-R60-001）")
    ap.add_argument("--module", default=None,
                    help="モジュールで絞る（例: R60Ssk）。doc_id / title の部分一致")
    ap.add_argument("--scope", default=None, choices=["company", "project"],
                    help="会社共通だけ / 案件知識だけ に絞る")
    ap.add_argument("--level", type=int, default=30, help="利用者の権限レベル")
    ap.add_argument("--as", dest="as_user", default=None,
                    help="利用者名（読権限。所属案件の知識だけが見える）")
    ap.add_argument("--all", dest="all", action="store_true",
                    help="読権限を外す（管理者。測定・保守用）")
    ap.add_argument("--for-external", dest="for_external", action="store_true",
                    help="対外文書用。client_only(L40) を必ず除外する")
    ap.add_argument("--no-expand", dest="no_expand", action="store_true",
                    help="用語集による検索語の拡張を行わない")
    ap.add_argument("--exclude-derived", dest="exclude_derived", action="store_true",
                    help="検索摘要（chunks/）を候補から外す（既定は含める・実測で recall が下がる）")
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--context", action="store_true", help="LLM 用コンテキストも出力")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--repo", default=str(DEFAULT_REPO))
    ap.add_argument("--embedder", default="hash", choices=["hash", "bge"])
    args = ap.parse_args(rest)

    allowed, user, source = _resolve_allowed(args.as_user, args.all)
    if not args.all and not user and args.project:
        print("[kb_local] 案件級の知識を読むには身元が要ります（次のどちらか）。", file=sys.stderr)
        print("            py -3 -m tools.kb_local whoami --set <名前>   # 端末に 1 回だけ", file=sys.stderr)
        print("            または --as <名前> を付ける", file=sys.stderr)
        return 2

    scope_note = _describe_scope(user, source, args.all, allowed)
    if args.for_external:
        # `client_only`(L40) は「見せる相手」ではなく「外へ出せない」の印である。
        # 権限レベルが 40 でも、対外文書用の検索では落とす（ガイド §4.7）。
        if args.level > 30:
            _out("[kb_local] --for-external: 権限レベルを 30 に下げます（L40 は対外禁止）")
            args.level = 30
        scope_note += "／対外用（L40 除外）"
    _out(f"[kb_local] 読取範囲: {scope_note}")

    embedder = get_embedder(args.embedder)
    conn = store.connect(args.db)
    store.init_schema(conn)

    # 用語集から中日英の対応を取り、質問に含まれる中文・English の語を日本語で補う。
    # **足した語は画面に出す**——何で当たったかが分からない検索は信用できない。
    query = args.query
    if not args.no_expand:
        from tools.kb_local import synonyms

        lexicon = synonyms.build(conn, Path(args.repo))
        query, applied = synonyms.expand(args.query, lexicon)
        if applied:
            pairs = ", ".join(f"{alias}→{jp}" for alias, jp in applied[:5])
            more = "" if len(applied) <= 5 else f" …他 {len(applied) - 5} 件"
            _out(f"[kb_local] 検索語を拡張: {pairs}{more}")

    results = search(
        conn, query, embedder,
        project_id=args.project, user_level=args.level, top_k=args.top_k,
        module=args.module, scope=args.scope, allowed_projects=allowed,
        exclude_derived=args.exclude_derived,
    )
    if args.json:
        _out(json.dumps(results, ensure_ascii=False, indent=2))
        return 0
    if not results:
        _out("ヒットなし")
        return 0
    weak = 0
    derived_count = 0
    for i, r in enumerate(results, 1):
        markers = r.get("markers") or []
        weak_marks = [m for m in markers if m in ("推測", "差異")]
        strong_marks = [m for m in markers if m not in ("推測", "差異")]
        tag = "".join(f"【{m}】" for m in weak_marks)
        if strong_marks:
            tag += f"[{'・'.join(strong_marks)}]"
        if r.get("derived"):
            tag += "[摘要]"
            derived_count += 1
        if weak_marks:
            weak += 1
        head = f"{i}. [{r['score']:.4f}] " + (f"{tag} " if tag else "") + r["citation"]
        _out(head)
        body = r["text"].replace("\n", " ")
        if len(body) > 140:
            body = body[:140] + "…"
        _out(f"   {body}")
    if derived_count:
        _out("※ [摘要] は検索用に書き直した要約です。正本（modules/・screens/）を確認してください。")
    if weak:
        _out(f"※ {len(results)} 件中 {weak} 件が【推測】または【差異】を含みます。"
             "確定値として使う前に別途確認してください。")
    if args.context:
        _out("\n--- context ---")
        _out(build_context(results))
    return 0


def cmd_check_constraints(rest: list[str]) -> int:
    """知識が要求する「形」を成果物が満たしているか検査する。"""
    from tools.kb_local import constraint_check

    return constraint_check.main(rest)


def cmd_node_brief(rest: list[str]) -> int:
    """節点の必読条目を AI の入力用に取り出す。"""
    from tools.kb_local import node_brief

    return node_brief.main(rest)


def cmd_check_knowledge(rest: list[str]) -> int:
    """`knowledge/` の条目が決められた形か検査する（内容の正しさは見ない）。"""
    from tools.kb_local import knowledge_check

    return knowledge_check.main(rest)


def cmd_project_init(rest: list[str]) -> int:
    """新しい案件の知識庫を scaffold する。

        py -3 -m tools.kb_local project-init --id P-XXX-001 --name "案件名" --by <PM>

    役割を混ぜない:
      sources/    … 人が原本を置く場所（xlsx/docx/pdf/md）。AI は生成しない・編集しない
      extracted/  … `import --scan` が sources から機械抽出したテキスト（status: draft）
      knowledge/ modules/ playbooks/ glossary/ review/ chunks/
                  … AI が sources/extracted をもとに生成する知識（人が確認して open）

    冪等。既存のディレクトリ・ファイルは上書きしない。
    """
    import datetime

    ap = argparse.ArgumentParser(prog="tools.kb_local project-init")
    ap.add_argument("--id", required=True, help="案件 ID（例: P-XXX-001）")
    ap.add_argument("--name", required=True, help="案件名")
    ap.add_argument("--by", required=True, help="責任者（人。紅線③）")
    ap.add_argument("--repo", default=str(DEFAULT_REPO))
    a = ap.parse_args(rest)

    pdir = Path(a.repo) / "projects" / a.id
    made = []
    for sub in ("sources", "extracted", "knowledge", "modules", "playbooks",
                "glossary", "review", "chunks"):
        d = pdir / sub
        if not d.is_dir():
            d.mkdir(parents=True, exist_ok=True)
            made.append(sub)

    readme = pdir / "sources" / "README.md"
    if not readme.is_file():
        lines = [
            "# sources/ — 原本を置く場所",
            "",
            "このフォルダには**人が原本を置く**。AI はここを生成しない・編集しない。",
            "",
            "- 置いてよい: 設計書・仕様書・マスタ定義・QA 票・会議資料（xlsx / docx / pdf / md / txt）",
            "- 置かない: 接続情報・パスワード・実データの実値（`kb-policy.md` §2.1）",
            "",
            "## 置いたあと",
            "",
            "```bash",
            f"py -3 -m tools.kb_local import --scan --project {a.id} --by <PM>",
            "```",
            "",
            "抽出結果は `extracted/` に出る（`status: draft`）。原本と突き合わせて `open` にした後、",
            "AI が `knowledge/` などへ整理する。",
            "",
        ]
        readme.write_text(chr(10).join(lines), encoding="utf-8")
        made.append("sources/README.md")

    pfile = pdir / "project.yml"
    if not pfile.is_file():
        meta = [
            "# 案件メタ（人向けの入口。索引には入れない）",
            f"project_id: {a.id}",
            'name: "%s"' % a.name,
            f'owner: "{a.by}"',
            f'created_at: "{datetime.date.today().isoformat()}"',
            "",
        ]
        pfile.write_text(chr(10).join(meta), encoding="utf-8")
        made.append("project.yml")

    # 権限台帳に案件責任者を登録する（無いと import / ingest が「未任命」で止まる）。
    owners = VENDOR / "owners.yaml"
    if owners.is_file():
        text = owners.read_text(encoding="utf-8")
        if f"{a.id}:" not in text and "projects:" in text:
            block = chr(10).join([
                f"  {a.id}:",
                f"    owner: {a.by}",
                f"    members: [{a.by}]",
                "    status: open",
                "",
            ])
            text = text.replace("projects:" + chr(10), "projects:" + chr(10) + block, 1)
            owners.write_text(text, encoding="utf-8")
            made.append("owners.yaml")

    _out(f"[project-init] projects/{a.id}: " + (", ".join(made) if made else "変更なし"))
    _out("  次に: sources/ に原本を置く → import --scan → 人が draft を open に → ingest --prune")
    return 0


def cmd_import(rest: list[str]) -> int:
    """Excel / Word / PDF を案件の知識庫へ取り込む。

    使い方は 2 つ:

        py -3 -m tools.kb_local import --scan --by <PM>            # sources/ の原本を全部処理
        py -3 -m tools.kb_local import <file> --project <P> --by <PM> --apply

    **抽出した `.md` は `status: draft` で作る**（既定で検索に出ない）。
    人が抽出報告を見て原文と突き合わせ、`open` に変えて初めて検索対象になる——
    「機械が抽出したものを、そのまま事実として検索させない」ための関門。
    """
    import hashlib
    import re
    import shutil
    from datetime import date

    import yaml as _yaml

    from tools.kb_local import extract

    ap = argparse.ArgumentParser(prog="tools.kb_local import",
                                 description="Excel / Word / PDF を知識庫へ取り込む")
    ap.add_argument("file", nargs="?", default=None)
    ap.add_argument("--scan", action="store_true", help="sources/ 配下をまとめて処理")
    ap.add_argument("--project", default=None, help="案件 ID（--scan では省略可＝全案件）")
    ap.add_argument("--by", default="", help="操作者（案件の責任者。紅線③）")
    ap.add_argument("--doc-type", dest="doc_type", default="howto")
    ap.add_argument("--title", default=None)
    ap.add_argument("--conf-level", dest="conf_level", type=int, default=30)
    ap.add_argument("--apply", action="store_true", help="単体指定のとき書き込む")
    ap.add_argument("--dry-run", dest="dry_run", action="store_true",
                    help="--scan のとき書き込まない")
    ap.add_argument("--repo", default=str(DEFAULT_REPO))
    args = ap.parse_args(rest)

    repo = Path(args.repo)

    def _slug(name: str) -> str:
        base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40]
        return base or "doc-" + hashlib.sha1(name.encode("utf-8")).hexdigest()[:8]

    def _build(src: Path, project: str, doc_type: str, title: str | None,
               conf: int) -> tuple[str, str, dict]:
        """(doc_id, ファイル内容, 抽出結果) を返す。抽出失敗は SystemExit。"""
        result = extract.extract(src)
        text = result["text"]
        stem = f"{project[2:].lower() if project.upper().startswith('P-') else project.lower()}-src-{_slug(src.stem)}"
        fm = {
            "id": f"KNOW-{project.upper()}-SRC-{_slug(src.stem).upper()}",
            "type": "knowledge",
            "req_ids": [],
            "sensitivity": "internal",
            "doc_id": stem,
            "scope": "project",
            "project_id": project,
            "title": title or src.stem,
            "doc_type": doc_type,
            "version": "0.1.0",
            # 人が見るまで検索に出さない（draft は既定の可检索状態に無い）
            "status": "draft",
            "conf_level": conf,
            "owner": args.by or "KB担当",
            "updated_at": str(date.today()),
            "source_file": f"sources/{src.name}",
            "extracted_by": f"tools.kb_local import ({result['method']})",
            "extracted_sha": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16],
        }
        body = ("> 本ファイルは `sources/` の原本から機械的に抽出したテキストである"
                "（要約ではない）。**人が原本と突き合わせて `status: open` に変えるまで検索に出ない。**\n\n"
                + text + "\n")
        content = ("---\n" + _yaml.safe_dump(fm, allow_unicode=True, sort_keys=False).rstrip()
                   + "\n---\n\n" + body)
        return stem, content, result

    def _is_generated(path: Path) -> bool:
        """自分たちが作った抽出結果か（`.md` を再投入して自己増殖しないための判定）。"""
        try:
            head = path.read_text(encoding="utf-8", errors="replace")[:800]
        except OSError:
            return False
        return "extracted_by: tools.kb_local import" in head

    def _summary(src: Path, result: dict) -> str:
        stats = result["stats"]
        bits = []
        for key, label in (("sheets", "sheet"), ("paragraphs", "段落"), ("tables", "表"),
                           ("rows", "行"), ("merges", "结合"), ("chars", "字")):
            if key in stats:
                bits.append(f"{label} {stats[key]}")
        return " / ".join(bits)

    # ---------------- --scan ----------------
    if args.scan:
        if not args.by:
            print("[import] --by が必要です（案件の責任者）", file=sys.stderr)
            return 2
        projects_root = repo / "projects"
        targets = ([projects_root / args.project] if args.project
                   else sorted(p for p in projects_root.iterdir() if p.is_dir()))

        from tools.kb_acl import check as acl_check

        total_ok = total_skip = total_fail = 0
        for pdir in targets:
            if not pdir.is_dir():
                continue
            project = pdir.name
            src_dir = pdir / "sources"
            if not src_dir.is_dir():
                continue
            # ★ 自分が生成した `.md` は**入力にしない**（再投入すると自己増殖して壊れる）。
            # ★ `README.*` は「このフォルダの説明」であって資料ではない（実測で誤って抽出された）。
            files = sorted(
                p for p in src_dir.iterdir()
                if p.is_file() and p.suffix.lower() in extract.SUPPORTED
                and not _is_generated(p)
                and not p.stem.lower().startswith("readme")
            )
            if not files:
                continue

            # 権限：その案件の責任者でなければ、その案件は触らない（自分の規則を守る）
            probe = f"tools/kb-platform/repo/projects/{project}/sources/x.md"
            problems = acl_check([probe], args.by, _bootstrap.ROOT)
            if problems:
                _out(f"[{project}] 権限がないため飛ばします: {problems[0]}")
                continue

            _out(f"[{project}] {len(files)} 件")
            for src in files:
                dest = pdir / "extracted" / f"{_slug(src.stem)}.md"
                dest.parent.mkdir(parents=True, exist_ok=True)
                existing = dest.read_text(encoding="utf-8") if dest.is_file() else ""
                try:
                    _stem, content, result = _build(src, project, args.doc_type,
                                                    args.title, args.conf_level)
                except SystemExit as exc:
                    _out(f"  ✗ {src.name} — {str(exc).splitlines()[0]}")
                    total_fail += 1
                    continue

                new_sha = hashlib.sha256(result["text"].encode("utf-8")).hexdigest()[:16]
                if existing and f"extracted_sha: {new_sha}" in existing:
                    _out(f"  = {src.name}（変更なし）")
                    total_skip += 1
                    continue

                status_note = "内容が変わったので draft に戻した" if existing else "新規"
                if not args.dry_run:
                    dest.write_text(content, encoding="utf-8")
                _out(f"  ○ {src.name} → {dest.name}  ({_summary(src, result)})")
                _out(f"       {status_note}／status: draft（人が確認して open にする）")
                for warning in result["warnings"]:
                    _out(f"       ⚠ {warning}")
                total_ok += 1

        _out(f"\n[import] 取り込み {total_ok} 件 / 変更なし {total_skip} 件 / 失敗 {total_fail} 件")
        if total_ok and not args.dry_run:
            _out("  次に: 抽出内容を原本と突き合わせ、`status: draft` を `open` に変える")
            _out("        → `py -3 -m tools.kb_local ingest --prune`")
        return 1 if total_fail else 0

    # ---------------- 単体 ----------------
    if not args.file or not args.project:
        print("[import] <file> と --project が必要です（まとめて処理するなら --scan）",
              file=sys.stderr)
        return 2
    src = Path(args.file)
    if not src.is_file():
        print(f"[import] ファイルがありません: {src}", file=sys.stderr)
        return 2
    project_dir = repo / "projects" / args.project
    if not project_dir.is_dir():
        print(f"[import] 案件ディレクトリがありません: projects/{args.project}", file=sys.stderr)
        return 2

    dest = project_dir / "extracted" / f"{_slug(src.stem)}.md"
    rel_md = (f"tools/kb-platform/repo/projects/{args.project}/extracted/{dest.name}")
    from tools.kb_acl import check as acl_check

    problems = acl_check([rel_md], args.by, _bootstrap.ROOT)
    if problems:
        print("[import] 権限違反:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    try:
        stem, content, result = _build(src, args.project, args.doc_type,
                                       args.title, args.conf_level)
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        return 1

    out = {"project": args.project, "doc_id": stem, "method": result["method"],
           "stats": result["stats"], "warnings": result["warnings"],
           "source": str(project_dir / "sources" / src.name),
           "extracted": str(dest), "written": args.apply}
    _out(json.dumps(out, ensure_ascii=False, indent=2))
    if not args.apply:
        _out("  （dry-run。取り込むには --apply）")
        return 0

    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.resolve() != (project_dir / "sources" / src.name).resolve():
        shutil.copy2(src, project_dir / "sources" / src.name)
    dest.write_text(content, encoding="utf-8")
    _out("  次に: 原本と突き合わせ、`status: draft` を `open` に変えて `ingest --prune`")
    return 0


def cmd_freshness(rest: list[str]) -> int:
    """索引とファイルの食い違いを見る（**知らないうちに古い答えを返す**のを防ぐ）。

    検出する 3 つ:
      - 未索引 … `repo/` に在るが索引に無い（`ingest` を忘れている）
      - 未反映 … 索引に在るがファイルが変わっている（`ingest` を忘れている）
      - 消失   … 索引に在るがファイルが無い（`ingest --prune` を忘れている）

    ★ 本ツールは**索引の鮮度**しか見ない。「内容そのものが古くなっていないか」は
      人が確かめる（設計が変わったのに文書が追いついていない、等）。
    """
    import hashlib

    from kbkit import store

    ap = argparse.ArgumentParser(prog="tools.kb_local freshness",
                                 description="索引とファイルの食い違い")
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--repo", default=str(DEFAULT_REPO))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(rest)

    conn = store.connect(args.db)
    store.init_schema(conn)
    repo = Path(args.repo)

    indexed: dict[str, tuple[str, str]] = {}
    for doc_id, rel, sha in conn.execute("SELECT doc_id, path, sha256 FROM kb_doc"):
        indexed[str(doc_id)] = (str(rel), str(sha or ""))

    # 改行を LF に揃えた指紋（`index_extra` が持つ）。CRLF/LF の入れ替わりを
    # 「内容が変わった」と誤判定しないため、こちらがあれば優先して使う。
    norm_map: dict[str, str] = {}
    try:
        for doc_id, sha_norm in conn.execute("SELECT doc_id, sha_norm FROM kb_doc_extra"):
            if sha_norm:
                norm_map[str(doc_id)] = str(sha_norm)
    except Exception:  # noqa: BLE001  （退避表が無い DB でも動かす）
        pass

    unindexed, outdated, missing = [], [], []
    seen_paths: set[str] = set()

    for doc_id, (rel, sha) in indexed.items():
        seen_paths.add(rel)
        path = repo / rel
        if not path.is_file():
            missing.append((doc_id, rel))
            continue
        raw = path.read_bytes()
        norm = hashlib.sha256(raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")).hexdigest()
        if norm_map.get(doc_id):
            if norm != norm_map[doc_id]:
                outdated.append((doc_id, rel))
        else:
            current = hashlib.sha256(raw).hexdigest()
            if sha and current != sha:
                outdated.append((doc_id, rel))

    for path in sorted(repo.rglob("*.md")):
        try:
            rel = path.relative_to(repo).as_posix()
        except ValueError:
            continue
        if rel not in seen_paths:
            unindexed.append(rel)

    problems = len(unindexed) + len(outdated) + len(missing)
    if args.json:
        import json as _json

        _out(_json.dumps({
            "indexed": len(indexed),
            "unindexed": unindexed,
            "outdated": [i for i, _ in outdated],
            "missing": [i for i, _ in missing],
        }, ensure_ascii=False, indent=2))
        return 1 if problems else 0

    _out(f"[freshness] 索引 {len(indexed)} 件")
    if unindexed:
        _out(f"  ✗ 未索引 {len(unindexed)} 件 — `ingest --prune` を実行してください")
        for rel in unindexed[:10]:
            _out(f"      {rel}")
    if outdated:
        _out(f"  ✗ 未反映 {len(outdated)} 件 — ファイルが変わっています。`ingest --prune` を")
        for doc_id, rel in outdated[:10]:
            _out(f"      {doc_id}  ({rel})")
    if missing:
        _out(f"  ✗ 消失 {len(missing)} 件 — `ingest --prune` で索引から外してください")
        for doc_id, rel in missing[:10]:
            _out(f"      {doc_id}  ({rel})")
    if problems:
        _out(f"\n  合計 {problems} 件。**この状態の検索は古い内容を返します。**")
        return 1
    _out("  OK（索引はファイルと一致しています）")
    _out("  ※ 内容そのものの鮮度（設計が変わって文書が古い、等）は人が確かめる")
    return 0


def cmd_synonyms(rest: list[str]) -> int:
    """用語集から作った中日英の対応表を見る（検索語の拡張に使われる）。"""
    from tools.kb_local import synonyms

    ap = argparse.ArgumentParser(prog="tools.kb_local synonyms",
                                 description="検索語の拡張に使う用語対応")
    ap.add_argument("--self-test", action="store_true", help="合成データで自己検証する")
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--repo", default=str(DEFAULT_REPO))
    args = ap.parse_args(rest)

    if args.self_test:
        return synonyms._self_test()

    from kbkit import store

    conn = store.connect(args.db)
    store.init_schema(conn)
    lexicon = synonyms.build(conn, Path(args.repo))
    _out(f"[synonyms] {len(lexicon)} 語（中文・English → 日本語）")
    for alias in sorted(lexicon):
        _out(f"  {alias} → {', '.join(sorted(lexicon[alias]))}")
    return 0


def cmd_whoami(rest: list[str]) -> int:
    """この端末の「操作者名」を表示・設定する。

    読権限は `--as <人>` で明示する建前だが、毎回聞くのは現実的でない。
    **端末ごとに 1 回だけ設定**しておき、会話ではそれを参照する。
    実値は gitignore 済（`tools/kb_local/whoami.txt`）。
    """
    ap = argparse.ArgumentParser(prog="tools.kb_local whoami",
                                 description="端末の操作者名（読権限の既定）")
    ap.add_argument("--set", dest="set_user", default=None, help="操作者名を保存する")
    args = ap.parse_args(rest)

    from tools.kb_local import whoami

    if args.set_user:
        name = args.set_user.strip()
        if not name:
            print("[whoami] 空の名前は設定できません", file=sys.stderr)
            return 2
        saved = whoami.set_(_bootstrap.ROOT, name)
        _out(f"[whoami] {name} として保存しました（{saved.relative_to(_bootstrap.ROOT).as_posix()}）")
        _out("        以後、`--as` を省いた検索でもこの名前が使われます。")
        return 0

    name = whoami.get(_bootstrap.ROOT)
    if name:
        _out(name)
        return 0
    _out("（未設定）— `py -3 -m tools.kb_local whoami --set <名前>` で設定します")
    return 0


def cmd_external_check(rest: list[str]) -> int:
    """対外文書に `client_only`（L40）の内容が混ざっていないかを見る。

    検索の絞り込みは「人がコピーして貼る」経路を止められない。
    このコマンドは、対外に出そうなファイルと L40 文書の**長い一致**を並べる。
    """
    from kbkit import store
    from tools.kb_local import confidential

    ap = argparse.ArgumentParser(prog="tools.kb_local external-check",
                                 description="対外文書への L40 混入検査")
    ap.add_argument("file", nargs="+", help="対外に出そうなファイル")
    ap.add_argument("--min-len", type=int, default=confidential.DEFAULT_MIN_LEN,
                    help=f"一致とみなす連続文字数（既定 {confidential.DEFAULT_MIN_LEN}）")
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--repo", default=str(DEFAULT_REPO))
    args = ap.parse_args(rest)

    conn = store.connect(args.db)
    store.init_schema(conn)
    sources = confidential.load_confidential(conn, Path(args.repo))
    if not sources:
        _out("[external-check] L40（client_only）の文書がありません。検査対象 0 件。")
        return 0

    bad = 0
    for name in args.file:
        path = Path(name)
        if not path.is_file():
            print(f"[external-check] ファイルがありません: {name}", file=sys.stderr)
            return 2
        hits = confidential.find_copies(path.read_text(encoding="utf-8"), sources, args.min_len)
        if hits:
            bad += 1
            _out(f"[NG] {name}: L40 の内容と一致 {len(hits)} 件")
            for hit in hits[:5]:
                _out(f"   - {hit['source']}: {hit['count']} 断片 / 例「{hit['sample']}」")
        else:
            _out(f"[OK] {name}")
    _out(f"[external-check] L40 文書 {len(sources)} 件と照合。NG {bad} 件 / 検査 {len(args.file)} 件。")
    return 1 if bad else 0


def cmd_eval(rest: list[str]) -> int:
    from kbkit import eval as kbeval
    from kbkit import store
    from kbkit.embedder import get_embedder

    ap = argparse.ArgumentParser(prog="tools.kb_local eval", description="ゴールデンセット評価")
    ap.add_argument("--golden", default=str(DEFAULT_GOLDEN))
    ap.add_argument("--project", default=None)
    ap.add_argument("--level", type=int, default=30)
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--as", dest="as_user", default=None,
                    help="利用者名（読権限。所属案件の知識だけが見える）")
    ap.add_argument("--all", dest="all", action="store_true",
                    help="読権限を外す（管理者。測定・保守用）")
    ap.add_argument("--exclude-derived", dest="exclude_derived", action="store_true",
                    help="検索摘要（chunks/）を候補から外す（既定は含める）")
    ap.add_argument("--threshold", type=float, default=0.85)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--repo", default=str(DEFAULT_REPO))
    ap.add_argument("--embedder", default="hash", choices=["hash", "bge"])
    args = ap.parse_args(rest)

    allowed, user, source = _resolve_allowed(args.as_user, args.all)
    if not args.all and not user:
        print("[kb_local] eval のゴールデンセットは案件級の設問を含みます。", file=sys.stderr)
        print("            身元を設定する（whoami --set <名前>）か、--as <人> / --all を指定してください。",
              file=sys.stderr)
        return 2

    _out(f"[kb_local] 読取範囲: {_describe_scope(user, source, args.all, allowed)}")

    embedder = get_embedder(args.embedder)
    conn = store.connect(args.db)
    store.init_schema(conn)
    cases = kbeval.load_golden(args.golden)   # 金標の読み方は上流のまま
    report = evaluate(
        conn, embedder, cases,
        project_id=args.project, user_level=args.level, top_k=args.top_k,
        allowed_projects=allowed,
        exclude_derived=args.exclude_derived,
    )
    if args.json:
        _out(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _out(format_report(report))
    ok = report["recall"] >= args.threshold
    _out(f"\nしきい値 recall@{args.top_k} >= {args.threshold}: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        _out(__doc__ or "")
        return 0

    cmd, rest = argv[0], argv[1:]
    if cmd in DELEGATED:
        return _upstream_main(argv)
    if cmd == "lint":
        return cmd_lint(rest)
    if cmd == "ingest":
        return cmd_ingest(rest)
    if cmd == "extra":
        return cmd_extra(rest)
    if cmd == "search":
        return cmd_search(rest)
    if cmd == "eval":
        return cmd_eval(rest)
    if cmd == "external-check":
        return cmd_external_check(rest)
    if cmd == "whoami":
        return cmd_whoami(rest)
    if cmd == "synonyms":
        return cmd_synonyms(rest)
    if cmd == "freshness":
        return cmd_freshness(rest)
    if cmd == "check-constraints":
        return cmd_check_constraints(rest)
    if cmd == "node-brief":
        return cmd_node_brief(rest)
    if cmd == "check-knowledge":
        return cmd_check_knowledge(rest)
    if cmd == "project-init":
        return cmd_project_init(rest)
    if cmd == "import":
        return cmd_import(rest)

    _out(f"未知のコマンド: {cmd}\n")
    _out(__doc__ or "")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

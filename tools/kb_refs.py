"""各工程節点の産出が「知識ベースの先例」を引いているか、引いた先例が実在するかを見る。

なぜ要るか
----------
知識ベースは「調べられる」だけでは使われない。節点の産出物が
`kb_refs:` に引いた先例を持ち、それが実在することで初めて追跡できる。

**何を `kb_refs` に書くか（2 種類ある。意味が違う）**
  - **先例** … 案件の事実（`r60-001-screens-r60login`）、テンプレート（`TPL-*`）、パターン（`PAT-*`）。
    照らし合わせる対象であり、**これが無いと「何を根拠にしたか」が辿れない**。
  - **規約** … `STD-*`（`company/standards/`）。遵守する対象であり、
    引用の値は「**どの規約に従ったか**の記録」である（新情報ではない）。
  どちらも記録してよい。**検査は 2 種を区別して並べる**（合否には使わない）。

**判定しないこと**
  「その先例に沿っているか」は見ない。見るのは「引いたか」「実在するか」「節点に必要な範囲を
  引いたか」までである。中身の妥当性は人が読む（紅線③）。

使い方
------
    py -3 -m tools.kb_refs show --node 3
    py -3 -m tools.kb_refs suggest --project P-R60-001 --as Li --query "排他制御"
    py -3 -m tools.kb_refs check <承認版.md> --node 3 [--strict]
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "tools" / "kb-platform" / "data" / "kb.sqlite3"
KB_REPO = ROOT / "tools" / "kb-platform" / "repo"
EXEMPT_FILE = ROOT / "tools" / "kb-platform" / "kb_refs_exempt.txt"


def _out(text: str = "") -> None:
    print(text)


#: 節点ごとの「引くべき範囲」。**いずれか 1 件でも当たれば合格**（全部ではない）。
#: 値は `kb_doc.path` の部分一致で照合する。
NODE_CATEGORIES: dict[int, tuple[str, ...]] = {
    1: ("company/patterns/review", "/glossary"),           # 審査観点・案件用語
    2: ("company/patterns/screen", "/screens", "company/templates", "company/standards"),
    3: ("/modules", "/standards", "company/templates"),
    4: ("company/standards/coding", "company/templates"),  # 技術規約・テンプレート
    5: ("/standards", "company/standards/coding"),         # 共通部品・コーディング規約
    6: ("company/standards/testing", "/review"),           # テスト観点・過去の指摘
    7: ("/modules", "/screens", "company/patterns/dev"),   # 契約・画面の実態＋実走例（必読条目を満たすため 2026-11-09 追加）
    8: ("company/patterns/delivery", "/glossary"),         # 交付方式・用語
}

#: 節点ごとの「必読条目」。`check --require-node` で、この doc_id が kb_refs に
#: 記録されているかを機械的に検査する。**作業票（nodes/nNN-*.md §1.5）の表と一致させること。**
#: 値の追加・変更は人の承認が要る（ここを緩めると「必読」が形骸化する）。
NODE_MAP_FILE = ROOT / "tools" / "kb-platform" / "node-map.yaml"


def _load_node_required() -> dict[int, tuple[str, ...]]:
    """`tools/kb-platform/node-map.yaml`（唯一真源）から節点の必読条目を読む。"""
    try:
        data = yaml.safe_load(NODE_MAP_FILE.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    out: dict[int, tuple[str, ...]] = {}
    for key, value in (data.get("nodes") or {}).items():
        req = (value or {}).get("required") or []
        if req:
            out[int(key)] = tuple(str(x) for x in req)
    return out


NODE_REQUIRED = _load_node_required()

NODE_NAMES = {
    1: "要件理解", 2: "基本設計", 3: "詳細設計", 4: "框架構築",
    5: "製造", 6: "単体テスト", 7: "結合・総合テスト", 8: "リリース・運用",
}


def _front_matter(path: Path) -> dict:
    """front matter を辞書で返す。

    **`.md` と `.yaml` で読み方が違う**（`.claude/rules/02-requirements.md` §5.1）:
      - `.md`  … 先頭の `---` と本文直前の `---` で挟む
      - `.yaml` … 文書全体が front matter（`---` は先頭の 1 本だけ）
    取り違えると実戦の YAML が読めず、「kb_refs が無い」と誤判定する。
    """
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml"):
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError:
            return {}
        return data if isinstance(data, dict) else {}
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    try:
        data = yaml.safe_load(text[3:end])
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


#: 節を指すときの区切り。`doc_id#4.2` のように書く（`kb-policy.md` §7.2）。
REF_SEP = "#"


def split_ref(ref: str) -> tuple[str, str | None]:
    """`doc_id#節` を `(doc_id, 節)` に分ける。節が無ければ `None`。"""
    text = str(ref).strip()
    if REF_SEP in text:
        doc_id, section = text.split(REF_SEP, 1)
        return doc_id.strip(), (section.strip() or None)
    return text, None


def load_docs(db: Path) -> dict[str, dict]:
    conn = sqlite3.connect(db)
    try:
        rows = conn.execute(
            "SELECT doc_id, path, scope, doc_type, title FROM kb_doc"
        ).fetchall()
    except sqlite3.OperationalError:
        return {}
    docs = {
        str(doc_id): {"path": str(path or ""), "scope": str(scope or ""),
                      "doc_type": str(doc_type or ""), "title": str(title or ""),
                      "canonical": False, "headings": set()}
        for doc_id, path, scope, doc_type, title in rows
    }
    # `canonical: true`（＝要約ではなく正本）を front matter から拾う。
    # これを読まないと、方法の正本まで「規則の摘要」と誤判定する（2026-11-06 是正）。
    for info in docs.values():
        if not str(info.get("path")):
            continue
        p = KB_REPO / str(info["path"])
        try:
            head = p.read_text(encoding="utf-8")[:600]
        except OSError:
            continue
        if "canonical: true" in head:
            info["canonical"] = True
    try:
        for doc_id, heading in conn.execute("SELECT doc_id, heading FROM kb_chunk"):
            entry = docs.get(str(doc_id))
            if entry is not None and heading:
                entry["headings"].add(str(heading))
    except sqlite3.OperationalError:
        pass
    finally:
        conn.close()
    return docs



def _node_doc_ids(node: int) -> set[str] | None:
    """作業票 §1.5 の「★本节点必读」表に書かれた doc_id を集める（NFR-1 の突合）。

    ファイルが無い／表が無い場合は None（突合しない）。
    """
    nodes = ROOT / ".claude" / "skills" / "trans-cosmos-ai-lifecycle-coach" / "nodes"
    cands = sorted(nodes.glob(f"n0{node}-*.md")) if nodes.is_dir() else []
    if not cands:
        return None
    text = cands[0].read_text(encoding="utf-8")
    i = text.find("★本节点必读")
    if i < 0:
        return None
    found: set[str] = set()
    for line in text[i:].splitlines()[1:]:
        if line.strip() == "":
            break
        for tok in re.findall(r"`([^`]+)`", line):
            if re.fullmatch(r"[A-Z][A-Z0-9-]*-\d{3}", tok):
                found.add(tok)
    return found or None


USAGE_HEADING_RE = re.compile(r"^##\s+(?:知識ベースの使用記録|知识库使用记录)\s*$", re.M)


def _n(s: str) -> str:
    """`§2 シート構成` / `2. シート構成（…）` を同じ形に落とす。"""
    s = re.sub(r"^§\s*", "", str(s)).strip()
    s = re.sub(r"^[0-9０-９]+(?:\.[0-9０-９]+)*\.?\s*", "", s)
    s = re.sub(r"[（(][^）)]*[）)]\s*$", "", s)
    return s.strip()


def _usage_rows(text: str) -> list[list[str]] | None:
    m = USAGE_HEADING_RE.search(text)
    if not m:
        return None
    seg = text[m.end():]
    nxt = re.search(r"^##\s+", seg, re.M)
    if nxt:
        seg = seg[:nxt.start()]
    rows: list[list[str]] = []
    for line in seg.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        if cells[0].startswith("doc_id") or set(cells[0]) <= set("-: "):
            continue
        rows.append(cells)
    return rows


def _check_usage(path: Path, node: int, docs: dict[str, dict]) -> list[str]:
    """`kb_usage`（使用記録）を検査する。返り値は problems。"""
    problems: list[str] = []
    text = path.read_text(encoding="utf-8")
    rows = _usage_rows(text)
    if rows is None:
        return ["`## 知識ベースの使用記録`（使用記録）の節がない"]
    by_id = {r[0].strip("`* "): r for r in rows}
    for did in NODE_REQUIRED.get(node, ()):
        if did not in by_id:
            problems.append(f"使用記録に {did} の行がない")
            continue
        info = docs.get(did)
        if not info:
            continue
        try:
            src = (KB_REPO / info["path"]).read_text(encoding="utf-8")
        except OSError:
            continue
        heads = {_n(h) for h in re.findall(r"^#{2,3}\s+(.+)$", src, re.M)}
        want = _n(by_id[did][1])
        if want and not any((want in h) or (h in want) for h in heads):
            problems.append(f"{did} の「参照した節」が原文に見つからない: {want}")
        # 反映先（本稿のどの節に効いたか）が実在するか
        refs = re.findall(r"§\s*(\d+(?:\.\d+)*)", " ".join(by_id[did][2:]))
        if refs:
            self_nums = {m.split(".")[0] for m in re.findall(r"^#{2,4}\s+(\d+(?:\.\d+)*)", text, re.M)}
            bad = [r for r in refs if r.split(".")[0] not in self_nums]
            if bad:
                problems.append(f"{did} の「反映先」が本稿に無い: §{', §'.join(bad)}")
    return problems


def _is_rule_summary(doc_id: str, info: dict) -> bool:
    """規則の摘要かどうか。`STD-*` のうち `company/standards/` に置かれたもの。

    テンプレート（`TPL-*`）とパターン（`PAT-*`）は先例として扱う。
    **`canonical: true` の条目は要約ではなく正本なので、摘要扱いしない**
    （作業票の「STD-* は書かない」の例外。`kb-policy.md` §2.4）。
    """
    if not (doc_id.upper().startswith("STD-") and "company/standards" in info["path"]):
        return False
    return not bool(info.get("canonical"))


def check(path: Path, node: int | None, docs: dict[str, dict], strict: bool = False,
          require_node: bool = False, require_usage: bool = False) -> dict:
    meta = _front_matter(path)
    refs = meta.get("kb_refs")
    problems: list[str] = []
    warnings: list[str] = []

    if refs is None:
        problems.append("front matter に `kb_refs` がありません（引いた先例を記録してください）")
        refs = []
    elif isinstance(refs, str):
        refs = [refs]
    elif not isinstance(refs, list):
        problems.append("`kb_refs` は配列で書いてください")
        refs = []

    refs = [str(r) for r in refs]
    missing = [r for r in refs if r not in docs]
    if missing:
        problems.append(f"実在しない先例: {', '.join(missing)}")

    # 参照を 2 種に分ける（どちらも記録してよい。意味が違う）。
    #   先例 … 案件の事実・テンプレート・パターン（照らし合わせる対象）
    #   規約 … `STD-*`（遵守する対象。引用の値は「遵守の記録」）
    standards = [r for r in refs if r in docs and _is_rule_summary(r, docs[r])]
    precedents = [r for r in refs if r in docs and r not in standards]

    # `--strict` は「先例だけで通す」追加の厳格モード。
    # 2026-11-06 是正：以前は引数を受けるだけで一度も判定に使われていなかった（help と実装が不一致）。
    if strict and standards:
        problems.append(
            "規則の摘要は --strict では不合格（先例を引くこと）: " + ", ".join(standards)
        )

    if require_usage and node is not None:
        problems.extend(_check_usage(path, node, docs))

    if require_node and node in NODE_REQUIRED:
        need = [d for d in NODE_REQUIRED[node] if d not in refs]
        if need:
            problems.append("節点 {0} の必読条目が kb_refs にありません: {1}".format(node, ", ".join(need)))
        # NFR-1: 作業票の表と NODE_REQUIRED が一致しているか
        table = _node_doc_ids(node)
        if table is not None and table != set(NODE_REQUIRED[node]):
            problems.append(
                "節点 {0} の必読表が NODE_REQUIRED と一致しません（作業票={1} / ツール={2}）".format(
                    node, ",".join(sorted(table)), ",".join(sorted(NODE_REQUIRED[node]))))

    if node in NODE_CATEGORIES:
        keys = NODE_CATEGORIES[node]
        covered = any(any(k in docs[r]["path"] for k in keys) for r in refs if r in docs)
        if not covered and refs:
            problems.append(
                f"節点 {node}（{NODE_NAMES[node]}）で引くべき範囲が抜けています: "
                + " / ".join(keys)
            )

    return {"file": str(path), "node": node, "refs": refs, "missing": missing,
            "precedents": precedents, "standards": standards,
            "problems": problems, "warnings": warnings, "ok": not problems}


def suggest(query: str, project: str | None, as_user: str | None,
            top_k: int, db: Path) -> list[dict]:
    """検索して「引用候補」を出す。実行体はこれをそのまま `kb_refs` に写す。

    読権限の既定は `kb_local search` と同じ（**会社級のみ**）。案件級を引くには `--as`。
    """
    sys.path.insert(0, str(ROOT))
    # `_bootstrap` を先に読む——これが vendor（`tools/kb-platform`）を sys.path に足す。
    from tools.kb_local import _bootstrap  # noqa: E402,F401
    from kbkit import store  # noqa: E402
    from kbkit.embedder import get_embedder  # noqa: E402
    from tools.kb_local.retrieval import search  # noqa: E402

    # `--as` が無ければ端末に設定した名前（`whoami`）を使う。**どちらも無ければ会社級だけ。**
    user = as_user
    if not user:
        from tools.kb_local import whoami

        user = whoami.get(ROOT)
    if user:
        from tools.kb_acl import allowed_projects

        allowed: set[str] | None = allowed_projects(user, ROOT)
    else:
        allowed = set()

    conn = store.connect(db)
    store.init_schema(conn)
    try:
        results = search(conn, query, get_embedder("hash"), project_id=project,
                         user_level=30, top_k=top_k, allowed_projects=allowed)
    finally:
        conn.close()
    return [
        {"doc_id": r["doc_id"], "title": r.get("title"), "scope": r.get("scope"),
         "section": r.get("heading"), "score": round(float(r.get("score", 0)), 4)}
        for r in results
    ]


def load_exempt(root: Path, exempt_file: Path | None = None) -> set[str]:
    """遡及適用しない文書の一覧（リポジトリ相対・`/` 区切り）。

    **静かに飛ばすための仕組みではない。** 例外は 1 行 1 理由つきでここに書き、
    レビューで外せる形にする。空行と `#` 行は無視する。
    """
    path = exempt_file or (root / EXEMPT_FILE.relative_to(ROOT) if root != ROOT else EXEMPT_FILE)
    if not path.is_file():
        return set()
    out: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip().replace("\\", "/")
        if not text or text.startswith("#"):
            continue
        out.add(text)
    return out


#: 実戦の成果物が置かれる `docs/<NN>_<工程>/` → 節点番号。
#: 節点5（製造）は `docs/` に成果物を置かない（コードそのものが成果物）ため、ここには無い。
NODE_BY_DOCS_DIR = {
    "10_": 1, "20_": 2, "30_": 3, "40_": 4,
    "50_": 6, "60_": 7, "70_": 8,
}


def _tutorial_outputs(root: Path) -> list[tuple[Path, int | None]]:
    """演習の承認版（`05_承認版_*`）。節点名（`节点N_`）から節点番号を推測する。"""
    out: list[tuple[Path, int | None]] = []
    for path in sorted(root.rglob("05_承認版_*.md")):
        node = None
        for part in path.parts:
            if part.startswith("节点") and len(part) > 2 and part[2].isdigit():
                node = int(part[2])
                break
        out.append((path, node))
    return out


def _real_outputs(root: Path) -> list[tuple[Path, int | None]]:
    """実戦の成果物（`docs/10_requirements/` … `docs/70_release/`）。

    **雛形は除く**——雛形は成果物ではない（まだ中身が無い）。判定は 2 通り:
      - ファイル名に `template` を含む（`req-template.yaml` など）
      - front matter の `id` が `TPL-` で始まる（`framework-record.yaml` は
        ファイル名に template を持たないが `id: TPL-004` の雛形である）
    """
    docs_dir = root / "docs"
    if not docs_dir.is_dir():
        return []
    out: list[tuple[Path, int | None]] = []
    for child in sorted(docs_dir.iterdir()):
        if not child.is_dir() or child.name.startswith(("_", "00_", "90_")):
            continue
        node = next((n for prefix, n in NODE_BY_DOCS_DIR.items()
                     if child.name.startswith(prefix)), None)
        if node is None:
            continue
        for path in sorted(child.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in (".yaml", ".yml", ".md"):
                continue
            if "template" in path.name.lower():
                continue
            meta = _front_matter(path)
            if str(meta.get("id") or "").upper().startswith("TPL-"):
                continue
            out.append((path, node))
    return out


def cited_index(root: Path) -> dict[str, list[str]]:
    """逆引き索引：`doc_id → [それを引用した成果物]`。

    `scan` と同じ対象（演習の承認版＋実戦の成果物）を読み、`kb_refs` を集める。
    **これがあると「この条目は誰かに使われているか」を数で答えられる**——
    昇格の判断（`kb-policy.md` §5「2 案件目で使われたもの」）の材料になる。
    """
    index: dict[str, list[str]] = {}
    for path, _node in (_tutorial_outputs(root) + _real_outputs(root)):
        meta = _front_matter(path)
        refs = meta.get("kb_refs")
        if isinstance(refs, str):
            refs = [refs]
        if not isinstance(refs, list):
            continue
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            rel = path.as_posix()
        for ref in refs:
            index.setdefault(str(ref), []).append(rel)
    return index


def scan(root: Path, docs: dict[str, dict], strict: bool = False,
         exempt_file: Path | None = None) -> dict:
    """演習と実戦の成果物を一括検査する。

    - 演習 … `**/05_承認版_*.md`（節点名から節点番号）
    - 実戦 … `docs/<NN>_<工程>/` 配下の `.yaml` / `.md`（ディレクトリ名から節点番号）

    `kb_refs_exempt.txt` に載っている文書は「適用外」として数える（不合格にしない）。
    **例外は明示的なリストにだけ許す**——静かに飛ばす仕組みは作らない。
    """
    exempt = load_exempt(root, exempt_file)
    targets = _tutorial_outputs(root) + _real_outputs(root)
    results = []
    for path, node in targets:
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            rel = path.as_posix()
        result = check(path, node, docs, strict)
        result["exempt"] = rel in exempt
        results.append(result)
    failed = [r for r in results if not r["ok"] and not r["exempt"]]
    skipped = [r for r in results if r["exempt"]]
    return {"checked": len(results), "failed": len(failed),
            "exempt": len(skipped), "results": results}


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    ap = argparse.ArgumentParser(prog="tools.kb_refs", description="節点産出の先例参照を検査する")
    ap.add_argument("--db", default=str(DEFAULT_DB))
    sub = ap.add_subparsers(dest="cmd", required=True)

    show = sub.add_parser("show", help="節点ごとの「引くべき範囲」を表示")
    show.add_argument("--node", type=int, default=None)

    sg = sub.add_parser("suggest", help="引用候補を検索して出す")
    sg.add_argument("--query", required=True)
    sg.add_argument("--project", default=None)
    sg.add_argument("--as", dest="as_user", default=None)
    sg.add_argument("--top-k", type=int, default=5)
    sg.add_argument("--json", action="store_true")

    ck = sub.add_parser("check", help="承認版の kb_refs を検査")
    ck.add_argument("file")
    ck.add_argument("--node", type=int, default=None)
    ck.add_argument("--strict", action="store_true", help="規則の摘要の引用も不合格にする")
    ck.add_argument("--require-node", action="store_true", help="節点の必読条目（NODE_REQUIRED）を検査する")
    ck.add_argument("--require-usage", action="store_true", help="使用記録（kb_usage）を検査する")

    sc = sub.add_parser("scan", help="承認版（05_承認版_*）を一括検査")
    sc.add_argument("--root", default=str(ROOT))
    sc.add_argument("--strict", action="store_true")

    ct = sub.add_parser("cited", help="逆引き：この知識は誰に引用されているか")
    ct.add_argument("doc_id", nargs="?", default=None, help="省略時は全件を引用回数順")
    ct.add_argument("--zero", action="store_true", help="一度も引用されていないものだけ")
    ct.add_argument("--root", default=str(ROOT))
    ct.add_argument("--json", action="store_true")

    args = ap.parse_args(argv)

    if args.cmd == "show":
        nodes = [args.node] if args.node else sorted(NODE_CATEGORIES)
        for node in nodes:
            if node not in NODE_CATEGORIES:
                print(f"[kb_refs] 節点 {node} は未定義です", file=sys.stderr)
                return 2
            print(f"節点 {node}（{NODE_NAMES[node]}）で引く範囲:")
            for key in NODE_CATEGORIES[node]:
                print(f"  - {key}")
        print("\n※ いずれか 1 件でも当たれば合格。`STD-*`（company/standards）のうち "
              "`canonical: true` でないものは規則の摘要、`canonical: true` は方法の正本（先例扱い）。")
        return 0

    if args.cmd == "suggest":
        rows = suggest(args.query, args.project, args.as_user, args.top_k, Path(args.db))
        if args.json:
            print(json.dumps(rows, ensure_ascii=False, indent=2))
            return 0
        if not rows:
            print("候補なし（--as を付けたか、話題が庫に無いかを確認）")
            return 0
        for i, row in enumerate(rows, 1):
            print(f"{i}. [{row['score']}] {row['doc_id']}  {row['title']}")
            if row.get("section"):
                print(f"   § {row['section']}")
        print("\n※ これを `kb_refs:` に写す。**規則の摘要（STD-*）ではなく先例を選ぶ。**")
        return 0

    if args.cmd == "cited":
        docs = load_docs(Path(args.db))
        root = Path(args.root)
        index = cited_index(root)

        if args.doc_id:
            users = index.get(args.doc_id, [])
            if args.json:
                _out(json.dumps({"doc_id": args.doc_id, "cited_by": users},
                                ensure_ascii=False, indent=2))
                return 0
            known = args.doc_id in docs
            _out(f"[cited] {args.doc_id}"
                 + ("" if known else "  ⚠ この doc_id は索引に無い"))
            if not users:
                _out("  引用している成果物: なし")
            else:
                _out(f"  引用している成果物 {len(users)} 件:")
                for rel in users:
                    _out(f"    - {rel}")
            return 0

        rows = []
        for doc_id, info in docs.items():
            users = index.get(doc_id, [])
            rows.append({"doc_id": doc_id, "count": len(users), "users": users,
                         "title": info.get("title", ""), "scope": info.get("scope", "")})
        if args.zero:
            rows = [r for r in rows if r["count"] == 0]
        rows.sort(key=lambda r: (-r["count"], r["doc_id"]))

        unknown = sorted(set(index) - set(docs))
        if args.json:
            _out(json.dumps({"rows": rows, "unknown_refs": unknown},
                            ensure_ascii=False, indent=2))
            return 0

        _out(f"[cited] 知識 {len(docs)} 件を引用回数順に"
             + ("（未引用のみ）" if args.zero else ""))
        _out("")
        for r in rows:
            _out(f"  {r['count']:>2} 回  [{r['scope']:<7}] {r['doc_id']}  {r['title'][:40]}")
        if unknown:
            _out("")
            _out(f"  ⚠ 索引に無い doc_id を参照している: {', '.join(unknown)}")
        if not any(r["count"] for r in rows) and not args.zero:
            _out("")
            _out("  ※ まだ 1 件も引用されていない（kb_refs を書いた成果物が無い）。")
        return 0

    if args.cmd == "scan":
        docs = load_docs(Path(args.db))
        root = Path(args.root)
        report = scan(root, docs, args.strict)
        for result in report["results"]:
            if result["exempt"]:
                print(f"SKIP {result['file']}  （適用外: kb_refs_exempt.txt）")
                continue
            mark = "OK  " if result["ok"] else "NG  "
            print(f"{mark} {result['file']}")
            if not result["ok"]:
                for problem in result["problems"]:
                    print(f"       ✗ {problem}")
            print(f"       先例: {', '.join(result['precedents']) or '（なし）'}")
            print(f"       規約: {', '.join(result['standards']) or '（なし）'}")
        print(f"\n[kb_refs] 承認版 {report['checked']} 件 / 不合格 {report['failed']} 件"
              f"（適用外 {report['exempt']} 件）")
        return 1 if report["failed"] else 0

    path = Path(args.file)
    if not path.is_file():
        print(f"[kb_refs] ファイルがありません: {path}", file=sys.stderr)
        return 2
    report = check(path, args.node, load_docs(Path(args.db)), args.strict, args.require_node, args.require_usage)
    print(f"[kb_refs] {report['file']}")
    print(f"  先例: {', '.join(report['precedents']) or '（なし）'}")
    print(f"  規約: {', '.join(report['standards']) or '（なし）'}")
    for warning in report["warnings"]:
        print(f"  ⚠ {warning}")
    for problem in report["problems"]:
        print(f"  ✗ {problem}")
    print(f"  判定: {'OK' if report['ok'] else '要修正'}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

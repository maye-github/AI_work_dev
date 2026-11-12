"""案件知識を会社級へ「昇格」させる道具（知識ベース構築ガイド §1.3・§9.3・STEP 12）。

なぜ要るか
----------
ガイドは昇格を 5 手順で書いている（匿名化 → 抽象化 → owner 審批 → git mv → read-only）。
このうち **機械でできるのは「検査」と「移送」だけ**である。
「これは通用するか」「抽象化の度合いは足りているか」は人の判断であり、ここでは扱わない。

使い方
------
    py -3 -m tools.kb_promote candidates --project <P-ID>       # 昇格しうる条目を列挙
    py -3 -m tools.kb_promote review --project <P-ID> --as <人>  # レビュー表（建議つき・勾选欄）
    py -3 -m tools.kb_promote review --project <P-ID> --as <人> --plan-out p.yaml  # 勾选→計画
    py -3 -m tools.kb_promote check <file>                      # 匿名化体检（読み取りのみ）
    py -3 -m tools.kb_promote plan  <file> --to ...             # 何が変わるかを見る
    py -3 -m tools.kb_promote apply <file> --to ... --apply     # 1 件を移送
    py -3 -m tools.kb_promote apply --from-plan <plan.yaml> --apply   # 一括移送
    py -3 -m tools.kb_promote close --project <P-ID> --apply    # 結案記録（CLOSED.md）

`apply` は既定で dry-run。`--apply` を付けたときだけファイルを動かす
（`tools.registry` と同じ流儀）。移送の記録は `promotions.yaml` に残し、
「どの案件の何がどこへ行ったか」を後から引けるようにする。

検査の中身
----------
1. 機密パターン … `tools.trace_check.scan_text` を**そのまま呼ぶ**（規則を二重実装しない）
2. 案件固有の識別子 … 案件 ID・接頭辞付きの物理名・`file:line` 参照
3. front matter の残留 … `project_id`・案件接頭辞付き `doc_id`
4. 顧客名 … `tools/kb_local/promote_denylist.json` があればそれを使う（無ければこの項は飛ばす）

★ **判定はしない。** ヒットを並べるだけである。「これは匿名化済みか」を決めるのは人。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "tools" / "kb-platform" / "repo"
LEDGER = ROOT / "tools" / "kb-platform" / "promotions.yaml"
DENYLIST = ROOT / "tools" / "kb_local" / "promote_denylist.json"

#: 案件固有の識別子。ここに当たったら「そのままでは会社級に出せない」候補である。
#: (ラベル, 正規表現, レベル)。`block` は会社級に出せない／`warn` は人が見て判断する。
#: テンプレートは例として `E-001` のような番号を載せるのが正しい姿なので、
#: 番号参照は warn に落とす（人が「例か実在か」を見分ける）。
IDENTIFIER_PATTERNS: list[tuple[str, re.Pattern, str]] = [
    ("案件ID", re.compile(r"\bP-[A-Z0-9]+-\d{3}\b"), "block"),
    ("案件接頭辞つき識別子", re.compile(r"\b[A-Z]{1,3}\d{2,3}[A-Z][A-Za-z0-9]*\b"), "block"),
    ("案件内の番号", re.compile(r"\b(?:R|F|I|D|L|E|TC|IT)-\d{2,4}\b"), "warn"),
    ("ファイル:行 参照", re.compile(r"[\w./-]+\.(?:py|ts|vue|java|xlsx|yaml)\s*:\s*\d+"), "block"),
    ("行番号参照", re.compile(r"\bL\d{1,4}-\d{1,4}\b"), "warn"),
]

#: 大文字の識別子（物理名らしきもの）。ただし **数字を含むものだけ** を案件固有とみなす。
#: `DEL_FLG` のような一般名や、`COL_1` のような占位（＝匿名化済みの形）は拾わない。
_IDENT_RE = re.compile(r"\b[A-Z][A-Z0-9]{1,}(?:_[A-Z0-9]+){1,}\b")

#: 占位の接頭辞（`01-security-redlines.md` の脱敏占位規則）。これらは会社級に出してよい形である。
GENERIC_PREFIXES = (
    "COL", "TBL", "PWD", "IP", "VAL", "EMP", "NAME", "MSG",
    "KEY", "DOM", "BUCKET", "PROFILE", "SID", "MAIL", "TRG", "SCR", "TXT",
    # ★ `PORT_1` は規則 01 の占位（`TBL_1/COL_1@PWD_1:PORT_1/SID_1`）。
    #   抜けていると「占位を残しただけの文書」が案件固有語として誤検知される（2026-11-10 追加）。
    "PORT",
)

#: 会社級条目が持つべき front matter の最小集合（構築ガイド §4.2）。
FM_MIN_KEYS = ("doc_id", "scope", "title", "doc_type", "version", "status", "conf_level", "updated_at")


def _out(text: str = "") -> None:
    print(text)


def _case_specific(token: str) -> bool:
    """案件固有の物理名らしいか。占位接頭辞は除外し、数字を含むものだけを拾う。"""
    if any(token.startswith(prefix + "_") for prefix in GENERIC_PREFIXES):
        return False
    return any(ch.isdigit() for ch in token)


def _rel(path: Path, root: Path) -> str:
    """リポジトリからの相対パス。区切りは `/` に揃える（Windows でも同じ記録になる）。"""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def split_front_matter(text: str) -> tuple[dict | None, str]:
    """`---` で挟まれた front matter と本文へ分ける。無ければ (None, text)。"""
    if not text.startswith("---"):
        return None, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, text
    try:
        meta = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None, text
    return (meta if isinstance(meta, dict) else None), parts[2]


DENYLIST_TXT = ROOT / "tools" / "kb_local" / "promote_denylist.txt"
MAP_TXT = ROOT / "tools" / "kb_local" / "promote_map.txt"


def load_map(root: Path) -> list[tuple[str, str]]:
    """匿名化の置換表（`元 => 先`）を読む。**長い語から先に当てる**。

    表に無い語は置き換えない。機械が同義語を推測すると業務の意味が変わるため、
    置換の知識は人が持つ（`promote_map.example.txt` が雛形）。
    """
    path = root / MAP_TXT.relative_to(ROOT) if root != ROOT else MAP_TXT
    if not path.is_file():
        return []
    pairs: list[tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=>" not in text:
            continue
        src, dst = text.split("=>", 1)
        src, dst = src.strip(), dst.strip()
        if src and dst and src != dst:
            pairs.append((src, dst))
    pairs.sort(key=lambda pair: len(pair[0]), reverse=True)
    return pairs


def draft(path: Path, root: Path, out: Path | None = None) -> dict:
    """匿名化の**下書き**を作る。原本は書き換えない。

    - 置換表にある語だけを置き換える（推測しない）
    - 置き換えられなかった要修正語は、下書きの冒頭に「未対応」として並べる
    - front matter は**そのまま**残す（移送時の書換は `apply` の仕事）

    出力は `<stem>.anon.md`（`--out` で変更可）。**人が読んで直してから**原本と差し替える。
    """
    raw = path.read_text(encoding="utf-8")
    if raw.startswith("---"):
        end = raw.find("\n---", 3)
        fm_text, body = (raw[:end + 4], raw[end + 4:]) if end != -1 else ("", raw)
    else:
        fm_text, body = "", raw

    pairs = load_map(root)
    counts: dict[tuple[str, str], int] = {}

    def apply_map(text: str, skip_prefixes: tuple[str, ...] = ()) -> str:
        lines = []
        for line in text.splitlines(keepends=True):
            if any(line.lstrip().startswith(prefix) for prefix in skip_prefixes):
                lines.append(line)
                continue
            for src, dst in pairs:
                n = line.count(src)
                if n:
                    counts[(src, dst)] = counts.get((src, dst), 0) + n
                    line = line.replace(src, dst)
            lines.append(line)
        return "".join(lines)

    # `doc_id` と `project_id` は移送時に `apply` が書き換えるので、ここでは触らない。
    fm_text = apply_map(fm_text, ("doc_id:", "project_id:"))
    body = apply_map(body)
    applied = [{"from": s, "to": d, "count": n} for (s, d), n in counts.items()]

    report = check(path, root)
    remaining: list[str] = []
    for hit in report["hits"]:
        term = str(hit.get("text") or "")
        if hit.get("level") != "block" or not term:
            continue
        if term in body and term not in remaining:
            remaining.append(term)

    # 既定の出力先は **repo/ の外**。repo/ の中に置くと知識ベースに索引され、
    # 原本と下書きが二重にヒットして検索を汚す。
    dest = out or (root / "reports" / "promote-drafts" / f"{path.stem}.anon.md")
    dest.parent.mkdir(parents=True, exist_ok=True)
    # ★ 注記は front matter の**後ろ**に置く（前に置くと front matter が読めなくなる）。
    # ★ 注記に案件名・ファイルパスを書かない（書くとそれ自体が要修正として拾われる）。
    #   置換の内訳は標準出力に出す——ファイルには残さない。
    note = (
        f"<!-- [kb_promote draft] 匿名化の下書き。原本ではない。"
        f"置換 {len(applied)} 組 / 未対応 {len(remaining)} 件 -->\n"
    )
    separator = "" if fm_text.endswith("\n") else "\n"
    dest.write_text(fm_text + separator + note + "\n" + body.lstrip("\n"), encoding="utf-8")
    return {"source": _rel(path, root), "out": _rel(dest, root),
            "applied": applied, "remaining": remaining}


def _kind_of(heading: str) -> str:
    """`# 顧客名` のような見出しを、検査で使う 3 区分へ寄せる。"""
    if "人名" in heading or "個人" in heading:
        return "人名"
    if "案件" in heading or "システム" in heading or "製品" in heading:
        return "案件名"
    if "顧客" in heading or "会社" in heading or "客先" in heading:
        return "顧客名"
    return "顧客名"


def _denylist(root: Path) -> list[tuple[str, str]]:
    """遮蔽すべき語を (区分, 語) で返す。

    形式は **人が書きやすいテキスト**（1 行 1 語、`#` で区分見出し）を既定とする：
    ```
    # 顧客名
    顧客A
    # 人名
    〈人名〉
    # 案件名
    R60
    ```
    旧形式の JSON（`promote_denylist.json`・`names` 配列）も読む（後方互換）。
    """
    txt = root / DENYLIST_TXT.relative_to(ROOT) if root != ROOT else DENYLIST_TXT
    if txt.is_file():
        out: list[tuple[str, str]] = []
        kind = "顧客名"
        for line in txt.read_text(encoding="utf-8").splitlines():
            text = line.strip()
            if not text:
                continue
            if text.startswith("#"):
                kind = _kind_of(text.lstrip("#").strip())
                continue
            out.append((kind, text))
        return out

    path = root / DENYLIST.relative_to(ROOT) if root != ROOT else DENYLIST
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if isinstance(data, dict):
        data = data.get("names") or []
    return [("顧客名", str(x)) for x in data if str(x).strip()]


def check(path: Path, root: Path, *, body_only: bool = False) -> dict:
    """1 ファイルの匿名化体检。ヒットを返すだけで、合否は決めない。

    `body_only=True` のときは front matter の残留（`scope` / `project_id` / `doc_id`）を
    見ない。**下書き（`draft`）の本文を確かめるときに使う**——front matter は移送時に
    `apply` が書き換えるので、ここで赤にしても意味がない。
    """
    from tools.trace_check import load_secret_patterns, scan_text

    text = path.read_text(encoding="utf-8")
    meta, body = split_front_matter(text)

    hits: list[dict] = []
    for h in scan_text(body, patterns=load_secret_patterns(root), rel=_rel(path, root), root=root):
        hits.append({"kind": f"機密/{h['kind']}", "line": h["line"], "text": h["match"], "level": "block"})

    for label, pat, level in IDENTIFIER_PATTERNS:
        for lineno, line in enumerate(body.splitlines(), 1):
            m = pat.search(line)
            if m:
                hits.append({"kind": label, "line": lineno, "text": m.group(0)[:60], "level": level})

    for lineno, line in enumerate(body.splitlines(), 1):
        for token in _IDENT_RE.findall(line):
            if _case_specific(token):
                hits.append({"kind": "物理名（案件接頭辞つき）", "line": lineno,
                             "text": token[:60], "level": "block"})

    names = _denylist(root)
    for kind, term in names:
        for lineno, line in enumerate(body.splitlines(), 1):
            if term and term in line:
                hits.append({"kind": kind, "line": lineno, "text": term, "level": "block"})

    fm_issues: list[str] = []
    if meta is None:
        fm_issues.append("front matter が無い（会社級条目は必須）")
    else:
        for key in FM_MIN_KEYS:
            if key not in meta:
                fm_issues.append(f"front matter に `{key}` が無い")
        if meta.get("project_id"):
            fm_issues.append("`project_id` が残っている（scope=company では禁止）")
        if str(meta.get("scope")) != "company":
            fm_issues.append(f"`scope` が company ではない（{meta.get('scope')!r}）")
        doc_id = str(meta.get("doc_id") or "")
        if re.search(r"-0\d{2}-", doc_id):
            fm_issues.append(f"`doc_id` が案件採番の形（{doc_id}）— 会社級は <種別>-<領域>-<連番>")

    blocking = [h for h in hits if h.get("level") == "block"]
    if body_only:
        fm_issues = []
    return {
        "file": _rel(path, root),
        "front_matter_issues": fm_issues,
        "hits": hits,
        "blocking": len(blocking),
        "warning": len(hits) - len(blocking),
        "denylist_count": len(names),
        "ok": not fm_issues and not blocking,
    }


PLACEHOLDER = "<…>"
_TABLE_SEP_RE = re.compile(r"^\|[\s:|-]+\|$")


def _is_special(stripped: str) -> bool:
    """段落として吸収してはいけない行（見出し・表・引用・フェンス・記号・区切り線）。"""
    return (
        stripped.startswith(("#", "|", ">", "```", "-", "*", "+"))
        or bool(re.match(r"^\d+\.\s", stripped))
        or bool(re.fullmatch(r"[-*_]{3,}", stripped))
    )


def _table_placeholder(block: list[str]) -> list[str]:
    """表ブロックを「見出し＋区切り＋1 行の占位」に畳む。列数は見出しから取る。"""
    header = block[0]
    ncols = max(1, header.count("|") - 1)
    out = [header]
    if len(block) > 1 and _TABLE_SEP_RE.match(block[1].strip()):
        out.append(block[1])
    out.append("|" + "|".join([PLACEHOLDER] * ncols) + "|")
    return out


def skeleton(text: str) -> str:
    """成果物の Markdown から骨格（テンプレート）を抜く。

    **残す**：見出し・表の見出し行・リスト記号・コードフェンスの言語・空行
    **置き換える**：段落・表の本体・コードの中身 → `<…>`

    ★ 見出しは残す。見出しに案件名が入っていれば `check` が後で拾う——
      機械が文意を判断して見出しを書き換えると、意味が変わる危険のほうが大きい。
    """
    _meta, body = split_front_matter(text)
    lines = body.splitlines()

    out: list[str] = []
    in_code = False
    i = 0
    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()
        stripped = line.strip()

        # コードブロック：フェンスと言語は残し、中身は 1 行の占位へ
        if stripped.startswith("```"):
            out.append(line)
            in_code = not in_code
            i += 1
            if in_code:
                # 中身を読み飛ばす（次のフェンスまで）
                j = i
                while j < len(lines) and not lines[j].strip().startswith("```"):
                    j += 1
                if j > i:
                    out.append(PLACEHOLDER)
                i = j
            continue

        if not stripped:
            out.append("")
            i += 1
            continue

        # 表：連続する `|` 行をひとまとめに扱う
        if stripped.startswith("|"):
            j = i
            block = []
            while j < len(lines) and lines[j].strip().startswith("|"):
                block.append(lines[j].rstrip())
                j += 1
            out.extend(_table_placeholder(block))
            i = j
            continue

        # 見出しは残す（構造そのものがテンプレートの価値）
        if stripped.startswith("#"):
            out.append(line)
            i += 1
            continue

        # 箇条書き・番号付き・チェックボックス：記号だけ残す
        m = re.match(r"^(\s*)([-*+]|\d+\.)\s+(\[[ xX]\]\s+)?(.*)$", line)
        if m:
            indent, marker, box, _rest = m.groups()
            out.append(f"{indent}{marker} {box or ''}{PLACEHOLDER}")
            i += 1
            continue

        # 引用：連続する引用行を 1 つに畳む
        if stripped.startswith(">"):
            j = i
            while j < len(lines) and lines[j].strip().startswith(">"):
                j += 1
            out.append("> " + PLACEHOLDER)
            i = j
            continue

        # 区切り線はそのまま
        if re.fullmatch(r"[-*_]{3,}", stripped):
            out.append(line)
            i += 1
            continue

        # 段落：連続する地の文を 1 つの占位にまとめる。
        # **必ず 1 行以上進める**（特殊行がどの分岐にも当たらなかったときに止まらないため）。
        j = i + 1
        while j < len(lines) and lines[j].strip() and not _is_special(lines[j].strip()):
            j += 1
        out.append(PLACEHOLDER)
        i = j

    # 連続する空行を 1 つに畳む
    collapsed: list[str] = []
    for line in out:
        if line == "" and collapsed and collapsed[-1] == "":
            continue
        collapsed.append(line)
    return "\n".join(collapsed).strip() + "\n"


def write_skeleton(src: Path, out_path: Path | None, *, source_project: str | None,
                   doc_id: str | None, title: str | None) -> str:
    """骨格を front matter 付きで組み立てる（書き出しは呼び出し側）。"""
    text = src.read_text(encoding="utf-8")
    meta, body = split_front_matter(text)
    meta = meta or {}
    base_title = title or str(meta.get("title") or "").strip()
    if not base_title:
        m = re.search(r"^#\s+(.+)$", body, re.M)
        base_title = m.group(1).strip() if m else src.stem
    new_title = base_title if "テンプレート" in base_title else f"{base_title} テンプレート"

    fm = {
        "doc_id": doc_id or "TPL-001",
        "scope": "company",
        "title": new_title,
        "doc_type": "template",
        "version": "1.0",
        "status": "draft",
        "conf_level": 20,
        "owner": "共通基盤チーム",
        "updated_at": str(date.today()),
    }
    if source_project:
        fm["source_project"] = source_project
    return "---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False).rstrip() + "\n---\n\n" + skeleton(text)


#: `doc_type` → `doc_id` の接頭辞。既存の会社級条目（`STD-*` / `PAT-*`）に合わせる。
DOC_ID_PREFIX = {
    "standard": "STD",
    "pattern": "PAT",
    "glossary": "GLO",
    "decision": "DEC",
    "howto": "HOW",
    "template": "TPL",
    "requirement": "REQ",
    "design-basic": "BS",
    "design-detail": "DS",
    "test": "TC",
}


def _all_doc_ids(repo: Path) -> set[str]:
    """`repo/` 全体の doc_id。**doc_id はリポジトリ内で一意**（ガイド §4.2）なので、
    移送先ディレクトリではなく全体で衝突を見る。"""
    out: set[str] = set()
    for path in repo.rglob("*.md"):
        doc_id = _doc_id_of(path)
        if doc_id:
            out.add(doc_id)
    return out


def _next_doc_id(repo: Path, doc_type: str) -> str:
    """`repo/` 全体で衝突しない連番を返す。領域（`REQ-ABC` 等）は人が `--doc-id` で詰める。"""
    prefix = DOC_ID_PREFIX.get(str(doc_type), "GEN")
    pat = re.compile(rf"^{re.escape(prefix)}-(\d{{3}})$")
    used = {int(m.group(1)) for one in _all_doc_ids(repo) if (m := pat.match(one))}
    n = 1
    while n in used:
        n += 1
    return f"{prefix}-{n:03d}"


def _doc_id_of(path: Path) -> str | None:
    try:
        meta, _ = split_front_matter(path.read_text(encoding="utf-8"))
    except OSError:
        return None
    return str(meta.get("doc_id")) if meta and meta.get("doc_id") else None


def plan(path: Path, root: Path, to: str, source_project: str | None, doc_id: str | None) -> dict:
    repo = root / REPO.relative_to(ROOT) if root != ROOT else REPO
    dest_dir = repo / "company" / to
    meta, _ = split_front_matter(path.read_text(encoding="utf-8"))
    meta = meta or {}
    new_id = doc_id or _next_doc_id(repo, str(meta.get("doc_type") or "standard"))

    # 下書きの `.anon.md` は移送先で落とす（そのまま会社級に残ると素性が分かる）。
    name = path.name
    if name.endswith(".anon.md"):
        name = name[: -len(".anon.md")] + ".md"

    # 下書きは `repo/` の外（`reports/promote-drafts/`）にあるので、
    # repo からの相対が取れないときはリポジトリルートからの相対で記録する。
    try:
        from_rel = path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        try:
            from_rel = path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            from_rel = path.as_posix()

    return {
        "from": from_rel,
        "to": _rel(dest_dir / name, repo),
        "doc_id_before": meta.get("doc_id"),
        "doc_id_after": new_id,
        "source_project": source_project,
        "dest_dir_exists": dest_dir.exists(),
        "doc_id_conflict": new_id in _all_doc_ids(repo),
    }


def _rewrite(meta: dict, new_id: str, source_project: str | None) -> str:
    meta = dict(meta)
    meta["doc_id"] = new_id
    meta["scope"] = "company"
    meta.pop("project_id", None)
    if source_project:
        meta["source_project"] = source_project
    body = yaml.safe_dump(meta, allow_unicode=True, sort_keys=False).rstrip()
    return f"---\n{body}\n---\n"


def apply_(path: Path, root: Path, to: str, source_project: str | None,
           doc_id: str | None, by: str, write: bool) -> dict:
    repo = root / REPO.relative_to(ROOT) if root != ROOT else REPO
    p = plan(path, root, to, source_project, doc_id)
    dest = repo / p["to"]
    if p.get("doc_id_conflict"):
        raise SystemExit(
            f"[kb_promote] doc_id が既に存在します: {p['doc_id_after']}"
            f"（`--doc-id` で一意な値を指定してください）"
        )

    # **書き込み前に権限を検査する。** 移送先は通常 `company/` ＝ 会社の責任者だけが書ける。
    # ここを素通りさせると「権限の無い人が会社級へ持ち上げる」経路が開く
    # （`init-glossary` だけが検査していて、移送は抜けていた＝2026-11-05 修正）。
    from tools.kb_acl import check as acl_check

    problems = acl_check([_rel(dest, root)], by, root)
    if problems:
        raise SystemExit("[kb_promote] 権限違反:\n  - " + "\n  - ".join(problems))

    # **移送元がまだ脱敏されていないなら止める。**
    # `apply` は原本をそのまま持って行くだけであり、置換はしない（置換は `draft` の仕事）。
    # ここを見ないと「脱敏可」と評価した条目が、案件名を残したまま会社級に入る
    # （2026-11-10 の実測: R60 が 20 箇所残ったまま移送された）。
    body_report = check(path, root, body_only=True)
    if not body_report["ok"]:
        raise SystemExit(
            "[kb_promote] 移送元がまだ脱敏されていません"
            f"（要修正 {body_report['blocking']} 件）:\n"
            f"  {body_report['file']}\n"
            "  先に `draft` で下書きを作り、内容を確認して**原本と差し替えて**から `apply` してください。"
        )

    if not write:
        return {**p, "written": False}

    meta, body = split_front_matter(path.read_text(encoding="utf-8"))
    if meta is None:
        raise SystemExit(f"[kb_promote] front matter が無いため移送できません: {p['from']}")

    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        raise SystemExit(f"[kb_promote] 移送先が既に存在します: {p['to']}")

    new_text = _rewrite(meta, p["doc_id_after"], source_project).rstrip("\n") + "\n\n" + body.lstrip("\n")
    dest.write_text(new_text, encoding="utf-8")
    path.unlink()

    _log(root, {**p, "by": by, "promoted_at": str(date.today())})
    return {**p, "written": True}


def _log(root: Path, entry: dict) -> None:
    ledger = root / LEDGER.relative_to(ROOT) if root != ROOT else LEDGER
    data = {"promotions": []}
    if ledger.is_file():
        try:
            loaded = yaml.safe_load(ledger.read_text(encoding="utf-8")) or {}
            if isinstance(loaded, dict) and isinstance(loaded.get("promotions"), list):
                data = loaded
        except yaml.YAMLError:
            pass
    data["promotions"].append(entry)
    ledger.write_text(
        "# 会社級への昇格記録（build guide STEP 12）。手で消さない。\n"
        + yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


#: 昇格の対象になりうる `doc_type`。案件の成果物そのもの（要件・設計・試験）は除く——
#: それらは案件の事実であり、抽象化しない限り会社級に置けない。
PROMOTABLE_TYPES = frozenset({"standard", "pattern", "decision", "howto", "glossary", "template"})

#: 構築ガイド §2.1「収録内容」の五類。**どれを昇格するかはこの五類で判断する。**
#: `(見出し, 粒度, 対応する doc_type)`。空の類も並べる——「無い」ことも判断材料である。
GUIDE_CATEGORIES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("規約・標準", "条文単位", ("standard",)),
    ("用語・領域", "語単位", ("glossary",)),
    ("設計パターン", "パターン単位", ("pattern",)),
    ("資産（テンプレート・共通部品）", "モジュール単位", ("template",)),
    ("実績データ", "集計値", ()),   # 現状この種の条目は庫に無い
)

#: 上の五類に入らない doc_type（ガイド §2.1 に区分が無い）。**隠さず別枠で出す。**
GUIDE_UNCATEGORIZED = ("decision", "howto")


def _category_of(doc_type: str) -> str:
    for name, _granularity, types in GUIDE_CATEGORIES:
        if doc_type in types:
            return name
    return "その他（ガイド §2.1 に区分なし）"


def _snippet(body: str, limit: int = 70) -> str:
    """本文の最初の「読める一文」を抜く（判定の材料にする）。見出し・引用・表は飛ばす。"""
    for line in body.splitlines():
        text = line.strip().lstrip("-*+> ").strip()
        if not text or text.startswith(("#", "|", "```", "<")):
            continue
        if text.startswith("**") and text.endswith("**"):
            continue
        return text[:limit] + ("…" if len(text) > limit else "")
    return ""


def candidates(project: str, root: Path, types: set[str] | None = None) -> list[dict]:
    """案件の中で「昇格しうる形」の条目を、匿名化の重さ順に並べて返す。

    **判定はしない。** 昇格するかは人が決める（ガイド §2.2・§9.3）。
    ここが出すのは「どの条目が、どれくらい手を入れれば会社級に出せるか」の目安である。

    `types` で対象を絞れる。実務では 3 種類に限るのが基本である：
      - `template` … 顧客へ出す成果物（設計書など）の**雛形**
      - `glossary` … 案件で使った**専用語**
      - `standard` … **コーディング規約**などの決め事
    """
    repo = root / REPO.relative_to(ROOT) if root != ROOT else REPO
    pdir = repo / "projects" / project
    if not pdir.is_dir():
        raise SystemExit(f"[kb_promote] 案件ディレクトリがありません: projects/{project}")

    wanted = types or PROMOTABLE_TYPES
    out: list[dict] = []
    for path in sorted(pdir.rglob("*.md")):
        # `chunks/` は検索摘要の派生物（`tools/kb_migrate.py` が生成）。知識ではないので候補にしない。
        if "chunks" in path.relative_to(pdir).parts:
            continue
        raw = path.read_text(encoding="utf-8")
        meta, body = split_front_matter(raw)
        if not meta or not meta.get("doc_id"):
            continue
        doc_type = str(meta.get("doc_type") or "")
        if doc_type not in wanted:
            continue
        report = check(path, root)
        out.append({
            "doc_id": str(meta.get("doc_id")),
            "doc_type": doc_type,
            "category": _category_of(doc_type),
            "path": _rel(path, repo),
            "blocking": report["blocking"],
            "warning": report["warning"],
            # 判定の材料（ID と「要修正」だけでは、人が開かないと決められない）
            "title": str(meta.get("title") or ""),
            "lines": len(raw.splitlines()),
            "snippet": _snippet(body),
        })
    out.sort(key=lambda r: (r["blocking"], r["doc_id"]))
    return out


# =============================================================================
# review — 昇格レビュー表（読み取りのみ）
# =============================================================================
#
# なぜ要るか
# ----------
# `candidates` は「候補を並べる」ところで止まり、明示的に**判定をしない**。
# その結果、人に渡るのは「doc_id と 要修正 N 件」だけで、判断には原本を開く必要がある。
# しかも「どれを上げるか」を記録する器が無く、人に聞いた結果は会話の中に消える。
#
# `review` はその間を埋める。**判定はしない**（しないまま、人が決められる形に整える）：
#   1. 会社級に今ある条目を doc_type 別に並べる（「庫に何があるか」を先に見せる）
#   2. 候補ごとに、判定基準 5 条の**うち機械で分かる 2 条**（③第2案件の実績・⑤脱敏の残数）を測る
#   3. 建議と**その理由**を 1 行で出す（理由が無い建議は出さない）
#   4. `[ ]` の勾选欄を持つ Markdown を書き出す（人はここに `x` を入れるだけ）
#   5. `--plan-out` で、勾选済みの行だけを `plan.yaml` にする（それでも移送はしない）
#
# **何も移送しない。** 移送は `apply`（会社級の権限を持つ人）の仕事である。

#: `review` が付ける建議の語彙。**判定ではない。** 人が決めるための材料である。
REVIEW_VERDICTS = ("昇格可", "雛形のみ", "要補表", "見送り", "要人判断")

#: 建議ごとの「次にやること」。表の下に置く。
REVIEW_ACTIONS = {
    "昇格可": "そのまま `plan.yaml` に載せられる。勾选してよい",
    "雛形のみ": "中身は案件の事実。`skeleton` で形だけ抜く",
    "要補表": "先に `tools/kb_local/promote_map.txt` へ語を足す（残件は下の列）",
    "見送り": "第2案件で使われたら見直す。**消さずに案件級へ残す**",
    "要人判断": "判定基準④（形になるか）に当たらない。人が中身を見て決める",
}


def _company_index(root: Path) -> list[dict]:
    """会社級に今ある条目（doc_type 付き）。**分類して見せる**ための材料。"""
    repo = root / REPO.relative_to(ROOT) if root != ROOT else REPO
    cdir = repo / "company"
    out: list[dict] = []
    if not cdir.is_dir():
        return out
    for path in sorted(cdir.rglob("*.md")):
        try:
            meta, _ = split_front_matter(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
        if not meta:
            continue
        out.append({
            "doc_id": str(meta.get("doc_id") or path.stem),
            "doc_type": str(meta.get("doc_type") or ""),
            "title": str(meta.get("title") or ""),
            "path": _rel(path, repo),
        })
    return out


def _second_project_use(doc_id: str, project: str, root: Path,
                        cache: dict[str, str]) -> list[str]:
    """他の案件がこの `doc_id` を引用しているか（判定基準 ③ の材料）。

    **引用が無い＝使えない、ではない。** 「まだ 2 案件目が無い」というだけである。
    """
    repo = root / REPO.relative_to(ROOT) if root != ROOT else REPO
    pdir = repo / "projects"
    if not pdir.is_dir() or not doc_id:
        return []
    hits: list[str] = []
    for other in sorted(p.name for p in pdir.iterdir() if p.is_dir()):
        if other == project:
            continue
        if other not in cache:
            texts: list[str] = []
            for p in sorted((pdir / other).rglob("*.md")):
                if "chunks" in p.relative_to(pdir / other).parts:
                    continue
                try:
                    texts.append(p.read_text(encoding="utf-8"))
                except (OSError, UnicodeDecodeError):
                    continue
            cache[other] = "\n".join(texts)
        if doc_id in cache[other]:
            hits.append(other)
    return hits


def _residual_terms(path: Path, root: Path) -> list[str]:
    """置換表を当てた後に**実際に残る**案件固有語。下書きを一時領域に作って測る。

    ★ 目分量で「表に語があるから消える」と判断してはいけない。
    置換した結果が別のパターンに当たる（例: パス中の案件名を置換しても
    `file.py:23` の形は残る）ため、**当てた後の本文を検査する**。
    一時ファイルは `repo/` の外に作り、終わったら消す。
    """
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as td:
        out = Path(td) / f"{path.stem}.anon.md"
        draft(path, root, out)
        report = check(out, root, body_only=True)
    terms: list[str] = []
    for hit in report["hits"]:
        if hit.get("level") != "block":
            continue
        term = str(hit.get("text") or "")
        if term and term not in terms:
            terms.append(term)
    return sorted(terms)


def _suggest(doc_type: str, residual: list[str], second: list[str]) -> tuple[str, list[str]]:
    """建議と**その理由**を返す。理由の無い建議は返さない（人が検算できないため）。"""
    reasons: list[str] = []
    if doc_type not in ("standard", "glossary", "template", "pattern"):
        reasons.append(f"④ 形にならない（{doc_type}）")
        if residual:
            reasons.append(f"⑤ 案件固有語 {len(residual)} 件残留")
        return "要人判断", reasons

    if residual:
        reasons.append(f"⑤ 脱敏後も案件固有語 {len(residual)} 件残留")
        return "要補表", reasons

    reasons.append("⑤ 脱敏可（残 0 件）")
    if second:
        reasons.append(f"③ 第2案件で利用（{', '.join(second)}）")
        return "昇格可", reasons

    reasons.append("③ 第2案件での利用実績なし")
    reasons.append("④ 形は抽出できる")
    return "雛形のみ", reasons


def review(project: str, root: Path, by: str, out: Path | None = None,
           types: set[str] | None = None) -> dict:
    """昇格レビュー表（Markdown）を作る。**読み取りのみ。何も移送しない。**"""
    rows = candidates(project, root, types)
    cache: dict[str, str] = {}
    items: list[dict] = []
    for row in rows:
        path = (root / REPO.relative_to(ROOT) if root != ROOT else REPO) / row["path"]
        residual = _residual_terms(path, root)
        second = _second_project_use(row["doc_id"], project, root, cache)
        verdict, reasons = _suggest(row["doc_type"], residual, second)
        items.append({**row, "verdict": verdict,
                      "reasons": reasons, "residual": residual, "second": second})
    # 建議の重い順に並べる（人が上から読めるように）。同順位は doc_id。
    rank = {v: i for i, v in enumerate(REVIEW_VERDICTS)}
    items.sort(key=lambda r: (rank.get(r["verdict"], len(REVIEW_VERDICTS)), r["doc_id"]))
    for i, item in enumerate(items, 1):
        item["no"] = i

    company = _company_index(root)
    dest = out or (root / "reports" / f"promote-review-{project}.md")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(_render_review(project, by, items, company), encoding="utf-8")
    return {"project": project, "by": by, "out": _rel(dest, root),
            "items": items, "company": company}


def _render_review(project: str, by: str, items: list[dict], company: list[dict]) -> str:
    lines: list[str] = []
    add = lines.append
    add(f"# 昇格レビュー — {project}")
    add("")
    add(f"> 生成: {date.today().isoformat()} ／ 操作者: {by or '（未記入）'}")
    add("> これは**判断材料**であり判定ではない。判定基準の唯一真源は "
        "`tools/kb-platform/promotion-criteria.md`。")
    add("> **勾选欄に `x` を入れた行だけ**が `--plan-out` で `plan.yaml` に載る。"
        "移送そのものは会社級の権限を持つ人が `apply` で行う。")
    add("")

    # ── 0. 会社級に今あるもの
    add(f"## 0. 会社級に今あるもの（{len(company)} 篇）")
    add("")
    if company:
        by_type: dict[str, list[dict]] = {}
        for c in company:
            by_type.setdefault(c["doc_type"] or "（未設定）", []).append(c)
        add("| doc_type | 件数 | doc_id |")
        add("|---|---|---|")
        for doc_type in sorted(by_type):
            group = by_type[doc_type]
            ids = "、".join(g["doc_id"] for g in group)
            add(f"| {doc_type} | {len(group)} | {ids} |")
    else:
        add("（会社級の条目がありません）")
    add("")

    # ── 1. 候補
    add(f"## 1. 候補（{len(items)} 件）")
    add("")
    if not items:
        add("（昇格しうる doc_type の条目がありません）")
        return "\n".join(lines) + "\n"
    add("| # | 勾选 | 条目 | 分類 | 建議 | 理由 | 残 | 行数 |")
    add("|---|---|---|---|---|---|---|---|")
    for it in items:
        reason = "／".join(it["reasons"])
        add(f"| {it['no']} | [ ] | {it['doc_id']} | {it['category']} | "
            f"{it['verdict']} | {reason} | {len(it['residual'])} | {it['lines']} |")
    add("")

    # ── 2. 建議ごとの次にやること
    add("## 2. 建議ごとの次にやること")
    add("")
    counts: dict[str, int] = {}
    for it in items:
        counts[it["verdict"]] = counts.get(it["verdict"], 0) + 1
    add("| 建議 | 件数 | 次にやること |")
    add("|---|---|---|")
    for verdict in REVIEW_VERDICTS:
        if counts.get(verdict):
            add(f"| {verdict} | {counts[verdict]} | {REVIEW_ACTIONS[verdict]} |")
    add("")

    # ── 3. 脱敏の残件
    stuck = [it for it in items if it["residual"]]
    if stuck:
        add("## 3. 脱敏の残件（置換表に足す語）")
        add("")
        add("| # | 条目 | 残った語 |")
        add("|---|---|---|")
        for it in stuck:
            add(f"| {it['no']} | {it['doc_id']} | {'、'.join(it['residual'])} |")
        add("")
        add("> **語**（`R60_...` など）は `tools/kb_local/promote_map.txt` に `元 => 先` で足す。"
            "**表に無い語は機械が置き換えない**（意味が変わるため）。")
        add("> **`file:line` 参照**は表に足さない——案件の実装の所在そのものであり、"
            "置換ではなく**人が抽象化する**（例: `AppHeader.vue:15` → `＜共通ヘッダ部品＞`）。")
        add("")

    add("## 4. 人がやること（この順で）")
    add("")
    add("1. `勾选` 欄に `x` を入れる（入れた行だけが計画に載る）")
    add("2. **脱敏の下書きを作り、原本と差し替える**（★飛ばさない）")
    add("   ```bash")
    add("   py -3 -m tools.kb_promote draft <原本>      # → reports/promote-drafts/<name>.anon.md")
    add("   py -3 -m tools.kb_promote check <下書き> --body-only   # 「問題なし」を確認")
    add("   # 内容を読んで、問題なければ原本と差し替える")
    add("   ```")
    add("   **`apply` は置換をしない。** 差し替えていない状態で移送しようとすると `apply` が止まる。")
    add("3. `py -3 -m tools.kb_promote review --project "
        f"{project} --as <人> --plan-out reports/promote-plan-{project}.yaml`")
    add("4. `py -3 -m tools.kb_promote plan --from-plan "
        f"reports/promote-plan-{project}.yaml --by <人>` で検証（何も書かない）")
    add("5. 会社級の権限を持つ人が `apply --from-plan ... --apply` を実行")
    add("6. `py -3 -m tools.kb_local ingest --prune` で索引を更新し、"
        "`py -3 -m tools.kb_promote close --project "
        f"{project} --apply --by <PM>` で結案記録を残す")
    return "\n".join(lines) + "\n"


def review_plan(review_path: Path, project: str, root: Path,
                out: Path | None = None) -> dict:
    """レビュー表の勾选（`[x]`）だけを `plan.yaml` にする。**移送しない。**"""
    text = review_path.read_text(encoding="utf-8")
    # 行の形: `| # | [x] | doc_id | 分類 | 建議 | 理由 | 残 | 行数 |`。
    # 番号ではなく **doc_id** で引く（表の並びは建議順に変わりうるため）。
    checked: list[tuple[str, str]] = []
    for line in text.splitlines():
        m = re.match(r"^\|\s*\d+\s*\|\s*\[[xX]\]\s*\|\s*([^|]+?)\s*\|", line)
        if m:
            checked.append((m.group(1).strip(), m.group(0)))
    by_id = {r["doc_id"]: r for r in candidates(project, root, None)}
    repo = root / REPO.relative_to(ROOT) if root != ROOT else REPO
    entries: list[dict] = []
    skipped: list[dict] = []
    for doc_id, line in checked:
        row = by_id.get(doc_id)
        if not row:
            skipped.append({"doc_id": doc_id, "why": "候補に見つからない（表が古い可能性）"})
            continue
        residual = _residual_terms(repo / row["path"], root)
        if residual:
            skipped.append({"doc_id": doc_id,
                            "why": f"脱敏の残件 {len(residual)} 件"})
            continue
        # `to` は company/ 配下の**ディレクトリ**（ファイル名は plan が元の名前で付ける）。
        folder = {"template": "templates", "glossary": "glossary",
                  "pattern": "patterns", "standard": "standards"}.get(row["doc_type"], "standards")
        entries.append({
            "file": row["path"],
            "to": folder,
            "source_project": project,
        })
    dest = out or (root / "reports" / f"promote-plan-{project}.yaml")
    dest.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "# 昇格計画（review の勾选から生成。**移送はまだしていない**）\n"
        "#\n"
        "# doc_id は省略すると `<種別>-001` に自動採番される（例 STD-001）。\n"
        "# 会社級の命名規約は `<種別>-<領域>-<連番>`（例 STD-CODING-001）なので、\n"
        "# **人が `doc_id:` を足すこと**。足さないと規約外の名前で会社級に入る。\n"
    )
    for e in entries:
        e.setdefault("doc_id", None)
    dest.write_text(
        header + yaml.safe_dump({"promotions": entries}, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return {"out": _rel(dest, root), "checked": [d for d, _ in checked],
            "entries": entries, "skipped": skipped}


#: 案件 ID の形（`SE-001` のような人の識別子は人名ではない）。
_PERSON_CODE_RE = re.compile(r"^[A-Z]{2,5}-\d{2,4}$")

#: 人名として拾ってはいけない役割名・チーム名。
_GENERIC_OWNERS = frozenset({
    "共通基盤チーム", "設計チーム", "開発チーム", "AI-SE", "AI-PG", "KB担当",
    "社内レビュー", "顧客", "運用", "QA", "SE", "PG", "PM",
})


def suggest_denylist(project: str, root: Path) -> dict[str, dict[str, int]]:
    """案件のファイルから「遮蔽すべき語」の候補を集める。

    **判定はしない。** 集めて並べるだけで、どれを残すかは人が決める。
    人名は front matter の `owner` / `approved_by` などから拾うが、
    `SE-001` のような識別子は人名ではないので除く。
    顧客名は**自動では拾えない**（どこにも書かれていないことが多い）ので、人が追記する。
    """
    repo = root / REPO.relative_to(ROOT) if root != ROOT else REPO
    pdir = repo / "projects" / project
    if not pdir.is_dir():
        raise SystemExit(f"[kb_promote] 案件ディレクトリがありません: projects/{project}")

    counts: dict[str, dict[str, int]] = {"顧客名": {}, "人名": {}, "案件名": {}}

    def bump(kind: str, term: str) -> None:
        text = str(term).strip()
        if len(text) < 2:
            return
        counts[kind][text] = counts[kind].get(text, 0) + 1

    bump("案件名", project)
    # `P-R60-001` の中央部分（`R60`）はシステム名として必ず遮蔽対象になる。
    parts = project.split("-")
    if len(parts) >= 3:
        bump("案件名", parts[1])

    for path in sorted(pdir.rglob("*.md")):
        if "chunks" in path.relative_to(pdir).parts:
            continue
        try:
            raw = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        meta, body = split_front_matter(raw)

        # `R60Area` / `R60W0006` のような **接頭辞＋本体** の形だけを拾う。
        # 単独の `HH24`（日付書式）や `BM25`（アルゴリズム）を案件名と誤認しないため。
        for m in re.finditer(r"\b([A-Z]{1,3}\d{2,3})[A-Z][A-Za-z0-9]*", body):
            bump("案件名", m.group(1))

        if meta:
            for key in ("owner", "approved_by", "by", "raised_by"):
                value = meta.get(key)
                values = value if isinstance(value, list) else ([value] if value else [])
                for item in values:
                    text = str(item).strip()
                    if not text or _PERSON_CODE_RE.match(text) or text in _GENERIC_OWNERS:
                        continue
                    bump("人名", text)
    return counts


def format_denylist(counts: dict[str, dict[str, int]]) -> str:
    """`promote_denylist.txt` の形に整える（そのまま保存できる）。"""
    lines = [
        "# 遮蔽語リスト（匿名化体检で使う）",
        "# 1 行 1 語。`#` で区分を切り替える。空行と `#` 行は無視される。",
        "# 保存先: tools/kb_local/promote_denylist.txt（gitignore 済）",
        "",
        "# 顧客名（会社名・呼称）",
        "# ↑ 自動では拾えない。客先の呼び方・社名・略称を人が書く",
        "",
        "# 人名",
    ]
    for term, n in sorted(counts.get("人名", {}).items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(term)
    lines += ["", "# 案件名・システム名"]
    for term, n in sorted(counts.get("案件名", {}).items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(term)
    lines.append("")
    return "\n".join(lines)


def init_glossary(project: str, root: Path, doc_id: str | None, by: str, write: bool) -> dict:
    """案件の用語集を起こす（`TPL-GLOSSARY-001` の構造を写す）。

    **書き込み前に権限を検査する**（`tools.kb_acl`）。案件級は PM だけが作れる。
    結案済みの案件なら `kb_acl` が拒否する——自分の作った規則を自分で破らないため。
    """
    from tools.kb_acl import check as acl_check
    from tools.kb_acl import load_owners

    repo = root / REPO.relative_to(ROOT) if root != ROOT else REPO
    pdir = repo / "projects" / project
    if not pdir.is_dir():
        raise SystemExit(f"[kb_promote] 案件ディレクトリがありません: projects/{project}")

    dest = pdir / "glossary" / "terms.md"
    rel = _rel(dest, root)
    problems = acl_check([rel], by, root)
    if problems:
        raise SystemExit("[kb_promote] 権限違反:\n  - " + "\n  - ".join(problems))

    owners = load_owners(root)
    owner = (owners["projects"].get(project) or {}).get("owner") or by
    # 既存の案件 doc_id（`r60-001-screens-*`）に合わせ、先頭の `P-` を落として小文字化する。
    stem = project[2:] if project.upper().startswith("P-") else project
    new_id = doc_id or f"{stem.lower()}-glossary-terms"

    fm = {
        # --- 骨架の 7 字段（gate3）。案件級の知識条目は既存の画面カードと同じ形に揃える ---
        # `SCAN_BASES` が `tools/kb-platform/repo/projects/P-R60-001` を含むため、
        # 案件級の .md は 7 字段が無いと gate3 で落ちる。
        "id": f"KNOW-{project.upper()}-GLOSSARY-TERMS",
        "type": "knowledge",
        "req_ids": [],
        "sensitivity": "internal",
        # --- 知識ベースの項目（`tools.kb_local lint` が見る）---
        "doc_id": new_id,
        "scope": "project",
        "project_id": project,
        "title": f"用語集 — {project}",
        "doc_type": "glossary",
        "version": "0.1.0",
        # `draft` は既定で検索に出ない（`_bootstrap.DEFAULT_RETRIEVABLE`）。
        # 用語集は「作った時点から現場が引く」ものなので `open`（可检索）で起こす。
        "status": "open",
        "conf_level": 30,
        "owner": owner,
        "updated_at": str(date.today()),
    }
    body = f"""# 用語集 — {project}

> 記入規則の正本は `tools/kb-platform/repo/company/templates/glossary.md`（`TPL-GLOSSARY-001`）。
> **案件専用語だけ**を載せる。一般語（画面・一覧・登録）は載せない。
> 空欄を残さない（空欄は「無い」と「まだ書いていない」を区別できない）。

| 用語ID | 用語（原文） | 読み | 中文 | English | 定義（1 文） | 出所 | 備考 |
|---|---|---|---|---|---|---|---|
| 〈この行を消して書き始める〉 |  |  |  |  |  |  |  |
"""
    text = "---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False).rstrip() + "\n---\n\n" + body

    if write:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
    return {"path": rel, "doc_id": new_id, "owner": owner, "written": write}


def _load_batch(path: Path) -> list[dict]:
    """バッチ計画 YAML を読む。

    ```yaml
    promotions:
      - file: projects/P-XXX-001/standards/foo.md
        to: standards/requirements
        doc_id: STD-REQ-FOO-001      # 省略時は自動採番
        source_project: P-XXX-001    # 省略時は --source-project
    ```
    """
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise SystemExit(f"[kb_promote] 計画ファイルを読めません: {exc}")
    if isinstance(data, dict):
        data = data.get("promotions") or []
    if not isinstance(data, list):
        raise SystemExit("[kb_promote] 計画ファイルの形式が不正です（promotions: [...] を期待）")
    for i, entry in enumerate(data, 1):
        if not isinstance(entry, dict) or "file" not in entry or "to" not in entry:
            raise SystemExit(f"[kb_promote] 項目 {i} に `file` / `to` がありません")
    return data


def batch_plans(entries: list[dict], root: Path, default_source: str | None) -> tuple[list[dict], list[str]]:
    """バッチ全件を先に検証する。**1 件でも駄目なら 1 件も動かさない。**"""
    repo = root / REPO.relative_to(ROOT) if root != ROOT else REPO
    plans: list[dict] = []
    errors: list[str] = []
    seen: set[str] = set()

    for i, entry in enumerate(entries, 1):
        path = repo / str(entry["file"])
        if not path.is_file():
            errors.append(f"{i}: ファイルがありません {entry['file']}")
            continue
        if not (entry.get("source_project") or default_source):
            errors.append(f"{i}: `source_project` がありません（会社級条目は必須・`kb-policy.md` §2.3）")
            continue
        try:
            p = plan(path, root, str(entry["to"]),
                     entry.get("source_project") or default_source, entry.get("doc_id"))
        except SystemExit as exc:
            errors.append(f"{i}: {exc}")
            continue
        if p.get("doc_id_conflict"):
            errors.append(f"{i}: doc_id が既存 `{p['doc_id_after']}`")
            continue
        if p["doc_id_after"] in seen:
            errors.append(f"{i}: doc_id がバッチ内で重複 `{p['doc_id_after']}`")
            continue
        if (repo / p["to"]).exists():
            errors.append(f"{i}: 移送先が既に存在 `{p['to']}`")
            continue
        seen.add(p["doc_id_after"])
        plans.append({"plan": p, "path": path, "to": str(entry["to"]),
                      "source_project": entry.get("source_project") or default_source})
    return plans, errors


def run_batch(plans: list[dict], root: Path, by: str, write: bool) -> list[dict]:
    results = []
    for item in plans:
        res = apply_(item["path"], root, item["to"], item["source_project"],
                     item["plan"]["doc_id_after"], by, write)
        results.append(res)
    return results


def close(project: str, root: Path, write: bool, by: str = "") -> dict:
    """案件の結案記録を作る（ガイド §9.3 の 8 項目＋機械項目の実績）。

    読み取り専用の強制は OS 依存で当てにならないので、**印（`CLOSED.md`）を置く**方式にする。
    編集を禁じるのは規約であり、機械は「閉じたこと」を記録するまでを担う。
    """
    repo = root / REPO.relative_to(ROOT) if root != ROOT else REPO
    pdir = repo / "projects" / project
    if not pdir.is_dir():
        raise SystemExit(f"[kb_promote] 案件ディレクトリがありません: projects/{project}")

    ledger = root / LEDGER.relative_to(ROOT) if root != ROOT else LEDGER
    promoted: list[dict] = []
    if ledger.is_file():
        try:
            loaded = yaml.safe_load(ledger.read_text(encoding="utf-8")) or {}
            promoted = [e for e in (loaded.get("promotions") or [])
                        if isinstance(e, dict) and e.get("source_project") == project]
        except yaml.YAMLError:
            promoted = []

    remaining = [p for p in sorted(pdir.rglob("*.md"))
                 if (p.name != "CLOSED.md") and _doc_id_of(p)]

    doc_id = f"{project.lower().replace('-', '')}-closed"
    front = [
        "---",
        f"doc_id: {doc_id}",
        "scope: project",
        f"project_id: {project}",
        f"title: 結案記録 — {project}",
        "doc_type: decision",
        'version: "1.0"',
        "status: draft",          # draft は既定で検索に出ない（未確定の記録を答えにしない）
        "conf_level: 30",
        "owner: KB担当",
        f"updated_at: {date.today()}",
        "---",
        "",
    ]
    lines = front + [
        f"# 結案記録 — {project}",
        "",
        "> 本ファイルは `py -3 -m tools.kb_promote close` が生成する。",
        "> **人は署名すること**（紅線③：承認は人がする）。生成物は人の署名の代わりにならない。",
        "",
        "## 1. 結案チェックリスト（構築ガイド §9.3）",
        "",
        "### 人が確認する項目",
        "- [ ] 結案評議会を実施した",
        "- [ ] 昇格候補を抽出した（`candidates` の出力を添付）",
        "- [ ] 匿名化・抽象化を完了した",
        "- [ ] KB 責任人の承認を得た",
        "",
        "### 機械が実行した項目（本記録で証跡）",
        f"- [{'x' if promoted else ' '}] `git mv` 相当の移送を実行した — **{len(promoted)} 件**",
        f"- [{'x' if promoted else ' '}] front matter を `scope: company` に変更した — **{len(promoted)} 件**",
        f"- [{'x' if promoted else ' '}] `source_project` を記録した — **{len(promoted)} 件**",
        "- [x] 案件ライブラリを読み取り専用にした — **本ファイル（`CLOSED.md`）が印**",
        "",
        "署名: ________________　（責任者の識別子）　日付: ________",
        "",
        "## 2. 本案件から昇格した条目",
        "",
    ]
    if promoted:
        lines += ["| doc_id | 移送元 | 移送先 |", "|---|---|---|"]
        for e in promoted:
            lines.append(f"| `{e.get('doc_id_after')}` | `{e.get('from')}` | `{e.get('to')}` |")
    else:
        lines.append("（まだ 1 件も昇格していない）")

    lines += [
        "",
        "## 3. 残っている条目",
        "",
        f"**{len(remaining)} 篇**が案件ディレクトリに残っている。",
        "昇格しなかった条目も**削除しない**（案件の事実であり、参照されうる）。",
        "",
        "## 4. 読み取り専用の扱い",
        "",
        "本ファイルが存在する案件は**閉じた**ものとして扱う。再開するときは",
        "`CLOSED.md` を消すのではなく、**再開の理由と日付を本ファイルに追記**する（履歴を消さない）。",
        "",
    ]
    text = "\n".join(lines)

    result = {
        "project": project,
        "promoted": len(promoted),
        "remaining": len(remaining),
        "path": _rel(pdir / "CLOSED.md", repo),
    }
    if write:
        # 結案は案件ディレクトリへの書き込み＝**その案件の責任者だけ**ができる。
        from tools.kb_acl import check as acl_check

        rel = _rel(pdir / "CLOSED.md", root)
        problems = acl_check([rel], by, root)
        if problems:
            raise SystemExit("[kb_promote] 権限違反:\n  - " + "\n  - ".join(problems))
        (pdir / "CLOSED.md").write_text(text, encoding="utf-8")
    return {**result, "written": write}


def _print_check(report: dict) -> None:
    print(f"[kb_promote] check: {report['file']}")
    if not report.get("denylist_count"):
        print("  ⚠ 顧客名リストが未設定（tools/kb_local/promote_denylist.json）。"
              "顧客名の検査は行われていない。")
    if report["front_matter_issues"]:
        print("  front matter:")
        for issue in report["front_matter_issues"]:
            print(f"    - {issue}")
    blocking = [h for h in report["hits"] if h.get("level") == "block"]
    warning = [h for h in report["hits"] if h.get("level") != "block"]
    if blocking:
        print(f"  【要修正】{len(blocking)} 件:")
        for h in blocking[:20]:
            print(f"    L{h['line']:<4} [{h['kind']}] {h['text']}")
        if len(blocking) > 20:
            print(f"    … 他 {len(blocking) - 20} 件")
    if warning:
        print(f"  【参考】{len(warning)} 件（例示の可能性あり。人が見て判断する）:")
        for h in warning[:10]:
            print(f"    L{h['line']:<4} [{h['kind']}] {h['text']}")
        if len(warning) > 10:
            print(f"    … 他 {len(warning) - 10} 件")
    print(f"  判定: {'問題なし（人による最終確認は必要）' if report['ok'] else '要修正（このままでは会社級に出せない）'}")


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    ap = argparse.ArgumentParser(prog="tools.kb_promote", description="案件知識を会社級へ昇格する")
    ap.add_argument("--root", default=str(ROOT), help="リポジトリルート（テスト用）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check", help="匿名化体检（読み取りのみ）")
    c.add_argument("file")
    c.add_argument("--body-only", dest="body_only", action="store_true",
                   help="本文だけを見る（front matter の残留は apply が処理する）")

    cd = sub.add_parser("candidates", help="昇格しうる条目を列挙（読み取りのみ）")
    cd.add_argument("--project", required=True, help="案件 ID（例 P-R60-001）")
    cd.add_argument("--types", default=None,
                    help="対象の doc_type をカンマ区切りで絞る（例 template,glossary,standard）")

    rv = sub.add_parser("review", help="昇格レビュー表を作る（読み取りのみ・移送しない）")
    rv.add_argument("--project", required=True, help="案件 ID（例 P-R60-001）")
    rv.add_argument("--as", dest="as_user", default="",
                    help="操作者（人の識別子。レビューを作った人）")
    rv.add_argument("--types", default=None,
                    help="対象の doc_type をカンマ区切りで絞る（例 template,glossary,standard）")
    rv.add_argument("--out", default=None,
                    help="出力先（省略時 reports/promote-review-<project>.md）")
    rv.add_argument("--from-review", dest="from_review", default=None,
                    help="勾选を読むレビュー表（省略時は --out か既定パス）")
    rv.add_argument("--plan-out", dest="plan_out", default=None,
                    help="勾选済みのレビュー表から plan.yaml を作る（**移送はしない**）")

    ig = sub.add_parser("init-glossary", help="案件の用語集を起こす（権限検査つき）")
    ig.add_argument("--project", required=True, help="案件 ID（例 P-R60-001）")
    ig.add_argument("--doc-id", default=None)
    ig.add_argument("--by", default="", help="操作者（案件責任者の識別子）")
    ig.add_argument("--apply", action="store_true", help="ファイルを作る")

    dl = sub.add_parser("denylist", help="遮蔽語の候補を集める（人が確認して保存する）")
    dl.add_argument("--project", required=True, help="案件 ID（例 P-R60-001）")

    dr = sub.add_parser("draft", help="匿名化の下書きを作る（原本は書き換えない）")
    dr.add_argument("file", help="匿名化したい案件の成果物")
    dr.add_argument("--out", default=None, help="出力先（省略時は <stem>.anon.md）")

    sk = sub.add_parser("skeleton", help="成果物から雛形（テンプレート）を抜く")
    sk.add_argument("file", help="顧客へ出した成果物の .md")
    sk.add_argument("--out", default=None, help="書き出し先（省略時は標準出力）")
    sk.add_argument("--source-project", default=None, help="昇格元の案件 ID")
    sk.add_argument("--doc-id", default=None, help="新しい doc_id（省略時は TPL-001）")
    sk.add_argument("--title", default=None, help="タイトル（省略時は原文の title）")

    for name, help_text in (
        ("plan", "移送内容を表示（書き込まない）"),
        ("apply", "移送する（--apply で実行。--from-plan で一括）"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("file", nargs="?", default=None, help="単件のときのファイル")
        p.add_argument("--from-plan", dest="from_plan", default=None,
                       help="一括計画 YAML（file / to / doc_id / source_project の配列）")
        p.add_argument("--to", default=None, help="company/ からの相対パス（単件のとき必須）")
        p.add_argument("--source-project", default=None, help="昇格元の案件 ID")
        p.add_argument("--doc-id", default=None, help="新しい doc_id（省略時は自動採番）")
        p.add_argument("--by", default="", help="承認した人の識別子（紅線③）")
        p.add_argument("--apply", action="store_true", help="実際に書き込む")

    cl = sub.add_parser("close", help="結案記録を作る（ガイド §9.3）")
    cl.add_argument("--project", required=True, help="案件 ID（例 P-R60-001）")
    cl.add_argument("--apply", action="store_true", help="CLOSED.md を書き出す")
    cl.add_argument("--by", default="", help="操作者（案件の責任者。紅線③）")

    args = ap.parse_args(argv)
    root = Path(args.root).resolve()

    if args.cmd == "review":
        if not args.as_user:
            print("[kb_promote] --as が必要です（レビューを作る人の識別子）", file=sys.stderr)
            return 2
        if args.plan_out:
            src = Path(args.from_review) if args.from_review else (
                Path(args.out) if args.out else (
                    root / "reports" / f"promote-review-{args.project}.md"))
            if not src.is_file():
                print(f"[kb_promote] レビュー表がありません: {src}", file=sys.stderr)
                return 2
            result = review_plan(src, args.project, root, Path(args.plan_out))
            _out(json.dumps(result, ensure_ascii=False, indent=2))
            if result["skipped"]:
                _out(f"  ※ 勾选 {len(result['checked'])} 件のうち "
                     f"{len(result['skipped'])} 件は載せていません（上記 skipped）")
            _out("  ※ 移送はしていません。`plan --from-plan` で検証し、"
                 "会社級の権限を持つ人が `apply` してください。")
            return 0
        types = {t.strip() for t in args.types.split(",") if t.strip()} if args.types else None
        result = review(args.project, root, args.as_user,
                        Path(args.out) if args.out else None, types)
        counts: dict[str, int] = {}
        for it in result["items"]:
            counts[it["verdict"]] = counts.get(it["verdict"], 0) + 1
        _out(f"[kb_promote] レビュー表を書き出しました: {result['out']}")
        _out(f"  会社級: {len(result['company'])} 篇 ／ 候補: {len(result['items'])} 件")
        for verdict in REVIEW_VERDICTS:
            if counts.get(verdict):
                _out(f"  {verdict}: {counts[verdict]} 件 — {REVIEW_ACTIONS[verdict]}")
        _out("  ※ 判定はしていません。表の勾选欄に `x` を入れてから `--plan-out` を実行してください。")
        return 0

    if args.cmd == "check":
        path = Path(args.file)
        if not path.is_file():
            print(f"[kb_promote] ファイルがありません: {path}", file=sys.stderr)
            return 2
        report = check(path, root, body_only=getattr(args, "body_only", False))
        _print_check(report)
        return 0 if report["ok"] else 1

    if args.cmd == "init-glossary":
        if not args.by:
            print("[kb_promote] --by が必要です（案件責任者の識別子）", file=sys.stderr)
            return 2
        result = init_glossary(args.project, root, args.doc_id, args.by, args.apply)
        _out(json.dumps(result, ensure_ascii=False, indent=2))
        if not args.apply:
            _out("  （dry-run。作るには --apply）")
        else:
            _out("  次に `py -3 -m tools.kb_local lint` と `ingest` を実行してください。")
        return 0

    if args.cmd == "denylist":
        counts = suggest_denylist(args.project, root)
        _out(format_denylist(counts))
        _out("  ※ 上記を tools/kb_local/promote_denylist.txt に保存し、顧客名を追記してください。")
        return 0

    if args.cmd == "draft":
        path = Path(args.file)
        if not path.is_file():
            print(f"[kb_promote] ファイルがありません: {path}", file=sys.stderr)
            return 2
        result = draft(path, root, Path(args.out) if args.out else None)
        _out(json.dumps(result, ensure_ascii=False, indent=2))
        verdict = check(Path(result["out"]), root, body_only=True)
        if verdict["ok"]:
            _out(f"  下書きの本文: OK（要修正 0 件 / 参考 {verdict['warning']} 件）")
        else:
            _out(f"  下書きの本文: 要修正 {verdict['blocking']} 件 — "
                 "置換表に語を足すか、人が直してください")
        _out("  ※ 下書きです。内容を確認してから原本と差し替えてください。")
        return 0

    if args.cmd == "skeleton":
        path = Path(args.file)
        if not path.is_file():
            print(f"[kb_promote] ファイルがありません: {path}", file=sys.stderr)
            return 2
        text = write_skeleton(path, None, source_project=args.source_project,
                              doc_id=args.doc_id, title=args.title)
        if args.out:
            Path(args.out).write_text(text, encoding="utf-8")
            _out(f"[kb_promote] 雛形を書き出しました: {args.out}")
            _out("  ※ 見出しに案件名が残ることがあります。`check` で確認し、人が直してください。")
        else:
            _out(text)
        return 0

    if args.cmd == "candidates":
        explicit_types = bool(args.types)
        types = {t.strip() for t in args.types.split(",") if t.strip()} if args.types else None
        rows = candidates(args.project, root, types)
        if not rows:
            _out("（昇格しうる doc_type の条目がありません）")
            return 0
        groups: dict[str, list[dict]] = {}
        for r in rows:
            groups.setdefault(r["category"], []).append(r)

        _out(f"[candidates] {args.project}: {len(rows)} 件"
             "（構築ガイド §2.1 の五類で分類。判定はしません）")
        _out("")
        order = [name for name, _, _ in GUIDE_CATEGORIES] + ["その他（ガイド §2.1 に区分なし）"]
        index = 0
        for name in order:
            items = groups.get(name, [])
            granularity = next((g for nm, g, _ in GUIDE_CATEGORIES if nm == name), "")
            head = f"■ {name}" + (f"（{granularity}）" if granularity else "")
            if not items:
                _out(f"{head} — 0 件")
                if name == "実績データ":
                    _out("   （集計値の条目は庫に無い。估算・工数・品質実績はまだ整備していない）")
                else:
                    _out("   （この案件には該当なし）")
                _out("")
                continue
            if name.startswith("その他") and not explicit_types:
                # ガイドの五類に入らないもの（レビュー記録・手順など）は**数だけ**出す。
                # 全部並べると、本来見るべき五類が埋もれる。
                # **`--types` で明示されたときは列挙する**（見たいと言っているので）。
                _out(f"{head} — {len(items)} 件"
                     "（既定では列挙しない。見るには --types decision,howto）")
                _out("")
                continue
            _out(f"{head} — {len(items)} 件")
            for r in items:
                index += 1
                _out(f"  {index}. {r['doc_id']}  [{r['doc_type']}]  "
                     f"要修正 {r['blocking']} / 参考 {r['warning']}")
                if r.get("title"):
                    _out(f"     {r['title']}")
                _out(f"     {r.get('lines', '?')} 行 · {r['path']}")
                if r.get("snippet"):
                    _out(f"     └ {r['snippet']}")
            _out("")
        _out("※ どれを昇格するかは人が決める（ガイド §2.2。目安は「2 案件目でも使われたもの」）。")
        return 0

    if args.cmd == "close":
        result = close(args.project, root, args.apply, args.by)
        _out(json.dumps(result, ensure_ascii=False, indent=2))
        if not args.apply:
            _out("  （dry-run。書き出すには --apply）")
        return 0

    # ---- plan / apply ----
    if args.from_plan:
        entries = _load_batch(Path(args.from_plan))
        plans, errors = batch_plans(entries, root, args.source_project)
        if errors:
            _out(f"[kb_promote] 検証で {len(errors)} 件の不備。**1 件も動かしていません。**")
            for err in errors:
                _out(f"  - {err}")
            return 1
        if args.cmd == "plan" or not args.apply:
            _out(json.dumps([p["plan"] for p in plans], ensure_ascii=False, indent=2))
            if args.cmd == "apply" and not args.apply:
                _out("  （dry-run。実行するには --apply）")
            return 0
        if not args.by:
            print("[kb_promote] --by が必要です（承認した人の識別子。紅線③）", file=sys.stderr)
            return 2
        results = run_batch(plans, root, args.by, True)
        _out(json.dumps(results, ensure_ascii=False, indent=2))
        _out(f"[kb_promote] {len(results)} 件を移送しました。続けて `py -3 -m tools.kb_local ingest` で索引を更新してください。")
        return 0

    if not args.file or not args.to:
        print("[kb_promote] 単件のときは <file> と --to が必要です（一括は --from-plan）", file=sys.stderr)
        return 2
    path = Path(args.file)
    if not path.is_file():
        print(f"[kb_promote] ファイルがありません: {path}", file=sys.stderr)
        return 2

    if args.cmd == "plan":
        p = plan(path, root, args.to, args.source_project, args.doc_id)
        print(json.dumps(p, ensure_ascii=False, indent=2))
        return 0

    if not args.apply:
        # 予演でも**権限を検査する**（書き込みはしない）。
        # 予演が通ってから本番で弾かれると、何が悪いのか分からない。
        p = apply_(path, root, args.to, args.source_project, args.doc_id, args.by, False)
        print(json.dumps({**p, "note": "dry-run。実行するには --apply"}, ensure_ascii=False, indent=2))
        return 0
    if not args.by:
        print("[kb_promote] --by が必要です（承認した人の識別子。紅線③）", file=sys.stderr)
        return 2
    result = apply_(path, root, args.to, args.source_project, args.doc_id, args.by, True)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("[kb_promote] 移送しました。続けて `py -3 -m tools.kb_local ingest` で索引を更新してください。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

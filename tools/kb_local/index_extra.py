"""front matter の `req_ids` / `source_project` を退避表 `kb_doc_extra` に持つ。

なぜ上流スキーマを触らないか
--------------------------
`kb_doc` / `kb_chunk` は上流 `kbkit.pipeline.ingest()` が作る表であり、我々の持ち物ではない
（`tools/kb-platform/VENDORED.md`：合格条件は「本地改変（コード）= 0」）。
列を足すと上流の再 ingest で上書きされ、同期のたびに当て直しが要る。
そこで **別表 `kb_doc_extra`** に置き、検索時は LEFT JOIN で引く（差し込みは `_bootstrap.py`）。

何を入れるか
------------
- `req_ids`        … 知識条目がどの要求に紐づくか。知識から要求への追跡の下端。
- `source_project` … 昇格元の案件 ID。構築ガイド §2.2「有出处」・§9.3 結案チェックの実体。

使い方
------
    py -3 -m tools.kb_local extra sync      # repo/ を走査して退避表を作り直す（冪等）
    py -3 -m tools.kb_local extra report    # 出处の有無を数える（只读）
    py -3 -m tools.kb_local extra --self-test

★ 判定はしない。front matter に書かれている値をそのまま写すだけである。
  「この条目は昇格に値するか」「出处は正しいか」は人の判断であり、ここでは扱わない。
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import tempfile
from pathlib import Path

import yaml

#: `source_project` に書いてよい「案件以外の出所」。構築ガイド §2.2④ の「有出处」を、
#: 案件由来でない条目でも満たせるようにするための語彙である（`kb-policy.md` §2.3 が正）。
#: - `upstream-demo`  … 上流 kb-platform が同梱していたデモ用文書
#: - `framework-rules` … 骨架の `.claude/rules/` 等から整理した条目（案件の沈殿ではない）
LEGAL_SOURCE_MARKERS = frozenset({"upstream-demo", "framework-rules"})

_PROJECT_ID_RE = re.compile(r"^P-[A-Z0-9]+-\d{3}$")


def is_legal_source(value: str | None) -> bool:
    """`source_project` の値が許される形か。案件 ID か、上記の標識のいずれか。"""
    if not value:
        return False
    text = str(value).strip()
    return text in LEGAL_SOURCE_MARKERS or bool(_PROJECT_ID_RE.match(text))


TABLE_DDL = """
CREATE TABLE IF NOT EXISTS kb_doc_extra (
    doc_id         TEXT PRIMARY KEY,
    source_project TEXT,
    req_ids        TEXT,
    updated_at     TEXT,
    sha_norm       TEXT
)
"""


def ensure_table(conn: sqlite3.Connection) -> None:
    """退避表が無ければ作る。在れば何もしない（冪等）。

    既存 DB には `sha_norm` が無いので、無ければ足す（ALTER は 1 回だけ効く）。
    `sha_norm` は**改行を LF に揃えた**本文の指紋である（`freshness` 用）。
    """
    conn.execute(TABLE_DDL)
    cols = {row[1] for row in conn.execute("PRAGMA table_info(kb_doc_extra)")}
    if "sha_norm" not in cols:
        conn.execute("ALTER TABLE kb_doc_extra ADD COLUMN sha_norm TEXT")
    conn.commit()


def has_table(conn: sqlite3.Connection, name: str = "kb_doc_extra") -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row is not None


def front_matter(path: Path) -> dict | None:
    """`---` で挟まれた front matter を dict で返す。無ければ None。

    壊れた YAML は握り潰して None（走査を止めない）。判定は lint の仕事である。
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        data = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def _sha_norm(raw: bytes) -> str:
    """改行を LF に揃えた本文の指紋。

    Windows のチェックアウト（`core.autocrlf`）で CRLF と LF が入れ替わるたびに
    「内容が変わった」と誤判定しないため、比較用の指紋は正規化して持つ。
    """
    return hashlib.sha256(
        raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    ).hexdigest()


def _rows(root: Path) -> list[tuple[str, str | None, str, str, str]]:
    """repo/ 配下の .md を走査し
    (doc_id, source_project, req_ids_json, updated_at, sha_norm) を返す。"""
    out: list[tuple[str, str | None, str, str, str]] = []
    for path in sorted(root.rglob("*.md")):
        fm = front_matter(path)
        if not fm:
            continue
        doc_id = fm.get("doc_id")
        if not doc_id:
            continue
        req_ids = fm.get("req_ids") or []
        if isinstance(req_ids, str):
            req_ids = [req_ids]
        try:
            raw = path.read_bytes()
        except OSError:
            continue
        out.append((
            str(doc_id),
            (str(fm["source_project"]) if fm.get("source_project") else None),
            json.dumps(list(req_ids), ensure_ascii=False),
            str(fm.get("updated_at") or fm.get("updated") or ""),
            _sha_norm(raw),
        ))
    return out


def sync(root: Path, db: Path) -> dict:
    """退避表を repo/ の現状に合わせる（冪等）。`kb_doc` に無い doc_id は入れない。

    `kb_doc` に無いものを入れると、検索にも出ない幽霊行が増えるだけである。
    """
    conn = sqlite3.connect(db)
    ensure_table(conn)
    indexed = {r[0] for r in conn.execute("SELECT doc_id FROM kb_doc")} if has_table(conn, "kb_doc") else set()

    rows = [r for r in _rows(root) if r[0] in indexed]
    conn.executemany(
        "INSERT INTO kb_doc_extra(doc_id, source_project, req_ids, updated_at, sha_norm) "
        "VALUES(?,?,?,?,?) ON CONFLICT(doc_id) DO UPDATE SET "
        "source_project=excluded.source_project, req_ids=excluded.req_ids, "
        "updated_at=excluded.updated_at, sha_norm=excluded.sha_norm",
        rows,
    )
    if indexed:
        keep = {r[0] for r in rows}
        stale = sorted(indexed - keep)
        conn.executemany("DELETE FROM kb_doc_extra WHERE doc_id=?", [(d,) for d in stale])
    conn.commit()
    conn.close()
    return {
        "indexed": len(indexed),
        "written": len(rows),
        "with_source": sum(1 for r in rows if r[1]),
        "with_req": sum(1 for r in rows if json.loads(r[2])),
    }


def report(db: Path) -> dict:
    """出处と要求紐付けの有無を数える（只读）。

    **会社級だけを見る。** 案件級条目は `project_id` が出处そのものであり、
    `source_project` を書く対象ではない（書くと二重管理になる）。
    最初の実装は全件を見ていたため「92 件すべて未記入」と誤って報告していた（2026-11-02 修正）。
    """
    conn = sqlite3.connect(db)
    if not has_table(conn):
        conn.close()
        return {
            "total": 0, "company_total": 0, "company_with_source": 0,
            "company_missing": [], "company_invalid": [],
            "project_total": 0, "with_req": 0,
        }
    rows = list(conn.execute(
        "SELECT x.doc_id, d.scope, x.source_project, x.req_ids "
        "FROM kb_doc_extra x JOIN kb_doc d ON d.doc_id = x.doc_id "
        "ORDER BY d.scope, x.doc_id"
    ))
    conn.close()

    company = [r for r in rows if r[1] == "company"]
    project = [r for r in rows if r[1] != "company"]
    return {
        "total": len(rows),
        "company_total": len(company),
        "company_with_source": sum(1 for r in company if r[2]),
        "company_missing": [r[0] for r in company if not r[2]],
        "company_invalid": [[r[0], r[2]] for r in company if r[2] and not is_legal_source(r[2])],
        "project_total": len(project),
        "with_req": sum(1 for r in rows if r[3] and json.loads(r[3])),
    }


def _self_test() -> int:
    """一時ディレクトリで parse → sync → report を一周させる。"""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "repo"
        (root / "a").mkdir(parents=True)
        (root / "a" / "one.md").write_text(
            "---\ndoc_id: D-ONE\nscope: company\nreq_ids: [X-1]\n"
            "source_project: P-XXX-001\n---\n# t\n",
            encoding="utf-8",
        )
        (root / "a" / "two.md").write_text(
            "---\ndoc_id: D-TWO\nscope: company\n---\n# t\n", encoding="utf-8"
        )
        (root / "a" / "junk.md").write_text("no front matter\n", encoding="utf-8")

        db = Path(tmp) / "kb.sqlite3"
        conn = sqlite3.connect(db)
        conn.execute("CREATE TABLE kb_doc (doc_id TEXT PRIMARY KEY, scope TEXT)")
        conn.executemany("INSERT INTO kb_doc(doc_id, scope) VALUES(?,?)",
                         [("D-ONE", "company"), ("D-TWO", "company")])
        conn.commit()
        conn.close()

        r1 = sync(root, db)
        r2 = sync(root, db)      # 冪等
        rep = report(db)
        ok = (
            r1["written"] == 2
            and r1["with_source"] == 1
            and r1["with_req"] == 1
            and r1 == r2
            and rep["total"] == 2
            and rep["company_total"] == 2
            and rep["company_missing"] == ["D-TWO"]
            and rep["company_invalid"] == []
            and is_legal_source("P-R60-001")
            and is_legal_source("framework-rules")
            and not is_legal_source("R60")
        )
        print(f"[self-test] sync={r1} company={rep['company_total']} "
              f"missing={rep['company_missing']} -> {'PASS' if ok else 'FAIL'}")
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())

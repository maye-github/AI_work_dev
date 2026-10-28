"""`tools.ingest` の自己検証（合成フィクスチャ）。

実在の歴史案件（`D:/AI_work`）には一切触れない。一時ディレクトリに
合成ツリーを作り、遮断・棚卸し・候補生成の各段を検証する。

機密パターンの文字列をこのソースへ直書きしない:
    gate6 は `tools/**/*.py` も走査する。フィクスチャ用の「偽の機密」を
    リテラルで書くと、本ツール自身が gate6 で落ちる。
    そのため実行時に連結して組み立てる（下の `_fake_secret()`）。
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from .id_candidates import approved_rows, propose_candidates
from .inventory import build_inventory, merge_by_pgm, scan_repo_text
from .manifest import load_manifest, validate_manifest
from .scanner import pgm_of, walk_repo
from .secret_gate import blocked_set, collect_secret_evidence, is_blocked

BLOCK_GLOBS = ["**/.env", "**/.env.*", "**/*.pem", "**/*.key", "**/id_rsa*"]


def _fake_secret() -> str:
    """gate6 に検出されるべき「偽の機密」を実行時に組み立てる（直書き回避）。"""
    return "DB_" + "PASSWORD" + " = " + "hunter" + "2xyz"


def _fake_placeholder() -> str:
    """占位なので検出されてはならない文字列。"""
    return "oracle://" + "TBL_1" + ":" + "PWD_1" + "@" + "HOST_1" + "/" + "SID_1"


def _make_fixture(base: Path) -> Path:
    """合成プロジェクトツリーを作る。"""
    api = base / "api"
    (api / "app" / "routers").mkdir(parents=True)
    (api / "fastapi_oracle_pjt").mkdir(parents=True)
    (api / "keys").mkdir(parents=True)

    (api / "app" / "routers" / "R60AreaController.py").write_text(
        "# 合成フィクスチャ\n" + _fake_secret() + "\n" + _fake_placeholder() + "\n",
        encoding="utf-8",
    )
    (api / "app" / "routers" / "R60CodeMesCreate.vue").write_text("<template/>\n", encoding="utf-8")
    (api / "app" / "routers" / "__init__.py").write_text("", encoding="utf-8")

    # 遮断対象（追跡下にある想定）
    (api / "fastapi_oracle_pjt" / ".env").write_text("DUMMY=1\n", encoding="utf-8")
    (api / "keys" / "server.key").write_text("DUMMY\n", encoding="utf-8")
    # 遮断対象（非追跡。追跡状態が不明なときは安全側で遮断されるべき）
    (api / ".env.development").write_text("DUMMY=1\n", encoding="utf-8")

    return api


def self_test(verbose: bool = True) -> tuple[bool, list[str]]:
    """自己検証を実行する。`(ok, 失敗理由のリスト)` を返す。"""
    failures: list[str] = []
    checks: list[str] = []

    def check(label: str, condition: bool) -> None:
        if condition:
            checks.append(label)
        else:
            failures.append(label)

    # --- 1. glob 遮断判定 ---
    check("is_blocked: 深い階層の .env", bool(is_blocked("fastapi_oracle_pjt/.env", BLOCK_GLOBS)))
    check("is_blocked: .env.development", bool(is_blocked("a/b/.env.development", BLOCK_GLOBS)))
    check("is_blocked: 鍵ファイル", bool(is_blocked("keys/server.key", BLOCK_GLOBS)))
    check("is_blocked: 通常ソースは非該当", is_blocked("app/routers/R60AreaController.py", BLOCK_GLOBS) is None)

    with tempfile.TemporaryDirectory(prefix="tcai-ingest-selftest-") as tmp:
        base = Path(tmp)
        api = _make_fixture(base)

        # --- 2. 機密遮断（tracked 注入 = git 無しで検証） ---
        tracked = {
            "app/routers/R60AreaController.py",
            "app/routers/R60CodeMesCreate.vue",
            "fastapi_oracle_pjt/.env",
            "keys/server.key",
        }
        evidence = collect_secret_evidence(api, BLOCK_GLOBS, tracked=tracked)
        blocked = blocked_set(evidence)
        check("遮断: tracking=git", evidence["tracking"] == "git")
        check("遮断: .env が除外された", "fastapi_oracle_pjt/.env" in blocked)
        check("遮断: 鍵が除外された", "keys/server.key" in blocked)
        check("遮断: 通常ソースは除外されない", "app/routers/R60AreaController.py" not in blocked)
        check("遮断: 証跡に値が含まれない", all(set(row) == {"path", "matched_glob", "tracked"} for row in evidence["blocked"]))
        check("遮断: json 直列化可能", isinstance(json.dumps(evidence, ensure_ascii=False), str))

        # --- 3. 追跡状態が不明なら安全側（遮断側に倒す） ---
        unknown = collect_secret_evidence(api, BLOCK_GLOBS, tracked=None)
        # 一時ディレクトリは git 管理外 → tracking は unknown か git のいずれかだが、
        # unknown の場合はディスク上の実ファイルを走査して遮断する。
        check("遮断(追跡不明): .env.development を遮断", ".env.development" in blocked_set(unknown))
        check("遮断(追跡不明): server.key を遮断", "keys/server.key" in blocked_set(unknown))

        # --- 4. 棚卸し（内容を読まない） ---
        entries = walk_repo(api, include_suffixes=(".py", ".vue", ".env", ".key", ".development"), exclude_dirs=("__pycache__",))
        rels = {e.rel for e in entries}
        check("棚卸し: ソースを検出", "app/routers/R60AreaController.py" in rels)
        check("棚卸し: sha1 が埋まる", all(len(e.sha1) == 40 for e in entries if e.rel.endswith(".py")))
        # 空ファイル（__init__.py）は size 0 で正しい。中身のあるソースだけ size>0 を要求する。
        by_rel = {e.rel: e for e in entries}
        check("棚卸し: size が実サイズを反映", by_rel["app/routers/R60AreaController.py"].size > 0)
        check("棚卸し: 空ファイルは size 0", by_rel["app/routers/__init__.py"].size == 0)
        check("棚卸し: 除外ディレクトリが効く", not any("__pycache__" in r for r in rels))

        # --- 5. PGM 名の抽出 ---
        check("PGM: Controller を落とす", pgm_of("app/routers/R60AreaController.py") == "R60Area")
        check("PGM: vue の Create を落とす", pgm_of("x/R60CodeMesCreate.vue") == "R60CodeMes")
        check("PGM: 共通系は除外", pgm_of("x/R60CSVDownloadController.py") is None)
        check("PGM: __init__ は除外", pgm_of("x/__init__.py") is None)

        merged = merge_by_pgm(entries)
        check("PGM 併合: R60Area が居る", "R60Area" in merged)

        # --- 6. 非遮断テキストの機密走査（gate6 と同一規格） ---
        hits = scan_repo_text(api, entries, blocked=blocked, root=base)
        hit_files = {h["file"] for h in hits}
        check("走査: 偽の機密を検出", "app/routers/R60AreaController.py" in hit_files)
        check("走査: 占位は検出しない", all("PWD_1" not in h["match"] for h in hits))
        check("走査: 遮断済み .env は読まない", not any(r.endswith(".env") for r in hit_files))

        # --- 7. 発号候補（全行 approved: false） ---
        candidates = propose_candidates(merged, {"block_width": {"R": 1, "I": 100}})
        all_props = [p for m in candidates["modules"] for p in m["proposals"]]
        check("候補: 生成された", bool(all_props))
        check("候補: 全て approved=false", all(p["approved"] is False for p in all_props))
        check("候補: assigned は null", all(p["assigned"] is None for p in all_props))
        check("候補: 承認行ゼロ", approved_rows(candidates) == [])
        check("候補: _unassigned は module 化しない", all(m["module"] != "_unassigned" for m in candidates["modules"]))

        # --- 8. 棚卸し成果物（内容を含まない） ---
        inv = build_inventory({"project_key": "FIXTURE", "root": str(api), "traversal": {"max_scan_bytes": 1024}}, "api", entries, blocked)
        check("inventory: 内容フィールドを持たない", "content" not in inv and all("content" not in f for f in inv["files"]))
        check("inventory: counts が埋まる", inv["counts"]["files"] == len(entries))

    # --- 9. 実マニフェストの検証 ---
    manifest_path = Path(__file__).resolve().parents[2] / "docs" / "00_registry" / "ingest-manifest.yml"
    if manifest_path.is_file():
        data = load_manifest(manifest_path)
        problems = validate_manifest(data)
        check("マニフェスト: 構造合格", not problems)
        if problems:
            failures.extend(f"マニフェスト: {p}" for p in problems)
    else:
        failures.append("マニフェスト: ファイルが見つからない")

    # --- 10. 検証器そのものが壊れた入力を弾く ---
    broken = {"schema_version": "1", "output_root": "/abs", "secret_block_globs": [], "projects": []}
    check("検証器: 壊れた入力を弾く", len(validate_manifest(broken)) >= 3)
    banned = {"secret_block_globs": ["**/.env"], "output_root": "reports", "projects": [
        {"project_key": "P", "root": "x", "repos": [{"name": "n", "path": "p", "role": "r"}], "module_id": 1}]}
    check("検証器: 禁止鍵を弾く", any("禁止キー" in p for p in validate_manifest(banned)))

    if verbose:
        for line in checks:
            print(f"  PASS  {line}")
        for line in failures:
            print(f"  FAIL  {line}")
        print(f"[tools.ingest] self-test: {len(checks)} passed, {len(failures)} failed")

    return (not failures), failures

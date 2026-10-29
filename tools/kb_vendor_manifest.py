#!/usr/bin/env python
"""kb-platform の上流（`D:\\AI_platform\\kb-platform`）との差分を可視化する。

    py -3 -m tools.kb_vendor_manifest --snapshot   # 上流の指紋を VENDOR_BASE.json に記録
    py -3 -m tools.kb_vendor_manifest --check      # 本抄本が上流からどこでずれたか

なぜ要るか
----------
上流は**ただのフォルダ**であり、git ではない（2026-10-29 実測：`.git` も VERSION も無い）。
新しい版が届いても「何が変わったか」を git が教えてくれないため、
こちらの `kbkit/` にどのファイルを手で当て直せばよいかを、人が目で探すことになる。
そこで上流の全ファイルの SHA-256 を 1 枚の JSON に落とし、
本抄本と突き合わせて「一致 / 本地改変 / 上流に無い」を機械で分ける。

判定の意味
----------
- `一致`       … 上流のまま。次の同期では触らない。
- `本地改変`   … こちらで手を入れた。**同期のたびに手で当て直す必要がある**（`VENDORED.md` の偏离表）。
  この数を減らすのが同期コストを下げる唯一の方法である（上流へ PR を出す）。
- `上流に無い` … こちらの追加物。`repo/company/`・`repo/projects/`・`repo/eval/` は
  **そもそも上流の持ち物ではない**ので、ここに出るのが正常。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCAL = ROOT / "tools" / "kb-platform"
DEFAULT_UPSTREAM = Path(r"D:\AI_platform\kb-platform")
MANIFEST = LOCAL / "VENDOR_BASE.json"

SKIP_DIRS = {"__pycache__", "data", ".git"}
SKIP_SUFFIX = {".pyc", ".pyo"}

# 上流の持ち物ではない区画（こちらの追加）。差分に出ても異常ではない。
OWNED_BY_US = (
    "repo/company/",
    "repo/projects/",
    "repo/eval/",
    "VENDOR_BASE.json",
    "VENDORED.md",
    "company-README.md",
    "projects-README.md",
    "UPSTREAM-SYNC.md",
)

# 上流のコード。ここが「同期のたびに手で当て直す」対象であり、数を減らすべきもの。
CODE_PATHS = ("kbkit/", "run.py", "api.py")


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def scan(base: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not base.is_dir():
        raise SystemExit(f"見つかりません: {base}")
    for p in sorted(base.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(base)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if p.suffix in SKIP_SUFFIX:
            continue
        out[rel.as_posix()] = _sha256(p)
    return out


def cmd_snapshot(args) -> int:
    base = Path(args.upstream)
    snap = scan(base)
    MANIFEST.write_text(
        json.dumps(snap, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"上流 {len(snap)} ファイルの指紋を記録しました: {MANIFEST.relative_to(ROOT).as_posix()}")
    print(f"  上流: {base}")
    return 0


def cmd_check(args) -> int:
    if not MANIFEST.is_file():
        raise SystemExit(f"指紋がありません。先に --snapshot を実行してください: {MANIFEST}")
    snap: dict[str, str] = json.loads(MANIFEST.read_text(encoding="utf-8"))
    now = scan(LOCAL)

    same, patched, missing, added = [], [], [], []
    for rel, digest in snap.items():
        if rel not in now:
            missing.append(rel)
        elif now[rel] == digest:
            same.append(rel)
        else:
            patched.append(rel)
    for rel in now:
        if rel not in snap:
            added.append(rel)

    ours = [r for r in added if r.startswith(OWNED_BY_US)]
    foreign = [r for r in added if not r.startswith(OWNED_BY_US)]
    patched_code = [r for r in patched if r.startswith(CODE_PATHS)]
    patched_data = [r for r in patched if not r.startswith(CODE_PATHS)]

    print(f"上流由来 {len(snap)} 件: 一致={len(same)} "
          f"本地改変={len(patched)}（うちコード {len(patched_code)}） 消失={len(missing)}")
    print(f"本地追加 {len(added)} 件: 我々の区画={len(ours)} 想定外={len(foreign)}")

    if patched_code:
        print("\n本地改変（コード）— 同期のたびに手で当て直す。数を減らすには上流へ PR:")
        for rel in patched_code:
            print(f"  M  {rel}")
    if patched_data:
        print("\n本地改変（データ）— 上流の雛形をこちら向けに書き換えたもの:")
        for rel in patched_data:
            print(f"  m  {rel}")
    if missing:
        print("\n上流にあってこちらに無い（消したか、上流で改名された）:")
        for rel in missing:
            print(f"  -  {rel}")
    if foreign:
        print("\n想定外の追加（上流の持ち物でも我々の区画でもない）:")
        for rel in foreign:
            print(f"  +  {rel}")

    # 上流が更新されたときの検出。--snapshot を取り直す前なら「上流が動いた」ことが分かる。
    if args.upstream and Path(args.upstream).is_dir():
        latest = scan(Path(args.upstream))
        moved = sorted(
            r for r in set(latest) | set(snap)
            if latest.get(r) != snap.get(r)
        )
        if moved:
            print(f"\n上流そのものが前回の記録から {len(moved)} 件動いています:")
            for rel in moved:
                print(f"  ~  {rel}")
        else:
            print("\n上流は前回の記録から動いていません。")

    # 非ゼロは「同期で壊れうる箇所がある」の意味。データ側の書き換えは想定内なので数えない。
    return 1 if (patched_code or missing or foreign) else 0


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    ap = argparse.ArgumentParser(description="上流 kb-platform との差分")
    ap.add_argument("--upstream", default=str(DEFAULT_UPSTREAM))
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--snapshot", action="store_true", help="上流の指紋を記録する")
    g.add_argument("--check", action="store_true", help="本抄本との差分を出す")
    args = ap.parse_args(argv)
    return cmd_snapshot(args) if args.snapshot else cmd_check(args)


if __name__ == "__main__":
    raise SystemExit(main())

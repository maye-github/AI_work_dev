#!/usr/bin/env python3
"""mask_demo - 機密値の双方向マスキング デモ / 実運用ツール。

使い方:
  python -m tools.masking.mask_demo --self-test
  python -m tools.masking.mask_demo --mask   <in> <out>
  python -m tools.masking.mask_demo --unmask <in> <out>

プレースホルダ形式は «KEY»（TBL_1 / COL_1 / PWD_1 / IP_1 / DOM_1 / BUCKET_1 / PROFILE_1 …）。
復元はキー→先頭値の逆引き。マスキングは長い値から順に適用し部分一致事故を防ぐ。

重要: 実在の接続情報・鍵は **このファイルにも example 辞書にも書かない**。
実値は .gitignore 済みの masking_dict.json のみに置く（NFR-2 機密紅線）。
self-test は往復可逆性の証明だけが目的なので、合成ダミー値で十分。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# プレースホルダは ASCII のみ（Windows コンソール cp932 でも安全に印字できること）
PLACEHOLDER_OPEN = "[["
PLACEHOLDER_CLOSE = "]]"


def _reconfigure_stdout() -> None:
    """Windows 既定 cp932 コンソールでも日本語・記号を落とさず出力する。"""
    stream = getattr(sys, "stdout", None)
    if stream is not None and hasattr(stream, "reconfigure"):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):  # pragma: no cover
            pass

DICT_NAME = "masking_dict.json"
EXAMPLE_NAME = "masking_dict.example.json"

# ---------------------------------------------------------------------------
# self-test 用の合成フィクスチャ（実在値ではない。往復可逆性の検証専用）
# ---------------------------------------------------------------------------
_SELF_TEST_DICT = {
    "TBL_1": ["R60_DEMO_M_TBL"],
    "COL_1": ["demo_cmp_cd", "demo_jig_cd", "demo_ara_cd", "demo_ksn_dat"],
    "PWD_1": ["demo_pass_xxxx"],
    # TEST-NET-2（RFC 5737）は文書用に予約されたアドレス。実在の内部セグメントは使わない。
    "IP_1": ["198.51.100.11", "198.51.100.12"],
    "SID_1": ["DEMODB1"],
    "DOM_1": ["demo-tenant.auth0.example"],
    "BUCKET_1": ["demo-bucket-0000"],
    "PROFILE_1": ["demo-profile-0000"],
}

_SELF_TEST_RAW = [
    "oracle+oracledb://demo_user:demo_pass_xxxx@198.51.100.11:1521/DEMODB1",
    "SELECT demo_cmp_cd, demo_jig_cd, demo_ara_cd, demo_ksn_dat FROM R60_DEMO_M_TBL;",
    "bucket=demo-bucket-0000 profile=demo-profile-0000 domain=demo-tenant.auth0.example",
]


# --------------------------------------------------------------------------
# コア
# --------------------------------------------------------------------------

def load_dict(path: Path) -> dict[str, list[str]]:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path} は key -> [value] のオブジェクトである必要があります")
    out: dict[str, list[str]] = {}
    for key, values in data.items():
        if isinstance(values, str):
            values = [values]
        if not isinstance(values, list):
            raise ValueError(f"{path}: {key} の値は文字列配列で指定してください")
        out[str(key)] = [str(v) for v in values]
    return out


def build_placeholder_map(mapping: dict[str, list[str]]) -> dict[str, str]:
    """実値 -> プレースホルダ の対応表を作る。

    1 つの key が複数の実値を持つ場合（例: COL_1 = 複数列名）は、復元が一意に
    定まるよう `[[COL_1_1]]` `[[COL_1_2]]` … と添字を付ける。可逆性の担保。
    単一値の key は `[[PWD_1]]` のように添字なし。
    """
    out: dict[str, str] = {}
    for key, values in mapping.items():
        cleaned = [str(v) for v in values if str(v)]
        if not cleaned:
            continue
        if len(cleaned) == 1:
            out[cleaned[0]] = f"{PLACEHOLDER_OPEN}{key}{PLACEHOLDER_CLOSE}"
        else:
            for idx, value in enumerate(cleaned, 1):
                out[value] = f"{PLACEHOLDER_OPEN}{key}_{idx}{PLACEHOLDER_CLOSE}"
    return out


def _ordered_values(placeholder_map: dict[str, str]) -> list[str]:
    # 長い実値を先に置換（短い値が長い値の一部を壊すのを防ぐ）
    return sorted(placeholder_map, key=lambda v: (-len(v), v))


def mask_text(text: str, mapping: dict[str, list[str]]) -> tuple[str, int]:
    hits = 0
    placeholder_map = build_placeholder_map(mapping)
    for value in _ordered_values(placeholder_map):
        n = text.count(value)
        if n:
            text = text.replace(value, placeholder_map[value])
            hits += n
    return text, hits


def unmask_text(text: str, mapping: dict[str, list[str]]) -> str:
    placeholder_map = build_placeholder_map(mapping)
    # 添字付きが先（[[COL_1_1]] が [[COL_1]] に食われないよう長い順）
    for placeholder in sorted(placeholder_map.values(), key=lambda p: (-len(p), p)):
        value = next(v for v, p in placeholder_map.items() if p == placeholder)
        text = text.replace(placeholder, value)
    return text


def roundtrip(text: str, mapping: dict[str, list[str]]) -> tuple[str, str, int]:
    masked, hits = mask_text(text, mapping)
    return masked, unmask_text(masked, mapping), hits


# --------------------------------------------------------------------------
# サブコマンド
# --------------------------------------------------------------------------

def _resolve_dict(root: Path, explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    real = root / "tools" / "masking" / DICT_NAME
    if real.is_file():
        return real
    return root / "tools" / "masking" / EXAMPLE_NAME


def do_self_test(root: Path) -> int:
    print("[mask_demo] self-test start (合成フィクスチャ使用 / 実値は含まない)")
    total_hits = 0
    ok = True
    for raw in _SELF_TEST_RAW:
        masked, restored, hits = roundtrip(raw, _SELF_TEST_DICT)
        total_hits += hits
        reversible = restored == raw
        ok = ok and reversible
        print(f"  RAW     : {raw}")
        print(f"  MASKED  : {masked}")
        print(f"  RESTORED: {restored}  reversible={reversible}")

    joined = "\n".join(mask_text(r, _SELF_TEST_DICT)[0] for r in _SELF_TEST_RAW)
    has_placeholder = any(
        f"{PLACEHOLDER_OPEN}{k}{PLACEHOLDER_CLOSE}" in joined for k in _SELF_TEST_DICT
    ) and any(tag in joined for tag in ("TBL_", "COL_", "PWD_"))

    good = bool(ok and has_placeholder)
    print(f"[mask_demo] mask_hits={total_hits} unmask_ok={str(good).lower()} exit={0 if good else 1}")
    return 0 if good else 1


def do_convert(root: Path, mode: str, src: str, dst: str, dict_path: str | None) -> int:
    mapping = load_dict(_resolve_dict(root, dict_path))
    text = Path(src).read_text(encoding="utf-8")
    if mode == "mask":
        out, hits = mask_text(text, mapping)
        print(f"[mask_demo] mask_hits={hits}")
    else:
        out = unmask_text(text, mapping)
        print("[mask_demo] unmask done")
    Path(dst).write_text(out, encoding="utf-8")
    print(f"[mask_demo] {mode} {src} -> {dst}")
    return 0


def main(argv: list[str] | None = None) -> int:
    _reconfigure_stdout()
    ap = argparse.ArgumentParser(prog="mask_demo", description="機密値 双方向脱敏")
    ap.add_argument("--self-test", action="store_true", help="内蔵フィクスチャで往復検証")
    ap.add_argument("--mask", nargs=2, metavar=("IN", "OUT"))
    ap.add_argument("--unmask", nargs=2, metavar=("IN", "OUT"))
    ap.add_argument("--dict", help="使用する辞書ファイル（既定: masking_dict.json → example へフォールバック）")
    ap.add_argument("--root")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[2]

    if args.self_test:
        return do_self_test(root)
    if args.mask:
        return do_convert(root, "mask", args.mask[0], args.mask[1], args.dict)
    if args.unmask:
        return do_convert(root, "unmask", args.unmask[0], args.unmask[1], args.dict)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())

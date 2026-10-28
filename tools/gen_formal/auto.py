#!/usr/bin/env python3
"""auto — 節点成果物の設計書 md が更新されていたら xlsx を描き直す。

何をするか:
  `tutorial/<case>/<節点>/` 配下の「基本設計書」「詳細設計書」md を走査し、
  **出力 xlsx より新しいものだけ**を `tools/gen_formal/book` で描き直す。
  体裁（画面編 / 詳細設計）は節題から自動判定する。
  更新が無ければ何もせずに即終了する（stat 2 回だけ）。

誰が呼ぶか:
  `.claude/settings.json` の **Stop フック**。1 ターン終了ごとに走る。
  → 「機読源を直したのに Excel が古い」状態を残さない（ユーザー指示 2026-10-22）。

やらないこと:
  - `docs/**` へは書かない（CP-R-3: `docs/**/*.xlsx == 0` は不変。`book._inside_docs` で拒否）。
  - 生成物を手で編集しない前提。直すのは md（規則 00 §11）。
  - 失敗してもターンを止めない（常に exit 0。エラーは stderr に出す）。

出力先:
  reports/_auto/<case>/<節点>/<stem>_预览版.xlsx
  （名前に「预览版」を入れるのは、目視用の下書きだと一目で分かるようにするため。
    顧客へ出す正式版は節点8 で `_正式版` を付けて別に出す）

使い方:
  py -3 -X utf8 tools/gen_formal/auto.py            # 更新分だけ描く（フックと同じ）
  py -3 -X utf8 tools/gen_formal/auto.py --force    # 時刻に関係なく全部描き直す
  py -3 -X utf8 tools/gen_formal/auto.py --dry-run  # 対象を表示するだけ
"""

from __future__ import annotations

import sys
from pathlib import Path

# 直接実行（py -3 tools/gen_formal/auto.py）でも動くようにする。
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.gen_formal.book import build, _inside_docs, _normalize_zip
    from tools.gen_formal.md_book import parse
else:
    from .book import build, _inside_docs, _normalize_zip
    from .md_book import parse

ROOT = Path(__file__).resolve().parents[2]
TUTORIAL = ROOT / "tutorial"
OUT_ROOT = ROOT / "reports" / "_auto"

# 設計書の機読源だけを対象にする（確認票・レビュー記録は描かない）。
# 体裁は `book.detect_profile()` が節題から判定する（画面編 / 詳細設計）。
NAME_HINTS = ("基本设计书", "基本設計書", "详细设计书", "詳細設計書")


def _order(md: Path) -> tuple[int, str]:
    """`05_承認版_…` の先頭番号を優先度にする（無ければ 0）。"""
    head = md.stem.split("_", 1)[0]
    return (int(head) if head.isdigit() else 0, md.stem)


def candidates() -> list[Path]:
    """各節点ディレクトリで**最も新しい番号の**基本設計書 md を返す。

    01/04 のような旧稿は履歴であり、毎ターン描き直す対象ではない。
    旧稿を見たいときは `--force` で全部描ける。
    """
    if not TUTORIAL.is_dir():
        return []
    groups: dict[Path, list[Path]] = {}
    for md in sorted(TUTORIAL.glob("*/*/*.md")):
        if any(part.startswith("_archive") for part in md.relative_to(TUTORIAL).parts):
            continue
        if md.name.endswith(".zh.md"):
            continue
        if not any(hint in md.stem for hint in NAME_HINTS):
            continue
        groups.setdefault(md.parent, []).append(md)
    return [max(mds, key=_order) for _, mds in sorted(groups.items())]


def out_for(md: Path) -> Path:
    """`05_承認版_基本设计书.md` → `…/05_承認版_基本设计书_预览版.xlsx`。

    名前で「これは下書き・目視用」と分かるようにする。顧客へ出す正式版は節点8 で
    `_正式版` を付けて別途出す（同じディレクトリに置かない）。
    """
    rel = md.relative_to(TUTORIAL).with_suffix("")
    return OUT_ROOT / rel.parent / (rel.name + "_预览版.xlsx")


def main(argv: list[str]) -> int:
    force = "--force" in argv
    dry = "--dry-run" in argv

    targets = candidates()
    if not targets:
        return 0

    generated = 0
    for md in targets:
        out = out_for(md)
        if not force and out.exists() and out.stat().st_mtime >= md.stat().st_mtime:
            continue
        if dry:
            print("[gen_formal.auto] 対象: %s -> %s"
                  % (md.relative_to(ROOT).as_posix(), out.relative_to(ROOT).as_posix()))
            continue
        if _inside_docs(out):
            print("[gen_formal.auto] docs/ へは書きません: %s" % out, file=sys.stderr)
            continue
        try:
            doc = parse(str(md))
            if not doc.sections:
                print("[gen_formal.auto] 節が無いので飛ばします: %s" % md, file=sys.stderr)
                continue
            wb = build(doc)
            out.parent.mkdir(parents=True, exist_ok=True)
            wb.save(out)
            _normalize_zip(out)
            print("[gen_formal.auto] 更新: %s（%d シート）"
                  % (out.relative_to(ROOT).as_posix(), len(wb.sheetnames)))
            generated += 1
        except Exception as exc:  # フックを止めない。原因は stderr に残す。
            print("[gen_formal.auto] 失敗 %s: %s" % (md, exc), file=sys.stderr)

    if not dry and generated == 0:
        print("[gen_formal.auto] 更新なし")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

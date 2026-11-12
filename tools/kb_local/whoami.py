"""端末ごとの「操作者名」を 1 箇所で扱う。

なぜ要るか
----------
読権限は `--as <人>` で明示する建前だが、毎回書くのは現実的でない。
**端末ごとに 1 回だけ設定**しておき、`--as` が省略されたときの既定として使う。

★ 既定は「誰でも見える」ではない。`whoami` が**未設定なら会社級だけ**（従来どおり）。
  設定は人が明示的に行う操作であり、これで制限が緩むわけではない。

保存先は `tools/kb_local/whoami.txt`（gitignore 済・1 行）。
"""

from __future__ import annotations

from pathlib import Path

REL = Path("tools") / "kb_local" / "whoami.txt"


def path(root: Path) -> Path:
    return root / REL


def get(root: Path) -> str | None:
    """設定済みの操作者名。未設定・空なら `None`。"""
    p = path(root)
    try:
        name = p.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return name or None


def set_(root: Path, name: str) -> Path:
    """保存して、保存先を返す。空文字は受け付けない（呼び出し側で弾く）。"""
    p = path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(name.strip() + "\n", encoding="utf-8")
    return p

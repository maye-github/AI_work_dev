#!/usr/bin/env python3
"""`python tools/trace_check.py` から実行するための薄いランチャー。

実体は `tools/trace_check/__init__.py`（パッケージ）。`python -m tools.trace_check`
と完全に同一の動作になるよう、リポジトリルートを sys.path に載せて委譲する。
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.trace_check import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())

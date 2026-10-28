"""trans-cosmos-ai AI 全流程骨架 - 歴史案件 取入パッケージ（tools.ingest）。

役割:
    既存の対日開発プロジェクト（歴史案件）から、設計資産・規約・用語を
    **読み取り専用**で取り込み、後段の人ゲートが判断できる材料を機器生成する。

処理の流れ:
    manifest.py   … 取入マニフェスト（docs/00_registry/ingest-manifest.yml）を検証
      ↓
    scanner.py    … ファイルを棚卸しする（**棚卸しでは内容を読まない**）
      ↓
    secret_gate.py… git 追跡下の .env / 鍵を **入力から除外** し証跡を残す
      ↓
    inventory.py  … 非遮断テキストを PGM 名で業務モジュールへ併合
      ↓
    id_candidates.py … 発号**候補**を生成する（全行 approved: false）

責任境界（红线①③の機械化）:
    本パッケージは ``docs/00_registry/ids.yml`` を **自動で書かない**。
    書き込めるのは ``id-apply`` サブコマンドのみであり、
    かつ人が ``approved: true`` と記入した行だけを書く。

機密の扱い:
    遮断した路径は記録するが、**値は決して読まない・書かない**。
    非遮断テキストの走査は ``tools.trace_check.scan_text`` を import して行う
    （規格を二重実装しない。過去に「除外区画を作った側から漏れた」事故があるため）。

依存: 標準ライブラリ + pyyaml のみ（NFR-6 外部サービス非依存）。
"""

from pathlib import Path

__all__ = [
    "PROJECT_ROOT_MARKER",
    "find_root",
    "load_manifest",
    "validate_manifest",
    "walk_repo",
    "is_blocked",
    "git_tracked",
    "collect_secret_evidence",
    "merge_by_pgm",
    "build_inventory",
    "propose_candidates",
    "self_test",
]

# リポジトリルートの標識と上方探索は tools/paths.py が唯一の実装である
# （かつて trace_check / gen_formal / ingest が同じ関数を 3 つ持っていた）。
# 既存の呼出側（__main__.py）が `from . import find_root` を使うため、公開名として再輸出する。
from ..paths import ROOT_MARKER as PROJECT_ROOT_MARKER, find_root  # noqa: E402, F401


from .inventory import build_inventory, merge_by_pgm  # noqa: E402
from .id_candidates import propose_candidates  # noqa: E402
from .manifest import load_manifest, validate_manifest  # noqa: E402
from .scanner import walk_repo  # noqa: E402
from .secret_gate import collect_secret_evidence, git_tracked, is_blocked  # noqa: E402
from .selftest import self_test  # noqa: E402

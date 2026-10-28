"""trans-cosmos-ai AI 全流程骨架 - tools パッケージ。

門番・変換:
  `python -m tools.trace_check`（6 重門番） / `python -m tools.gen_formal.gen_excel` /
  `python -m tools.masking.mask_demo` / `python -m tools.gen_view`

台帳・影響面（2026-10-13 追加。**人が実行する CLI**。エージェントの能力ではない）:
  `python -m tools.registry`（`ids.yml` の唯一の書込み口。`--apply` なしでは書かない） /
  `python -m tools.impact`（変更影響面。読むだけで何も書かない）

歴史資産の取入:
  `python -m tools.ingest`

すべて標準ライブラリ + pyyaml のみに依存（NFR-6 外部サービス非依存）。
"""

"""masking - 双方向脱敏ツール（マスキング / アンマスキング）。

NFR-2「機密紅線不越界」の実行主体。外部 LLM に投げる前に必ずここを通す。
辞書 `masking_dict.json` は .gitignore 済み（実値は絶対にコミットしない）。

API は `tools.masking.mask_demo` から直接 import する
（`python -m tools.masking.mask_demo` を壊さないため、ここでは再エクスポートしない）。
"""

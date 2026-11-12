"""constraints.yaml の単一引用符スカラに残った二重バックスラッシュを 1 本へ直す。

YAML の単一引用符はバックスラッシュを解釈しない。つまり ':\\w+' は
「コロン + バックスラッシュ + w+」という正規表現になり、`:name` に決して一致しない。
結果、require_regex の検査は**恒に失敗**し、forbid_regex の検査は**恒に通過**していた
（＝ no_fstring_sql / no_physical_delete / no_unmasked_secret は死んでいた）。
"""
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

P = "tools/kb-platform/constraints.yaml"
DOUBLE = "\\" + "\\"
SINGLE = "\\"

lines = open(P, encoding="utf-8").read().split("\n")
n = 0
for i, ln in enumerate(lines):
    is_single_pat = "pattern: '" in ln
    is_single_item = bool(re.match(r"^\s+- '.*'$", ln))
    if (is_single_pat or is_single_item) and DOUBLE in ln:
        lines[i] = ln.replace(DOUBLE, SINGLE)
        n += 1
open(P, "w", encoding="utf-8").write("\n".join(lines))
print("修正行数:", n)

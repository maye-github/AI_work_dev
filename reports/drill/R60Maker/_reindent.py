"""try { ... } finally { ... } の内側を 2 スペース深くする（整形のみ・意味は変えない）。"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

P = "tutorial/R60Maker/节点5_制造/frontend/views/MakerEditScreen.vue"
lines = open(P, encoding="utf-8").read().split("\n")
out, depth, inside = [], 0, False
for ln in lines:
    if ln.strip() == "try {" and not inside:
        inside = True
        out.append(ln)
        continue
    if inside and ln.strip() == "} finally {":
        inside = False
        out.append(ln)
        continue
    if inside and ln.strip():
        out.append("  " + ln)
    else:
        out.append(ln)
open(P, "w", encoding="utf-8").write("\n".join(out))
print("整形した")

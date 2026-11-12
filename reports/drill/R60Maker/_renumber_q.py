"""R60Maker の Q 番号も全局序列の続きへ振り直す（2026-11-10）。

R60Login の Q は Q-201〜Q-238。R60Maker は Q-201 から数え直しており、
Q-201〜Q-238 の 38 件が「同じ番号で別の問い」になっていた
（実測: R60Maker Q-201＝前提条件の内容／R60Login Q-201＝暗号化算式の境界規則）。
R60Maker の Q-201〜Q-297 を Q-239〜Q-335 へ +38 する。
"""
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

RX = re.compile(r'(?<![0-9A-Za-z-])Q-(\d{3})(b?)(?![0-9])')


def shift(m):
    n = int(m.group(1))
    if 201 <= n <= 297:
        return 'Q-%03d%s' % (n + 38, m.group(2))
    return m.group(0)


ROOTS = ['tutorial/R60Maker', 'docs/00_plan/coach/R60Maker', 'reports/drill/R60Maker']
SKIP_PATH = {
    'reports/drill/R60Maker/incoming',
    'tutorial/R60Maker/节点6_单元测试/02_审查结果.md',
}
EXTS = ('.md', '.yaml', '.yml', '.py', '.ts', '.vue', '.js', '.html')

changed = []
for root in ROOTS:
    for dirpath, _, files in os.walk(root):
        d = os.path.join(dirpath).replace(os.sep, '/')
        if any(d.startswith(s) for s in SKIP_PATH):
            continue
        for f in files:
            p = os.path.join(dirpath, f).replace(os.sep, '/')
            if p in SKIP_PATH or not p.endswith(EXTS) or f.startswith('_'):
                continue
            raw = open(p, 'rb').read()
            try:
                t = raw.decode('utf-8')
            except UnicodeDecodeError:
                continue
            new = RX.sub(shift, t)
            if new != t:
                n = sum(1 for m in RX.finditer(t) if 201 <= int(m.group(1)) <= 297)
                open(p, 'wb').write(new.encode('utf-8'))
                changed.append((p, n))

print('書き換えたファイル: %d / 置換総数: %d' % (len(changed), sum(n for _, n in changed)))
for p, n in sorted(changed, key=lambda x: -x[1])[:15]:
    print('  %-70s %d' % (p, n))

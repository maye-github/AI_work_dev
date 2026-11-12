"""R60Maker の ID を全局序列の続きへ振り直す（2026-11-10）。

根拠: R60Maker は Q と TC を「全局最大号 +1」から続けた（Q-268、TC-222）のに、
      R/F/D/L/E/I だけ 201 から数え直した。そのため R60Login の登録条目と
      同じ番号に別の意味が載った（E-201 = ログインの「社員なし」／
      メーカーの「0 件」）。振り直しは「続きから数える」に統一する。

触らない:
  reports/drill/R60Maker/incoming/**  受領資料（顧客文書・凍結入力）
  tutorial/R60Maker/节点6_单元测试/02_审查结果.md  ← 借用を説明する文が入っており、
    ここを機械置換すると説明そのものが壊れる。別途手で直す。
"""
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

MAP = {}
MAP['R-201'] = 'R-202'
MAP['F-201'] = 'F-202'
for i in range(1, 7):      # D-201..D-206
    MAP['D-%03d' % (200 + i)] = 'D-%03d' % (206 + i)
for i in range(1, 12):     # L-201..L-211
    MAP['L-%03d' % (200 + i)] = 'L-%03d' % (211 + i)
for i in range(1, 13):     # E-201..E-212
    MAP['E-%03d' % (200 + i)] = 'E-%03d' % (212 + i)
for i in range(1, 34):     # I-01..I-33 → I-322..I-354
    MAP['I-%02d' % i] = 'I-%03d' % (321 + i)

KEYS = sorted(MAP, key=len, reverse=True)
RX = re.compile(r'(?<![0-9A-Za-z-])(' + '|'.join(re.escape(k) for k in KEYS) + r')(?![0-9])')

ROOTS = ['tutorial/R60Maker', 'docs/00_plan/coach/R60Maker', 'reports/drill/R60Maker']
SKIP_PATH = {
    'reports/drill/R60Maker/incoming',
    'tutorial/R60Maker/节点6_单元测试/02_审查结果.md',
}
EXTS = ('.md', '.yaml', '.yml', '.py', '.ts', '.vue', '.js', '.html')

changed = []
for root in ROOTS:
    for dirpath, dirnames, files in os.walk(root):
        p_dir = os.path.join(dirpath).replace(os.sep, '/')
        if any(p_dir.startswith(s) for s in SKIP_PATH):
            continue
        for f in files:
            p = os.path.join(dirpath, f).replace(os.sep, '/')
            if p in SKIP_PATH or not p.endswith(EXTS):
                continue
            if f.startswith('_'):
                continue
            raw = open(p, 'rb').read()
            try:
                t = raw.decode('utf-8')
            except UnicodeDecodeError:
                continue
            # 二段置換（連鎖を防ぐ）
            tmp = RX.sub(lambda m: '\x00' + MAP[m.group(1)] + '\x00', t)
            new = tmp.replace('\x00', '')
            if new != t:
                n = len(RX.findall(t))
                open(p, 'wb').write(new.encode('utf-8'))
                changed.append((p, n))

print('書き換えたファイル: %d' % len(changed))
for p, n in sorted(changed, key=lambda x: -x[1]):
    print('  %-72s %d 箇所' % (p, n))
print('\n置換総数: %d' % sum(n for _, n in changed))

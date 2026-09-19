import re

h = open('article.html', encoding='utf-8').read()
print('len', len(h))
print('mp.weixin count', h.count('mp.weixin.qq.com/s/'))
print('portal-title', h.count('portal-title'))
print('传送门 occurrences', h.count('传送门'))
for m in re.finditer('传送门', h):
    print('  at', m.start(), repr(h[max(0, m.start() - 80):m.start() + 80]))
print('__CODE__ leftover', h.count('__CODE__'))
print('img', len(re.findall(r'<img', h)))
print('pre', len(re.findall(r'<pre', h)))
print('table', len(re.findall(r'preview-table', h)))
print('strong', len(re.findall(r'<strong', h)))
print('h2', len(re.findall(r'<h2', h)), 'h3', len(re.findall(r'<h3', h)))

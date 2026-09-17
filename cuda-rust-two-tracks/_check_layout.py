import re, io, html
ART = 'D:/06_Hermes/articles/cuda-rust-two-tracks'
h = io.open(ART + '/article.html', encoding='utf-8').read()
print('h2 titles:', re.findall(r'<h2[^>]*>(.*?)</h2>', h))
print('stray **:', h.count('**'))
print('bullet spans:', h.count('font-size:7px'))
print('quote cards:', h.count('background:#f5f8fb'))
print('fig01 pos:', h.find('fig01.png'), '/', len(h))
# 顺序检查：正文块顺序
seq = []
for m in re.finditer(r'<h2[^>]*>(.*?)</h2>|<img[^>]+src="(fig\d+\.png)"|<figcaption', h):
    if m.group(1):
        seq.append('H2:' + m.group(1))
    elif m.group(2):
        seq.append('FIG:' + m.group(2))
print('order:', seq)
# 图片前后文字
i = h.find('<figure')
print('--- around figure ---')
print(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '|', h[i-700:i+250])))

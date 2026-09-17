import re, io
t = io.open('D:/06_Hermes/articles/cuda-rust-two-tracks/article.html', encoding='utf-8').read()
for pat in ['portal-links', 'mp.weixin.qq.com', '【传送门】', '结语</strong>', '参考：']:
    print(pat, '->', [m.start() for m in re.finditer(re.escape(pat), t)])
i = t.find('<div style="background:#f5f0eb')
print('--- jieyu..end ---')
print(t[i:i + 2600])

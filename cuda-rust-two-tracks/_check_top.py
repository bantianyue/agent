import re, io, html
ART = 'D:/06_Hermes/articles/cuda-rust-two-tracks'
h = io.open(ART + '/article.html', encoding='utf-8').read()
body = h[h.find('background:#e8f4fd'):h.find('<h2')]
txt = re.sub(r'<br\s*/?>', '\n', body)
txt = re.sub(r'<[^>]+>', '', txt)
txt = html.unescape(txt).replace('\u00a0', ' ')
print(re.sub(r'\n{3,}', '\n\n', txt).strip())

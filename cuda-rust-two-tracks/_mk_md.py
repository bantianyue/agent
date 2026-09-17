import re, io, os

ART = 'D:/06_Hermes/articles/cuda-rust-two-tracks'
html = io.open(os.path.join(ART, 'article.html'), encoding='utf-8').read()
text = re.sub(r'<[^>]+>', '', html)
text = re.sub(r'\n{3,}', '\n\n', text).strip()
io.open(os.path.join(ART, 'article.md'), 'w', encoding='utf-8').write(text)
io.open(os.path.join(ART, 'article_human.md'), 'w', encoding='utf-8').write(text)
print('article.md / article_human.md written, chars =', len(text))

dashes = re.findall(r'——|—', text)
print('dash count:', len(dashes))
for w in ['标志着', '见证了', '至关重要', '此外', '值得注意的是', '非常', '极其', '相当', '本文', '这篇', '本博客', '原文', '翻译', '全中文', '原文配图']:
    n = text.count(w)
    if n:
        print('  AI/redline word:', w, n)
print('cjk:', len(re.findall(r'[\u4e00-\u9fa5]', text)), 'latin:', len(re.findall(r'[A-Za-z]', text)))

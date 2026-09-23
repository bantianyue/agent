import re, json, html
raw = open('D:/06_Hermes/articles/_src_raw.html', encoding='utf-8').read()
m = re.search(r'<title>(.*?)</title>', raw, re.S)
print('TITLE:', m.group(1) if m else None)
for tag in ['h1', 'h2', 'h3', 'p', 'pre', 'img', 'figure', 'figcaption', 'li', 'table']:
    print(tag, len(re.findall(r'<' + tag + r'[\s>]', raw)))
# article body container guess
for pat in [r'<article[^>]*>', r'class="[^"]*blog-post[^"]*"', r'class="[^"]*entry-content[^"]*"']:
    print(pat, len(re.findall(pat, raw)))

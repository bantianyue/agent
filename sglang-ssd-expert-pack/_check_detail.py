import re

h = open('article.html', encoding='utf-8').read()

# code block integrity
i = h.find('--load-format')
print('--- code sample ---')
print(repr(h[i - 60:i + 200]))

i2 = h.find('expert_offset')
print('--- expert_offset code ---')
print(repr(h[i2 - 40:i2 + 220]))

# figure / caption pairing order
print('--- figure order ---')
for m in re.finditer(r'<img[^>]*src="([^"]+)"[^>]*>(?:<figcaption[^>]*>(.*?)</figcaption>)?', h):
    print(m.group(1), '|', (m.group(2) or '')[:60])

# h2/h3 order
print('--- headings ---')
for m in re.finditer(r'<(h2|h3)[^>]*>(.*?)</\1>', h, re.S):
    t = re.sub(r'<[^>]+>', '', m.group(2)).strip()
    print(m.group(1), t[:60])

# conclusion & ref order
print('--- tail order ---')
print('conclusion idx', h.find('#f5f0eb'), 'portal idx', h.find('portal-title', 1000), 'ref idx', h.find('参考：'))

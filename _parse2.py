import re, json, os, io, sys
d = 'D:/06_Hermes/articles/vllm-hardware-agnostic-models'
raw = open('D:/06_Hermes/articles/_src_raw.html', encoding='utf-8').read()
imgs = re.findall(r'<img[^>]*>', raw)
out = []
for i in imgs:
    src = re.search(r'src=["\']([^"\']+)', i)
    alt = re.search(r'alt=["\']([^"\']*)', i)
    out.append((src.group(1) if src else '', alt.group(1) if alt else ''))
with io.open('D:/06_Hermes/articles/_imgs_raw.txt', 'w', encoding='utf-8') as f:
    for s, a in out:
        f.write(s + '  ||  ALT=' + a + '\n')
print('done', len(out))

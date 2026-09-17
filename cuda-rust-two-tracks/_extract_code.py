import re, io, html, json

h = io.open('D:/06_Hermes/articles/cuda-rust-two-tracks/_page.html', encoding='utf-8').read()

# 只取正文 article 容器（至 About the Authors / Related Resources 之前）
m = re.search(r'<div[^>]*class="[^"]*entry-content[^"]*"[^>]*>', h)
start = m.start() if m else 0
end = h.find('About the Author', start)
body = h[start:end if end > 0 else len(h)]

pres = re.findall(r'<pre[^>]*>(.*?)</pre>', body, re.S)
lines = ['found pre blocks: %d' % len(pres)]
out = []
for i, raw in enumerate(pres):
    t = re.sub(r'<br\s*/?>', '\n', raw)
    t = re.sub(r'</?span[^>]*>', '', t)
    t = re.sub(r'<[^>]+>', '', t)
    t = html.unescape(t)
    t = t.replace('\r\n', '\n').strip('\n')
    lines.append('=' * 30 + ' BLOCK %d ' % (i + 1) + '=' * 30)
    lines.append(t)
    out.append(t)

lines.append('KINDS: ' + repr(re.findall(r'<pre[^>]*class="([^"]*)"', body)))
io.open('D:/06_Hermes/articles/cuda-rust-two-tracks/_code_dump.txt', 'w', encoding='utf-8').write('\n'.join(lines))
print('written', len(out))

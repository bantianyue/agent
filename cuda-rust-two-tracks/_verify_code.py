import re, io, html, json

ART = 'D:/06_Hermes/articles/cuda-rust-two-tracks'
h = io.open(ART + '/article.html', encoding='utf-8').read()
print('<pre count:', h.count('<pre'))
pres = re.findall(r'<pre[^>]*><code>(.*?)</code></pre>', h, re.S)
print('code blocks found:', len(pres))

d = json.load(open(ART + '/article_data.json', encoding='utf-8'))
srcs = []
for sec in d['sections']:
    for p in sec['paras']:
        if p.startswith('__CODE__'):
            raw = p[len('__CODE__'):]
            if '::' in raw[:25]:
                lang, _, code = raw.partition('::')
            else:
                code = raw
            srcs.append(code)
print('source code blocks:', len(srcs))

dumps = json.load(open(ART + '/_code_dump.json', encoding='utf-8')) if False else None

def norm(t):
    t = t.replace('&nbsp;', ' ')
    t = t.replace('<br/>', '\n').replace('<br />', '\n').replace('<br>', '\n')
    t = re.sub(r'<[^>]+>', '', t)
    t = html.unescape(t)
    t = t.replace('\u00a0', ' ')
    return t

ok = True
for i, (rendered, src) in enumerate(zip(pres, srcs)):
    a = norm(rendered).rstrip('\n')
    b = src.rstrip('\n')
    if a != b:
        ok = False
        print('=== MISMATCH block', i + 1, '===')
        al, bl = a.split('\n'), b.split('\n')
        for j in range(max(len(al), len(bl))):
            x = al[j] if j < len(al) else '<missing>'
            y = bl[j] if j < len(bl) else '<missing>'
            if x != y:
                print('  line', j + 1)
                print('   html:', repr(x))
                print('   src :', repr(y))
print('ALL CODE BLOCKS IDENTICAL' if ok else 'CODE MISMATCH FOUND')

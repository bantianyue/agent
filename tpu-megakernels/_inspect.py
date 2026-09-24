import re, sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
h = open('_raw.html', encoding='utf-8', errors='replace').read()
figs = list(re.finditer(r'<figure.*?</figure>', h, re.S))
print('figures:', len(figs))
for i, m in enumerate(figs):
    s = m.group(0)
    svg = re.search(r'<svg[^>]*aria-label="(.*?)"', s, re.S)
    cap = re.findall(r'<figcaption.*?</figcaption>', s, re.S)
    print('--- FIG', i, 'len', len(s))
    print('  aria:', (svg.group(1)[:600] if svg else None))
    print('  captions:', len(cap))
    for c in cap:
        print('   CAP:', re.sub(r'<[^>]+>', '', c).strip()[:800])

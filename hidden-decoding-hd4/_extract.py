import re, json, os

HERE = "D:/06_Hermes/articles/hidden-decoding-hd4"
html = open(os.path.join(HERE, 'source.html'), encoding='utf-8').read()

def clean(t):
    t = re.sub(r'<[^>]+>', ' ', t)
    for a,b in [('&amp;','&'),('&lt;','<'),('&gt;','>'),('&quot;','"'),("&apos;","'"),('&#39;',"'"),('&nbsp;',' ')]:
        t = t.replace(a,b)
    t = re.sub(r'&#x[0-9a-fA-F]+;', '', t)
    return re.sub(r'\s+', ' ', t).strip()

# locate content region
s1 = html.find('<section id="S1"')
bib = html.find('ltx_bibliography')
region = html[s1:bib if bib>0 else len(html)]

lines = []
for m in re.finditer(r'<(h[1-4]|p)[^>]*class="[^"]*?(ltx_p|ltx_title)[^"]*"[^>]*>(.*?)</\1>', region, re.S):
    tag, content = m.group(1), m.group(3)
    txt = clean(content)
    if not txt:
        continue
    lines.append(('## ' if tag.startswith('h') else '') + txt)

open(os.path.join(HERE, 'full_text.txt'), 'w', encoding='utf-8').write('\n\n'.join(lines))
print("text blocks:", len(lines))

# figures - scan whole html for <figure> with <img>
figs = []
for m in re.finditer(r'<figure\b.*?</figure>', html, re.S):
    seg = m.group(0)
    fid = re.search(r'\bid="([^"]+)"', seg)
    imgs = re.findall(r'<img[^>]*src="([^"]+)"', seg)
    if not imgs:
        continue
    cap = re.search(r'<figcaption.*?>(.*?)</figcaption>', seg, re.S)
    captxt = clean(cap.group(1)) if cap else ''
    # full url
    src0 = imgs[0]
    if src0.startswith('http'):
        url = src0
    else:
        url = "https://arxiv.org/html/" + src0.lstrip('/')
    figs.append({
        'type': 'figure',
        'id': fid.group(1) if fid else 'fig%d' % len(figs),
        'img': url,
        'caption': captxt,
        'after_para': 0,
        'hero': False
    })

# mark hero: first figure = S1.F1 typically
for i, f in enumerate(figs):
    if i == 0:
        f['hero'] = True

print("figures found:", len(figs))
for f in figs:
    print(" ", f['id'], '|', f['img'][:80], '| hero=', f['hero'])
    print("    cap:", f['caption'][:80])

with open(os.path.join(HERE, 'blocks.jsonl'), 'w', encoding='utf-8') as fp:
    for f in figs:
        fp.write(json.dumps(f, ensure_ascii=False) + '\n')
print("blocks.jsonl written")

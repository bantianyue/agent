import re, json, os

HERE = "D:/06_Hermes/articles/hidden-decoding-hd4"
html = open(os.path.join(HERE, 'source.html'), encoding='utf-8').read()

def clean(t):
    t = re.sub(r'<[^>]+>', ' ', t)
    for a,b in [('&amp;','&'),('&lt;','<'),('&gt;','>'),('&quot;','"'),("&apos;","'"),('&#39;',"'"),('&nbsp;',' ')]:
        t = t.replace(a,b)
    t = re.sub(r'&#x[0-9a-fA-F]+;', '', t)
    return re.sub(r'\s+', ' ', t).strip()

s1 = html.find('<section id="S1"')
bib = html.find('ltx_bibliography')
region = html[s1:bib if bib>0 else len(html)]

# after_para: paragraph index into full_translation.md (1:1 with source text blocks)
# figure id -> after_para
AP = {
    'S2.F2': 9,    # Figure 2 contrasts HD (para 9 = §2 intro)
    'S2.F3': 26,   # Figure 3 illustrates masks (para 26)
    'S4.F4': 62,   # Figure 4(a) training cost (para 62)
    'S4.F5': 74,   # Figure 5 serving throughput (para 74)
    'S5.F6': 84,   # Figure 6 stream probes (para 84)
    'S5.F7': 87,   # Figure 7 LM-head probes (para 87)
    'S5.F8': 88,   # Figure 8 stream-probe examples (para 88)
    'A8.F9': 93,   # Appendix F9 (last para)
}

figs = []
for m in re.finditer(r'<figure\b.*?</figure>', html, re.S):
    seg = m.group(0)
    fid = re.search(r'\bid="([^"]+)"', seg)
    if not fid:
        continue
    fid = fid.group(1)
    imgs = re.findall(r'<img[^>]*src="([^"]+)"', seg)
    if not imgs:
        continue
    cap = re.search(r'<figcaption.*?>(.*?)</figcaption>', seg, re.S)
    captxt = clean(cap.group(1)) if cap else ''
    src0 = imgs[0]
    url = src0 if src0.startswith('http') else "https://arxiv.org/html/" + src0.lstrip('/')
    is_hero = (fid == 'S0.F1')
    entry = {
        'type': 'figure',
        'id': fid,
        'img': url,
        'caption': captxt,
        'after_para': AP.get(fid, 0),
        'hero': is_hero,
    }
    figs.append(entry)

# order: keep document order; hero first
for i, f in enumerate(figs):
    print(i, f['id'], 'hero=', f['hero'], 'ap=', f['after_para'], '|', f['caption'][:60])

with open(os.path.join(HERE, 'blocks.jsonl'), 'w', encoding='utf-8') as fp:
    for f in figs:
        fp.write(json.dumps(f, ensure_ascii=False) + '\n')
print("blocks.jsonl written, total figures:", len(figs))

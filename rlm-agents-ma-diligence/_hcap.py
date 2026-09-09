import re,sys,html
sys.stdout.reconfigure(encoding='utf-8')
h=open('_harvey.html',encoding='utf-8',errors='ignore').read()
# find figures with caption and image src/alt in order
for m in re.finditer(r'<figure[^>]*>(.*?)</figure>',h,re.S):
    seg=m.group(1)
    alt=re.search(r'<img[^>]+alt="([^"]*)"',seg)
    src=re.search(r'<img[^>]+(?:src|data-src)="([^"]+)"',seg)
    cap=re.search(r'<figcaption[^>]*>(.*?)</figcaption>',seg,re.S)
    print('SRC', (src.group(1) if src else '')[-45:], '| ALT', (alt.group(1)[:70] if alt else ''))
    if cap: print('   CAP:', re.sub(r'\s+',' ',re.sub(r'<[^>]+>','',cap.group(1))).strip()[:120])
# also generic images

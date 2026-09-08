import re,sys
sys.stdout.reconfigure(encoding='utf-8')
html=open('_probe.html',encoding='utf-8').read()
# find each figcaption and its enclosing block
for mm in re.finditer(r'<figcaption[^>]*>(.*?)</figcaption>', html, re.S):
    cap=re.sub(r'<[^>]+>',' ',mm.group(1))
    cap=re.sub(r'\s+',' ',cap).strip()
    # backtrack 2000 chars to capture img tags before caption
    start=max(0, mm.start()-2500)
    seg=html[start:mm.end()]
    srcs=[]
    for im in re.findall(r'<img[^>]+>', seg):
        def grab(pat):
            g=re.search(pat, im); return g.group(1) if g else None
        v=grab(r'(?:data-src|data-original|src|data-lazy-src)="([^"]+)"')
        if v and 'databricks.com' in v and 'logo' not in v:
            srcs.append(v[-60:])
    print('CAP:',cap)
    print('   IMGS:',srcs)
    print('---')

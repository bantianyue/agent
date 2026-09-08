import urllib.request,ssl,re,os
os.environ['HTTP_PROXY']='http://127.0.0.1:7890'; os.environ['HTTPS_PROXY']='http://127.0.0.1:7890'
ctx=ssl.create_default_context()
proxy=urllib.request.ProxyHandler({'http':'http://127.0.0.1:7890','https':'http://127.0.0.1:7890'})
op=urllib.request.build_opener(proxy)
op.addheaders=[('User-Agent','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0 Safari/537.36')]
html=op.open('https://www.databricks.com/blog/achieving-extreme-efficiency-through-specialized-gpu-kernel-generation',timeout=40).read().decode('utf-8','ignore')
open('_probe.html','w',encoding='utf-8').write(html)
print('len',len(html))
m=re.search(r'<article.*?</article>', html, re.S)
print('article tag found', bool(m))
imgs=re.findall(r'<img[^>]+>', html)
print('total <img>', len(imgs))
seen=set()
for im in imgs:
    sm=re.search(r'src="([^"]+)"',im); alt=re.search(r'alt="([^"]*)"',im)
    s=sm.group(1)[:90] if sm else '?'
    if s in seen: continue
    seen.add(s)
    if 'databricks.com' in s:
        print('SRC',s,'| ALT=', (alt.group(1)[:70] if alt else ''))
# look for caption/figure text patterns
for kw in ['Figure 1','Figure 2','Figure 3','Figure 4','<figcaption','figure__caption']:
    idxs=[mm.start() for mm in re.finditer(re.escape(kw),html)]
    print(kw, len(idxs))

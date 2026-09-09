import re,sys,json
sys.stdout.reconfigure(encoding='utf-8')
d=json.load(open('article_data.json',encoding='utf-8'))
for i,s in enumerate(d.get('sections',[])):
    fa=s.get('fig_after') or {}
    figs=[(k,[f.get('src') for f in v]) for k,v in fa.items()]
    print(f'S{i} title={s.get("title")[:30]!r} nparas={len(s.get("paras",[]))} fig_after={figs}')
# original page figures
h=open('page.html',encoding='utf-8',errors='ignore').read()
print('--- original page ---')
for m in re.finditer(r'<figure[^>]*>(.*?)</figure>',h,re.S):
    seg=m.group(1)
    img=re.search(r'<img[^>]+src="([^"]+)"',seg)
    cap=re.search(r'<figcaption[^>]*>(.*?)</figcaption>',seg,re.S)
    c=re.sub(r'<[^>]+>','',cap.group(1)) if cap else ''
    print('IMG',img.group(1)[-40:] if img else None,'| CAP:',re.sub(r'\s+',' ',c).strip()[:80])
print('total figure tags:', len(re.findall(r'<figure',h)))

#!/usr/env python3
"""Download images in document order; hero->cover.png, others->figNN.png."""
import urllib.request, os, json

here=os.path.dirname(os.path.abspath(__file__))
blocks=[]
with open(os.path.join(here,'blocks.jsonl'),encoding='utf-8') as f:
    for line in f:
        line=line.strip()
        if line:
            try: blocks.append(json.loads(line))
            except Exception: pass
figs=[b for b in blocks if b.get('type')=='figure']
n=0
for b in figs:
    src=b['img']
    if b.get('hero'):
        fname='cover.png'
    else:
        n+=1
        fname=f'fig{n:02d}.png'
    try:
        req=urllib.request.Request(src,headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req,timeout=30) as r:
            data=r.read()
            ct=r.headers.get('Content-Type','')
            if 'svg' in ct: fname=fname.rsplit('.',1)[0]+'.svg'
            elif ('jpg' in ct or 'jpeg' in ct) and not fname.endswith('.svg'): fname=fname.rsplit('.',1)[0]+'.jpg'
            with open(os.path.join(here,fname),'wb') as ff: ff.write(data)
            print(f'  OK {fname} ({len(data)//1024}KB)')
    except Exception as e:
        print(f'  FAIL {fname}: {e}')

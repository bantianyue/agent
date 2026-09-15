import fitz,sys,re
sys.stdout.reconfigure(encoding='utf-8')
doc=fitz.open('_ds41.pdf')
def page_info(pno):
    p=doc[pno-1]; W,H=p.rect.width,p.rect.height
    d=p.get_text("dict")
    caps=[]
    for b in d['blocks']:
        if b.get('type')!=0: continue
        txt=''.join(s['text'] for l in b['lines'] for s in l['spans'])
        if re.match(r'^\s*(Figure|Table)\s+\d+', txt):
            caps.append((txt[:70], tuple(round(v) for v in b['bbox'])))
    dr=p.get_drawings()
    bs=[tuple(round(v) for v in it['rect']) for it in dr]
    print(f'--- page {pno} ({round(W)}x{round(H)}) drawings={len(dr)}')
    for c in caps: print('  CAP',c)
    # aggregate drawings into clusters by y
    ys=sorted(bs,key=lambda b:b[1])
    if ys:
        print('  drawing y-range:',ys[0][1],'->',max(b[3] for b in ys))
        print('  first few rects:',ys[:6])
page_info(1)
page_info(5)
page_info(7)
page_info(10)
page_info(11)

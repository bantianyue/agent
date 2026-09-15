import fitz,sys,re
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')
doc=fitz.open('_b42.pdf')
def caps_on(pno):
    out=[]
    p=doc[pno-1]
    for b in p.get_text("dict")['blocks']:
        if b.get('type')!=0: continue
        txt=''.join(s['text'] for l in b['lines'] for s in l['spans'])
        m=re.match(r'^\s*Fig\.\s*(\d+)\s*[:.]',txt)
        if m: out.append((int(m.group(1)), fitz.Rect(b['bbox'])))
    return sorted(out)
for pno in (5,9):
    print('page',pno,caps_on(pno))
def render(pno,label,out,floor):
    p=doc[pno-1]
    cap=None
    for n,r in caps_on(pno):
        if f'Fig. {n}'==label: cap=r
    cands=[fitz.Rect(d['rect']) for d in p.get_drawings()]
    for xref in {im[0] for im in p.get_images(full=True)}:
        for r in p.get_image_rects(xref): cands.append(fitz.Rect(r))
    cands=[r for r in cands if r.width>5 and r.height>2]
    anchor=cap.y0
    for _ in range(200):
        nxt=min([r.y0 for r in cands if r.y1<=anchor+6 and r.y1>=anchor-90 and r.y0>floor], default=None)
        if nxt is None or nxt>=anchor-0.5: break
        anchor=nxt
    top=max(anchor-6, floor)
    clip=fitz.Rect(cap.x0-8, top, cap.x1+8, cap.y0-3)
    pix=p.get_pixmap(matrix=fitz.Matrix(3,3),clip=clip); pix.save(out)
    im=Image.open(out); im.load(); print(label,'p%d'%pno, tuple(round(v) for v in clip), im.size)
# Fig.2: floor = bottom of Fig.1 caption on p5
f1=dict(caps_on(5))[1]
render(5,'Fig. 2',r'D:\06_Hermes\articles\fig02.png', f1.y1+4)
# Fig.5: floor = bottom of Fig.4 caption on p9
f4=dict(caps_on(9))[4]
render(9,'Fig. 5',r'D:\06_Hermes\articles\fig05.png', f4.y1+4)

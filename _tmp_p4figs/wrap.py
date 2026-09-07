# make wrapper html that renders SVG at specified pixel width
import re,sys
for f,w in [("5Dparallelism_8Bmemoryusage.svg",1500),("what_we_learnt_heatmap.svg",1500)]:
    svg=open(f,encoding='utf-8').read()
    # natural width: parse viewBox or width attr
    m=re.search(r'width="([\d.]+)"',svg)
    vb=re.search(r'viewBox="([\d. \-]+)"',svg)
    natw=float(m.group(1)) if m else (float(vb.group(1).split()[2]) if vb else 800)
    nath=float(re.search(r'height="([\d.]+)"',svg).group(1)) if re.search(r'height="([\d.]+)"',svg) else (float(vb.group(1).split()[3]) if vb else 400)
    if natw<10: natw=float(vb.group(1).split()[2]); nath=float(vb.group(1).split()[3])
    disp_w=w; disp_h=int(nath*(w/natw))
    html=f'''<!doctype html><html><head><meta charset="utf-8"><style>html,body{{margin:0;padding:0;background:#fff}}img{{width:{disp_w}px;height:auto;display:block}}</style></head><body><img src="{f}"></body></html>'''
    open(f.replace('.svg','_w.html'),'w',encoding='utf-8').write(html)
    print(f,"nat",natw,"x",nath,"->disp",disp_w,"x",disp_h, "html wrote", f.replace('.svg','_w.html'))

import re,sys
from svglib.svglib import svg2rlg
# mapping file -> target display width px
jobs=[("5Dparallelism_8Bmemoryusage.svg",1650),("what_we_learnt_heatmap.svg",1500),
      ("5d_full.svg",1750),("5d_nutshell_ep.svg",1500),("5d_nutshell_cp.svg",1500),
      ("5d_nutshell_tp_sp.svg",1500)]
for f,tw in jobs:
    d=svg2rlg(f)  # gives pts dims
    natw=d.width; nath=d.height
    disp_w=tw
    disp_h=int(nath*(tw/natw))
    # also parse viewBox fallback units for aspect
    html=('<html><head><meta charset="utf-8"><style>html,body{margin:0;padding:0;background:#ffffff}'
          f'img{{width:{disp_w}px;height:auto;display:block}}</style></head>'
          f'<body><img src="{f}"></body></html>')
    open(f.replace('.svg','_w.html'),'w',encoding='utf-8').write(html)
    print(f,"nat",round(natw,1),"x",round(nath,1),"disp",disp_w,"x",disp_h)

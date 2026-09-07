# -*- coding: utf-8 -*-
import os, re, glob, html as htmllib
from playwright.sync_api import sync_playwright

D = r"D:\06_Hermes\articles\ultrascale-p2-zero-tp-sp-cp"
svgs = {
 "fig00_zero_memory.svg":"fig00_zero_memory.png",
 "fig01_zero1_overlap.svg":"fig01_zero1_overlap.png",
 "fig02_tp_base.svg":"fig02_tp_base.png",
 "fig08_cpmask.svg":"fig08_cpmask.png",
 "fig09_zigzag.svg":"fig09_zigzag.png",
}
def get_viewbox(s):
    m = re.search(r'viewBox=["\']?\s*([-\d.]+)[ ,]+([-\d.]+)[ ,]+([\d.]+)[ ,]+([\d.]+)', s)
    if m:
        x,y,w,h = [float(v) for v in m.groups()]
        if w>0 and h>0: return w,h
    return None, None

W_target = 1500
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    for sx, px in svgs.items():
        sp = os.path.join(D, sx)
        txt = open(sp, encoding="utf-8").read()
        txt = re.sub(r'<\?xml[^>]*\?>', '', txt)
        w,h = get_viewbox(txt)
        if w is None or h is None:
            # search width/height
            wm=re.search(r'width=["\']?([\d.]+)', txt); hm=re.search(r'height=["\']?([\d.]+)', txt)
            w=float(wm.group(1)) if wm else 1200
            h=float(hm.group(1)) if hm else 900
        H = max(int(h*W_target/w),50)
        page = b.new_page(viewport={"width":W_target+8,"height": H+8})
        html = ('<!DOCTYPE html><html><head><meta charset="utf-8">'
                '<style>html,body{margin:0;padding:0;background:#fff}'
                f'svg{{width:{W_target}px;height:{H}px;display:block;background:#fff}}</style>'
                f'</head><body>{txt}</body></html>')
        page.set_content(html, wait_until="load")
        out = os.path.join(D, px)
        page.screenshot(path=out, clip={"x":0,"y":0,"width":W_target+2,"height":H+2})
        page.close()
        # verify variance
        from PIL import Image, ImageStat
        im=Image.open(out).convert("RGB")
        st=ImageStat.Stat(im)
        var=sum(st.var)
        print(sx,"->",px, im.size, "var=%.0f" % var)
    b.close()

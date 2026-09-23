# -*- coding: utf-8 -*-
import os
from PIL import Image
out = []
# move captured figs into article root as figNN.png, compress
mapping = {"cap/fig02.png": "fig02.png", "cap/fig03.png": "fig03.png",
           "cap/fig04.png": "fig04.png", "cap/fig05.png": "fig05.png",
           "cap/fig01_final.png": "_cover_src.png"}
for src, dst in mapping.items():
    im = Image.open(src)
    w, h = im.size
    im = im.convert("RGB")
    if w > 1200:
        im = im.resize((1200, round(h * 1200 / w)), Image.LANCZOS)
    im.save(dst, quality=88, optimize=True)
    out.append("%s -> %s  %dx%d -> %dx%d  %dKB" % (src, dst, w, h, im.size[0], im.size[1], os.path.getsize(dst)//1024))
out.append("fig01.gif %dKB" % (os.path.getsize("fig01.gif")//1024))
open("_prep.txt","w",encoding="utf-8").write("\n".join(out))

#!/usr/bin/env python3
import os, re
from PIL import Image
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))

SVG_SRC = ["Feature1Value.svg","PredictableTarget.svg","TargetWithoutNoise.svg","Target.svg","SGD.svg","IDBD.svg"]

def render(svg):
    out = svg[:-4] + ".png"
    svg_content = open(os.path.join(HERE, svg), encoding="utf-8").read()
    vb = re.search(r'viewBox="([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)"', svg_content)
    x,y,w,h = (float(v) for v in vb.groups())
    W,H = int(w+0.5), int(h+0.5)
    pg.set_viewport_size({"width": W+20,"height": H+20})
    s = re.sub(r'(<svg[^>]*?)(/?>)',
        lambda m: m.group(1)+f' width="{W}" height="{H}" style="display:block" '+m.group(2), svg_content, count=1)
    pg.set_content(f'<!DOCTYPE html><html><head><meta charset="utf-8"></head><body style="margin:0;padding:0;background:white">{s}</body></html>', wait_until="networkidle")
    pg.wait_for_timeout(300)
    p = os.path.join(HERE, out)
    pg.screenshot(path=p, full_page=True)
    im = Image.open(p).convert("RGB")
    bb = im.getbbox()
    if bb: im.crop(bb).save(p)
    return p

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page()
    for s in SVG_SRC:
        render(s)
        print("rendered", s[:-4]+".png")
    b.close()

# rename to document order fig01..fig12
ORDER = {
    "network_backprop_full.png": "fig01.png",  # lead + Fig7
    "Feature1Value.png":       "fig02.png",      # Fig1
    "PredictableTarget.png":   "fig03.png",      # Fig1 cont
    "Feature1Value.png":       "fig04.png",      # Fig2 (copy)
    "TargetWithoutNoise.png":  "fig05.png",      # Fig2 cont
    "Target.png":              "fig06.png",      # Fig3
    "SGD.png":                 "fig07.png",      # Fig4
    "IDBD.png":                "fig08.png",      # Fig5
    "Digit.png":               "fig09.png",      # Fig6
    "3DView.png":              "fig10.png",      # Fig6 cont
    "network_backprop_full.png":"fig11.png",     # Fig7 (copy)
    "network_idbd_full.png":   "fig12.png",      # Fig8
}
# do copies first then originals
import shutil
# fig04 = copy of Feature1Value.png; fig11 = copy of network_backprop_full.png
shutil.copy("Feature1Value.png","fig04.png")
shutil.copy("network_backprop_full.png","fig11.png")
mapping = {"network_backprop_full.png":"fig01.png","Feature1Value.png":"fig02.png","PredictableTarget.png":"fig03.png",
           "TargetWithoutNoise.png":"fig05.png","Target.png":"fig06.png","SGD.png":"fig07.png","IDBD.png":"fig08.png",
           "Digit.png":"fig09.png","3DView.png":"fig10.png","network_idbd_full.png":"fig12.png"}
for src,dst in mapping.items():
    shutil.move(src,dst)
# cleanup svg + leftover
for f in SVG_SRC: os.remove(f)
print("final figs:", sorted(os.listdir(HERE)))

#!/usr/bin/env python3
import os, base64, io
from PIL import Image
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))

SVGS = {
    "PredictableTarget.svg": "fig01.png",  # Figure 1
    "TargetWithoutNoise.svg": "fig02.png",  # Figure 2 (input w/o noise)
    "Target.svg": "fig03.png",               # Figure 3
    "SGD.svg": "fig04.png",                 # Figure 4
    "IDBD.svg": "fig05.png",                # Figure 5
}

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page()
    for svg, out in SVGS.items():
        path = os.path.join(HERE, svg)
        svg_content = open(path, encoding="utf-8").read()
        # inline svg, white bg, preserve intrinsic size via viewBox
        html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"></head>
<body style="margin:0;background:white;display:inline-block">
{svg_content}
</body></html>"""
        pg.set_content(html, wait_until="networkidle")
        pg.wait_for_timeout(300)
        el = pg.query_selector("svg")
        box = el.bounding_box()
        w, h = int(box["width"]), int(box["height"])
        # render at 2x for crisp text
        out_path = os.path.join(HERE, out)
        el.screenshot(path=out_path, scale="css")
        # verify non-white
        img = Image.open(out_path).convert("RGB")
        px = list(img.getdata())
        nw = sum(1 for c in px if c[0] < 240 or c[1] < 240 or c[2] < 240)
        pct = nw / len(px) * 100
        print(f"{out}: {img.size} content={pct:.1f}%")
        if pct < 3:
            raise RuntimeError(f"{out} 几乎全白，SVG 渲染失败")
    b.close()
print("✅ 全部 SVG 渲染完成")

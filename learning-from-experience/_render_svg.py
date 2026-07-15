#!/usr/bin/env python3
import os, re
from PIL import Image
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))

SVGS = {
    "PredictableTarget.svg": "fig01.png",  # Figure 1
    "TargetWithoutNoise.svg": "fig02.png",  # Figure 2
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
        vb = re.search(r'viewBox="([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)"', svg_content)
        if not vb:
            raise RuntimeError(f"{svg} 无 viewBox")
        x, y, w, h = (float(v) for v in vb.groups())
        W, H = int(w + 0.5), int(h + 0.5)
        pg.set_viewport_size({"width": W + 20, "height": H + 20})
        # force explicit size on the svg
        svg_sized = re.sub(r'(<svg[^>]*?)(/?>)',
                           lambda m: m.group(1) + f' width="{W}" height="{H}" style="display:block" ' + m.group(2),
                           svg_content, count=1)
        html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:white">
{svg_sized}
</body></html>"""
        pg.set_content(html, wait_until="networkidle")
        pg.wait_for_timeout(300)
        out_path = os.path.join(HERE, out)
        pg.screenshot(path=out_path, full_page=True)
        img = Image.open(out_path).convert("RGB")
        # trim to content bounds (drop extra whitespace)
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)
            img.save(out_path)
        px = list(img.getdata())
        nw = sum(1 for c in px if c[0] < 240 or c[1] < 240 or c[2] < 240)
        pct = nw / len(px) * 100
        print(f"{out}: {img.size} content={pct:.1f}%")
        if pct < 1:
            raise RuntimeError(f"{out} 几乎全白，渲染失败")
    b.close()
print("✅ 全部 SVG 渲染完成")

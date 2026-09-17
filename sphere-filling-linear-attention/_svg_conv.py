import os, re, pathlib
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

base = r"D:\06_Hermes\articles\sphere-filling-linear-attention"
order = {"fig02": "fig02", "fig03": "fig03", "fig04": "fig04"}

with sync_playwright() as p:
    browser = p.chromium.launch()
    for name in order:
        svg_text = open(os.path.join(base, name + ".svg"), encoding="utf-8").read()
        vb = re.search(r'viewBox="([-\d.\s]+)"', svg_text)
        w = h = None
        if vb:
            nums = [float(x) for x in vb.group(1).split()]
            if len(nums) == 4 and nums[2] > 0 and nums[3] > 0:
                w, h = nums[2], nums[3]
        if not w:
            m = re.search(r'width="([\d.]+)"', svg_text)
            w = float(m.group(1)) if m else 1200
            h = w * 0.6
        W = 1500
        H = int(h * W / w)
        page = browser.new_page(viewport={"width": W + 4, "height": H + 4})
        html = ('<!DOCTYPE html><html><head><meta charset="utf-8">'
                '<style>html,body{margin:0;padding:0;background:#fff}'
                f'svg{{width:{W}px;height:{H}px;display:block}}</style>'
                f'</head><body>{svg_text}</body></html>')
        page.set_content(html, wait_until="load")
        page.wait_for_timeout(900)
        out = os.path.join(base, order[name] + "_raw.png")
        page.screenshot(path=out)
        page.close()
        print(f"OK {name} viewBox={w}x{h} -> {W}x{H} bbox_file={out}")
    browser.close()

for name in order:
    p_raw = os.path.join(base, order[name] + "_raw.png")
    im = Image.open(p_raw).convert("RGB")
    a = np.array(im.convert("L"))
    nw = a < 245
    rows = nw.any(axis=1); cols = nw.any(axis=0)
    if rows.any():
        r0, r1 = rows.argmax(), len(rows) - rows[::-1].argmax() - 1
        c0, c1 = cols.argmax(), len(cols) - cols[::-1].argmax() - 1
        pad = 8
        im = im.crop((max(0, c0 - pad), max(0, r0 - pad),
                      min(im.size[0], c1 + pad), min(im.size[1], r1 + pad)))
    final = os.path.join(base, order[name] + ".png")
    im.save(final)
    print(f"CROP {name} -> {final} size={im.size} var={np.array(im.convert('L')).var():.0f}")

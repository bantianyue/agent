#!/usr/bin/env python3
import os, re
from PIL import Image
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
svg = "Feature1Value.svg"; out = "Feature1Value.png"
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page()
    svg_content = open(os.path.join(HERE, svg), encoding="utf-8").read()
    vb = re.search(r'viewBox="([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)"', svg_content)
    x, y, w, h = (float(v) for v in vb.groups())
    W, H = int(w+0.5), int(h+0.5)
    pg.set_viewport_size({"width": W+20, "height": H+20})
    svg_sized = re.sub(r'(<svg[^>]*?)(/?>)',
        lambda m: m.group(1)+f' width="{W}" height="{H}" style="display:block" '+m.group(2), svg_content, count=1)
    pg.set_content(f'<!DOCTYPE html><html><head><meta charset="utf-8"></head><body style="margin:0;padding:0;background:white">{svg_sized}</body></html>', wait_until="networkidle")
    pg.wait_for_timeout(300)
    pg.screenshot(path=os.path.join(HERE, out), full_page=True)
    b.close()
print("OK Feature1Value.png")

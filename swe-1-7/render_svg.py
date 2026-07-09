#!/usr/bin/env python3
import asyncio, os, glob
from playwright.async_api import async_playwright

SRC = "svg_src"
OUT = "."
files = sorted(glob.glob(os.path.join(SRC, "*.svg")))
print(f"Found {len(files)} SVGs")

async def render(svg_file, png_file):
    with open(svg_file, "r", encoding="utf-8") as f:
        svg = f.read()
    # extract width/height from svg root tag for base scale
    import re
    m = re.search(r'width="([\d.]+)pt"', svg)
    base_w = float(m.group(1)) if m else 500.0
    scale = 3
    w = int(base_w * scale)
    html = f'''<!DOCTYPE html><html><body style="margin:0;background:white;display:inline-block;">
<div style="width:{w}px;">{svg}</div></body></html>'''
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(html, wait_until="networkidle")
        await page.set_viewport_size({"width": w + 40, "height": 2000})
        await asyncio.sleep(0.6)
        await page.screenshot(path=png_file, full_page=True)
        await browser.close()
    sz = os.path.getsize(png_file)
    return sz

async def main():
    for sf in files:
        base = os.path.splitext(os.path.basename(sf))[0]
        out = os.path.join(OUT, f"{base}.png")
        sz = await render(sf, out)
        print(f"  {base}.png ({sz//1024}KB)")

asyncio.run(main())
print("DONE")

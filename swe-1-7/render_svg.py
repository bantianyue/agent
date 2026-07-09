#!/usr/bin/env python3
import asyncio, os, glob, re
from playwright.async_api import async_playwright

SRC = "svg_src"
OUT = "."
files = sorted(glob.glob(os.path.join(SRC, "*.svg")))
print(f"Found {len(files)} SVGs")

def scaled_svg(svg, scale=3):
    # parse viewBox to know aspect; set width/height to viewBox size * scale
    m = re.search(r'viewBox="([\d.\-]+)\s+([\d.\-]+)\s+([\d.]+)\s+([\d.]+)"', svg)
    if m:
        _, _, vbw, vbh = map(float, m.groups())
        w = int(vbw * scale); h = int(vbh * scale)
    else:
        w = int(1500); h = int(900)
    # replace width/height attrs on <svg ...>
    svg2 = re.sub(r'width="[^"]*"', f'width="{w}px"', svg, count=1)
    svg2 = re.sub(r'height="[^"]*"', f'height="{h}px"', svg2, count=1)
    return svg2, w, h

async def render(svg_file, png_file):
    with open(svg_file, "r", encoding="utf-8") as f:
        svg = f.read()
    svg, w, h = scaled_svg(svg)
    html = f'''<!DOCTYPE html><html><body style="margin:0;background:white;">
<div style="width:{w}px;height:{h}px;">{svg}</div></body></html>'''
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_viewport_size({"width": w + 20, "height": h + 20})
        await page.set_content(html, wait_until="networkidle")
        await asyncio.sleep(0.6)
        await page.locator("div").first.screenshot(path=png_file)
        await browser.close()
    return os.path.getsize(png_file)

async def main():
    for sf in files:
        base = os.path.splitext(os.path.basename(sf))[0]
        out = os.path.join(OUT, f"{base}.png")
        sz = await render(sf, out)
        print(f"  {base}.png ({sz//1024}KB)")

asyncio.run(main())
print("DONE")

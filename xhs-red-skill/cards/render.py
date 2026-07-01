import asyncio
from playwright.async_api import async_playwright
import os

CARDS_DIR = "D:/06_Hermes/articles/xhs-red-skill/cards"
HTML_PATH = os.path.join(CARDS_DIR, "index.html")
OUTPUT_DIR = os.path.join(CARDS_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

async def render():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1200, "height": 1600})
        await page.goto(f"file://{HTML_PATH}", wait_until="networkidle")
        await asyncio.sleep(2)
        
        posters = await page.query_selector_all("section.poster.xhs")
        print(f"Found {len(posters)} posters")
        
        for i, poster in enumerate(posters):
            box = await poster.bounding_box()
            if box:
                path = os.path.join(OUTPUT_DIR, f"xhs-{i+1:02d}.png")
                await poster.screenshot(path=path)
                print(f"  xhs-{i+1:02d}.png: {box['width']}x{box['height']}")
        
        await browser.close()

asyncio.run(render())
print("DONE")

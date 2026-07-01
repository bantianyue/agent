import asyncio
from playwright.async_api import async_playwright
import os

CARDS_DIR = "D:/06_Hermes/articles/xhs-red-skill/cards"
OUTPUT_DIR = os.path.join(CARDS_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

async def render():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1200, "height": 1600})
        await page.goto(f"file://{CARDS_DIR}/index.html", wait_until="networkidle")
        await asyncio.sleep(2)
        
        posters = await page.query_selector_all("section.poster.xhs")
        print(f"Found {len(posters)} posters")
        
        for i, poster in enumerate(posters):
            # Get bounding box
            box = await poster.bounding_box()
            if not box:
                print(f"  Poster {i+1}: no bounding box")
                continue
            print(f"  Poster {i+1}: {box['width']}x{box['height']} at ({box['x']},{box['y']})")
            
            # Set viewport to match poster size
            await page.set_viewport_size({"width": int(box["width"]), "height": int(box["height"])})
            await asyncio.sleep(0.3)
            
            # Take screenshot of just this element
            await poster.screenshot(path=os.path.join(OUTPUT_DIR, f"xhs-{i+1:02d}.png"))
            print(f"  xhs-{i+1:02d}.png saved")
        
        await browser.close()
    print("DONE")

asyncio.run(render())

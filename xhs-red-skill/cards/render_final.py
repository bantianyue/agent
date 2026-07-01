import asyncio
from playwright.async_api import async_playwright
import os

CARDS_DIR = "D:/06_Hermes/articles/xhs-red-skill/cards"
OUTPUT_DIR = os.path.join(CARDS_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

async def render():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1080, "height": 1440})
        await page.goto(f"file://{CARDS_DIR}/index.html", wait_until="networkidle")
        await asyncio.sleep(3)
        
        posters = await page.query_selector_all("section.poster.xhs")
        print(f"Found {len(posters)} posters")
        
        for i, poster in enumerate(posters):
            # Scroll to this poster
            await poster.scroll_into_view_if_needed()
            await asyncio.sleep(0.5)
            
            # Take screenshot of the element
            await poster.screenshot(path=os.path.join(OUTPUT_DIR, f"xhs-{i+1:02d}.png"))
            
            # Verify it's not black
            from PIL import Image
            img = Image.open(os.path.join(OUTPUT_DIR, f"xhs-{i+1:02d}.png"))
            extrema = img.convert('L').getextrema()
            avg = sum(img.convert('L').getdata()) / (img.size[0] * img.size[1])
            status = "✅" if extrema[1] > 30 else "❌ BLACK"
            print(f"  xhs-{i+1:02d}.png: {img.size} range={extrema} avg={avg:.1f} {status}")
        
        await browser.close()
    print("DONE")

asyncio.run(render())

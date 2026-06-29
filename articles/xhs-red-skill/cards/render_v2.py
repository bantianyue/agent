import asyncio
from playwright.async_api import async_playwright
import os
from PIL import Image

CARDS_DIR = "D:/06_Hermes/articles/xhs-red-skill/cards"
OUTPUT_DIR = os.path.join(CARDS_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

async def render():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1080, "height": 1440})
        await page.goto(f"file://{CARDS_DIR}/index.html", wait_until="networkidle")
        await asyncio.sleep(3)
        
        cards = await page.query_selector_all("div.card")
        print(f"Found {len(cards)} cards")
        
        for i, card in enumerate(cards):
            await card.scroll_into_view_if_needed()
            await asyncio.sleep(0.5)
            await card.screenshot(path=os.path.join(OUTPUT_DIR, f"xhs-{i+1:02d}.png"))
            
            img = Image.open(os.path.join(OUTPUT_DIR, f"xhs-{i+1:02d}.png"))
            extrema = img.convert('L').getextrema()
            status = "✅" if extrema[1] > 30 else "❌ BLACK"
            print(f"  xhs-{i+1:02d}.png: {img.size} range={extrema} {status}")
        
        await browser.close()
    print("DONE")

asyncio.run(render())

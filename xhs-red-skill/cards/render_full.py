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
        
        # Get full page height
        height = await page.evaluate("document.body.scrollHeight")
        print(f"Full page height: {height}")
        
        # Set viewport to full page
        await page.set_viewport_size({"width": 1080, "height": height})
        await asyncio.sleep(1)
        
        # Take full page screenshot
        await page.screenshot(path=os.path.join(OUTPUT_DIR, "full.png"), full_page=True)
        print("Full page screenshot saved")
        
        # Now crop each poster from the full image
        full_img = Image.open(os.path.join(OUTPUT_DIR, "full.png"))
        
        # Get poster positions from DOM
        positions = await page.evaluate("""
            () => {
                const posters = document.querySelectorAll('section.poster.xhs');
                return Array.from(posters).map((p, i) => {
                    const r = p.getBoundingClientRect();
                    return {index: i, x: r.x, y: r.y, w: r.width, h: r.height};
                });
            }
        """)
        
        print(f"Found {len(positions)} posters")
        for pos in positions:
            print(f"  Poster {pos['index']+1}: ({pos['x']},{pos['y']}) {pos['w']}x{pos['h']}")
            # Crop from full image
            crop = full_img.crop((pos['x'], pos['y'], pos['x'] + pos['w'], pos['y'] + pos['h']))
            crop.save(os.path.join(OUTPUT_DIR, f"xhs-{pos['index']+1:02d}.png"))
            print(f"    -> xhs-{pos['index']+1:02d}.png saved")
        
        await browser.close()
    print("DONE")

asyncio.run(render())

"""Capture full page at 2x, then crop SVGs locally"""
import asyncio, json, base64, os
from playwright.async_api import async_playwright

OUTDIR = r"D:\06_Hermes\articles\kv-cache-compression-and-its-infra-problems"

# SVG bounding boxes (from earlier CDP measurement)
svgs = [
    ("fig1_memory_oom", 217, 1457, 831, 300),
    ("fig2_streamingllm", 217, 2326, 831, 190),
    ("fig3_h2o", 217, 2875, 831, 232),
    ("fig4_snapkv", 217, 3622, 831, 172),
    ("fig5_paged_fragmentation", 275, 4878, 715, 255),
    ("fig6_rope_geometry", 217, 5867, 831, 469),
    ("fig7_order_preserving", 217, 6860, 831, 250),
    ("fig8_hole_filling", 217, 7275, 831, 250),
    ("fig9_results_comparison", 217, 8231, 831, 333),
]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else (await context.new_page())
        
        # Navigate if needed
        if "research.nvidia.com" not in page.url:
            await page.goto("https://research.nvidia.com/labs/eai/blogs/kv-cache-compression-and-its-infra-problems/",
                          wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)
        
        # Full page screenshot at 2x
        await page.evaluate("document.body.style.overflow = 'visible'")
        await page.wait_for_timeout(500)
        
        # Use CDP directly for 2x full page
        cdp = await context.new_cdp_session(page)
        dims = await cdp.send("Runtime.evaluate", {
            "expression": "JSON.stringify({w: document.body.scrollWidth, h: document.body.scrollHeight})",
            "returnByValue": True
        })
        dims = json.loads(dims["result"]["value"])
        print(f"Page: {dims['w']}x{dims['h']}")
        
        # Set 2x
        await cdp.send("Emulation.setDeviceMetricsOverride", {
            "width": min(dims["w"], 1280),
            "height": min(dims["h"], 12097),
            "deviceScaleFactor": 2,
            "mobile": False
        })
        await asyncio.sleep(1)
        
        # Capture at 2x scale
        result = await cdp.send("Page.captureScreenshot", {
            "format": "png",
            "clip": {"x": 0, "y": 0, "width": 1280, "height": min(dims["h"], 12097), "scale": 1}
        })
        data = result["data"]
        print(f"Full page capture: {len(data)//1024}KB base64")
        
        full_path = os.path.join(OUTDIR, "full_hd.png")
        with open(full_path, "wb") as f:
            f.write(base64.b64decode(data))
        
        # Now crop at 2x coordinates
        from PIL import Image
        img = Image.open(full_path)
        
        for name, x, y, w, h in svgs:
            crop = img.crop((x*2-10, y*2-10, (x+w)*2+10, (y+h)*2+10))
            fpath = os.path.join(OUTDIR, f"{name}.png")
            crop.save(fpath)
            sz = os.path.getsize(fpath) // 1024
            print(f"{name}.png: {sz}KB")
        
        await cdp.send("Emulation.clearDeviceMetricsOverride", {})
        print("Done!")

asyncio.run(main())

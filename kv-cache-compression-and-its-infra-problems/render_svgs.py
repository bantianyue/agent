"""Render SVG figures from NVIDIA blog using CDP Chrome"""
import json, base64, os, asyncio
import websockets

OUTDIR = r"D:\06_Hermes\articles\kv-cache-compression-and-its-infra-problems"

# SVG viewBox data for each figure (from page.html parsing)
# We'll create an HTML page that renders each SVG at high resolution
with open(os.path.join(OUTDIR, "page.html"), "r", encoding="utf-8") as f:
    html = f.read()

# Extract 9 SVGs
import re
svg_pattern = re.compile(r'<svg[^>]*>.*?</svg>', re.DOTALL)
svgs = svg_pattern.findall(html)

names = [
    "fig1_memory_oom",
    "fig2_streamingllm",
    "fig3_h2o",
    "fig4_snapkv",
    "fig5_paged_fragmentation",
    "fig6_rope_geometry",
    "fig7_order_preserving",
    "fig8_hole_filling",
    "fig9_results_comparison",
]

# Create a temp HTML that renders all SVGs in a tall strip
styled_svgs = []
for svg in svgs:
    # Ensure SVG has width/height for rendering
    if 'width=' not in svg:
        svg = svg.replace('<svg ', '<svg width="900" ')
    if 'height=' not in svg:
        svg = svg.replace('<svg ', '<svg height="400" ')
    styled_svgs.append(svg)

render_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body {{ margin: 0; background: white; }}
svg {{ display: block; margin: 0; }}
</style></head><body>
{"<hr>".join(styled_svgs)}
</body></html>"""

with open(os.path.join(OUTDIR, "_render.html"), "w", encoding="utf-8") as f:
    f.write(render_html)

print(f"Render HTML written ({len(render_html)} chars)")

async def capture():
    # Open a new tab to the render HTML
    ws_url = "ws://localhost:9222/devtools/browser"
    
    async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
        # Create target
        cmd = {"id": 1, "method": "Target.createTarget", "params": {"url": f"file:///{OUTDIR}/_render.html".replace('\\', '/'), "width": 1280, "height": 8000}}
        await ws.send(json.dumps(cmd))
        resp = json.loads(await ws.recv())
        tab_id = resp["result"]["targetId"]
        print(f"Tab: {tab_id}")
        
        # Switch to page target
        page_ws_url = f"ws://localhost:9222/devtools/page/{tab_id}"
        
    # Connect directly to the page
    async with websockets.connect(f"ws://localhost:9222/devtools/page/{tab_id}", max_size=50*1024*1024) as ps:
        await asyncio.sleep(3)
        
        # Set device scale to 2
        cmd = {"id": 1, "method": "Emulation.setDeviceMetricsOverride", "params": {"width": 1280, "height": 8000, "deviceScaleFactor": 2, "mobile": False}}
        await ps.send(json.dumps(cmd))
        await asyncio.sleep(0.5)
        _ = json.loads(await ps.recv())
        
        # Get page dimensions
        cmd = {"id": 2, "method": "Runtime.evaluate", "params": {"expression": "JSON.stringify({w: document.body.scrollWidth, h: document.body.scrollHeight})", "returnByValue": True}}
        await ps.send(json.dumps(cmd))
        resp = json.loads(await ps.recv())
        dims = json.loads(resp["result"]["result"]["value"])
        print(f"Render page: {dims['w']}x{dims['h']}")
        
        # Full page capture
        cmd = {"id": 3, "method": "Page.captureScreenshot", "params": {"format": "png", "clip": {"x": 0, "y": 0, "width": min(dims["w"], 1280), "height": min(dims["h"], 8000), "scale": 1}}}
        await ps.send(json.dumps(cmd))
        resp = json.loads(await ps.recv())
        data = resp["result"]["data"]
        
        full_path = os.path.join(OUTDIR, "_render_full.png")
        with open(full_path, "wb") as f:
            f.write(base64.b64decode(data))
        print(f"Full render: {os.path.getsize(full_path)//1024}KB")
        
        # Crop each SVG by calculating y position
        # Each SVG at 2x: position_i = sum of previous SVG heights at 2x
        from PIL import Image
        img = Image.open(full_path)
        
        # We need to know each SVG's rendered height (at 2x)
        # Use getBoundingClientRect for each SVG
        current_y = 0
        for i, (name, svg) in enumerate(zip(names, svgs)):
            # Get height from viewBox
            vb = re.search(r'viewBox="[^"]* (\d+)"', svg)
            height_px = int(vb.group(1)) if vb else 200
            # With <hr> separators (1px), at 2x
            hr_offset = 2 * 1 if i > 0 else 0
            y2 = current_y
            h2 = height_px * 2
            x2 = 0
            w2 = min(1280, 1800)  # enough width
            
            crop = img.crop((x2, y2, x2 + w2, y2 + h2))
            fpath = os.path.join(OUTDIR, f"{name}.png")
            crop.save(fpath)
            sz = os.path.getsize(fpath) // 1024
            print(f"{name}.png: {sz}KB at y={y2}")
            
            current_y = y2 + h2 + 2  # +2 for hr
        
        # Reset
        cmd = {"id": 99, "method": "Emulation.clearDeviceMetricsOverride", "params": {}}
        await ps.send(json.dumps(cmd))
        
        # Close tab
        cmd = {"id": 100, "method": "Target.closeTarget", "params": {"targetId": tab_id}}
        await ps.send(json.dumps(cmd))

asyncio.run(capture())

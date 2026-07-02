"""Render SVG figures - simpler approach: open page with file:// URL"""
import json, base64, os, asyncio, re
import websockets

OUTDIR = r"D:\06_Hermes\articles\kv-cache-compression-and-its-infra-problems"

# Create a tab to the render HTML
TAB = None
async def main():
    global TAB
    # Get browser WS URL
    info = json.loads(await (await asyncio.get_event_loop().run_in_executor(
        None, lambda: __import__('urllib.request').request.urlopen("http://localhost:9222/json/version").read()
    )))
    ws_url = info["webSocketDebuggerUrl"]
    
    async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
        # Create target
        file_url = "file:///D:/06_Hermes/articles/kv-cache-compression-and-its-infra-problems/_render.html"
        cmd = {"id": 1, "method": "Target.createTarget", "params": {"url": file_url, "width": 1280, "height": 8000}}
        await ws.send(json.dumps(cmd))
        resp = json.loads(await ws.recv())
        tab_id = resp["result"]["targetId"]
        print(f"Tab: {tab_id}")
        global TAB
        TAB = tab_id
    
    # Now connect to the page directly
    page_ws_url = f"ws://localhost:9222/devtools/page/{tab_id}"
    async with websockets.connect(page_ws_url, max_size=50*1024*1024) as ps:
        await asyncio.sleep(4)
        
        # Set device scale to 2
        cmd = {"id": 1, "method": "Emulation.setDeviceMetricsOverride",
               "params": {"width": 1280, "height": 8000, "deviceScaleFactor": 2, "mobile": False}}
        await ps.send(json.dumps(cmd))
        await asyncio.sleep(1)
        _ = json.loads(await ps.recv())
        
        # Get page height
        cmd = {"id": 2, "method": "Runtime.evaluate",
               "params": {"expression": "document.body.scrollHeight", "returnByValue": True}}
        await ps.send(json.dumps(cmd))
        resp = json.loads(await ps.recv())
        ph = resp["result"]["result"]["value"]
        print(f"Page height: {ph}")
        
        # Full page capture
        cmd = {"id": 3, "method": "Page.captureScreenshot",
               "params": {"format": "png", "clip": {"x": 0, "y": 0, "width": 1280, "height": min(ph, 8000), "scale": 1}}}
        await ps.send(json.dumps(cmd))
        resp = json.loads(await ps.recv())
        data = resp["result"]["data"]
        
        full_path = os.path.join(OUTDIR, "_render_full.png")
        with open(full_path, "wb") as f:
            f.write(base64.b64decode(data))
        print(f"Full render: {os.path.getsize(full_path)//1024}KB")
        
        from PIL import Image
        img = Image.open(full_path)
        
        # Get each SVG's rendered rect at 2x
        cmd = {"id": 4, "method": "Runtime.evaluate",
               "params": {"expression": "JSON.stringify(Array.from(document.querySelectorAll('svg')).map(s => {const r=s.getBoundingClientRect(); return {x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height)}}))",
                          "returnByValue": True}}
        await ps.send(json.dumps(cmd))
        resp = json.loads(await ps.recv())
        rects = json.loads(resp["result"]["result"]["value"])
        
        names = ["fig1_memory_oom","fig2_streamingllm","fig3_h2o","fig4_snapkv",
                 "fig5_paged_fragmentation","fig6_rope_geometry","fig7_order_preserving",
                 "fig8_hole_filling","fig9_results_comparison"]
        
        for i, (name, r) in enumerate(zip(names, rects)):
            # At 2x scale, coordinates are doubled
            crop = img.crop((r['x']*2, r['y']*2, (r['x']+r['w'])*2, (r['y']+r['h'])*2))
            fpath = os.path.join(OUTDIR, f"{name}.png")
            crop.save(fpath)
            sz = os.path.getsize(fpath) // 1024
            print(f"{name}.png: {sz}KB at ({r['x']},{r['y']}) {r['w']}x{r['h']}")
        
        # Reset metrics
        cmd = {"id": 99, "method": "Emulation.clearDeviceMetricsOverride", "params": {}}
        await ps.send(json.dumps(cmd))
        _ = json.loads(await ps.recv())
        
        # Close tab
        cmd = {"id": 100, "method": "Target.closeTarget", "params": {"targetId": tab_id}}
        await ps.send(json.dumps(cmd))

asyncio.run(main())

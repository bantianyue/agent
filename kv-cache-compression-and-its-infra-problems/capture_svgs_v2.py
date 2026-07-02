import asyncio, json, base64, os, sys

TAB_ID = sys.argv[1]
OUTDIR = r"D:\06_Hermes\articles\kv-cache-compression-and-its-infra-problems"

import websockets

async def main():
    ws_url = f"ws://localhost:9222/devtools/page/{TAB_ID}"
    async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
        # Check page is alive
        cmd = {"id": 0, "method": "Runtime.evaluate", "params": {"expression": "document.title", "returnByValue": True}}
        await ws.send(json.dumps(cmd))
        resp = json.loads(await ws.recv())
        title = resp["result"]["result"]["value"]
        print(f"Page: {title}", flush=True)

        # Get page dimensions
        cmd = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": "JSON.stringify({w: document.body.scrollWidth, h: document.body.scrollHeight})", "returnByValue": True}}
        await ws.send(json.dumps(cmd))
        resp = json.loads(await ws.recv())
        dims = json.loads(resp["result"]["result"]["value"])
        pw, ph = min(dims["w"], 1280), min(dims["h"], 10000)
        print(f"Dims: {dims['w']}x{dims['h']}, capture: {pw}x{ph}", flush=True)

        # Set 2x scale
        cmd = {"id": 2, "method": "Emulation.setDeviceMetricsOverride",
               "params": {"width": 1280, "height": 10000, "deviceScaleFactor": 2, "mobile": False}}
        await ws.send(json.dumps(cmd))
        await asyncio.sleep(1)
        _ = json.loads(await ws.recv())

        # Capture in chunks to avoid timeout
        chunk_h = 4000  # capture 4000px at a time
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

        from PIL import Image
        import io

        for name, x, y, w, h in svgs:
            # Capture just the SVG region at 2x
            cmd = {"id": 3, "method": "Page.captureScreenshot",
                   "params": {"format": "png", "clip": {"x": x, "y": y, "width": w, "height": h, "scale": 2}}}
            await ws.send(json.dumps(cmd))
            resp = json.loads(await ws.recv())
            if "result" in resp and "data" in resp["result"]:
                data = resp["result"]["data"]
                fpath = os.path.join(OUTDIR, f"{name}.png")
                with open(fpath, "wb") as f:
                    f.write(base64.b64decode(data))
                sz = os.path.getsize(fpath) // 1024
                print(f"{name}.png: {sz}KB", flush=True)
            else:
                print(f"FAIL {name}: {resp.get('error', 'unknown')}", flush=True)

        # Reset
        cmd = {"id": 99, "method": "Emulation.clearDeviceMetricsOverride", "params": {}}
        await ws.send(json.dumps(cmd))
        print("Done!", flush=True)

asyncio.run(main())

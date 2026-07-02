import json, asyncio, websockets, base64, os

TAB_ID = "9E08C942C306B39B42A099A9804422C4"
OUTDIR = r"D:\06_Hermes\articles\kv-cache-compression-and-its-infra-problems"

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
    ws_url = f"ws://localhost:9222/devtools/page/{TAB_ID}"
    async with websockets.connect(ws_url, max_size=20*1024*1024) as ws:
        for name, x, y, w, h in svgs:
            # Set 2x scale
            cmd = {"id": 1, "method": "Emulation.setDeviceMetricsOverride",
                   "params": {"width": 1265, "height": 12097, "deviceScaleFactor": 2, "mobile": False}}
            await ws.send(json.dumps(cmd))
            await asyncio.sleep(0.3)
            _ = json.loads(await ws.recv())

            # Capture at 2x
            cmd2 = {"id": 2, "method": "Page.captureScreenshot",
                    "params": {"format": "png", "clip": {"x": x, "y": y, "width": w, "height": h, "scale": 2}}}
            await ws.send(json.dumps(cmd2))
            resp = json.loads(await ws.recv())
            data = resp["result"]["data"]

            fpath = os.path.join(OUTDIR, f"{name}.png")
            with open(fpath, "wb") as f:
                f.write(base64.b64decode(data))
            sz = os.path.getsize(fpath) // 1024
            print(f"{name}.png: {sz}KB")

    # Reset
    cmd3 = {"id": 3, "method": "Emulation.clearDeviceMetricsOverride", "params": {}}
    await ws.send(json.dumps(cmd3))

asyncio.run(main())

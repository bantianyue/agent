import json, asyncio, websockets, base64, os

TAB_ID = "D17305A7E3B4CDA251B44070632C80A6"
OUTDIR = r"D:\06_Hermes\articles\kv-cache-compression-and-its-infra-problems"
names = ["fig1_memory_oom","fig2_streamingllm","fig3_h2o","fig4_snapkv",
         "fig5_paged_fragmentation","fig6_rope_geometry","fig7_order_preserving",
         "fig8_hole_filling","fig9_results_comparison"]

async def main():
    ws_url = f"ws://localhost:9222/devtools/page/{TAB_ID}"
    async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
        await asyncio.sleep(1)
        
        # Get SVG rects
        cmd = {"id": 1, "method": "Runtime.evaluate",
               "params": {"expression": "JSON.stringify(Array.from(document.querySelectorAll('svg')).map(s => {const r=s.getBoundingClientRect(); return {x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height)}}))",
                          "returnByValue": True}}
        await ws.send(json.dumps(cmd))
        resp = json.loads(await ws.recv())
        rects = json.loads(resp["result"]["result"]["value"])
        
        for i, (name, r) in enumerate(zip(names, rects)):
            await asyncio.sleep(0.3)
            cmd = {"id": 10+i, "method": "Page.captureScreenshot",
                   "params": {"format": "png", "clip": {"x": r["x"], "y": r["y"], "width": r["w"], "height": r["h"], "scale": 2}}}
            await ws.send(json.dumps(cmd))
            resp = json.loads(await ws.recv())
            data = resp["result"]["data"]
            fpath = os.path.join(OUTDIR, f"{name}.png")
            with open(fpath, "wb") as f:
                f.write(base64.b64decode(data))
            sz = os.path.getsize(fpath) // 1024
            print(f"{name}.png: {sz}KB")

asyncio.run(main())

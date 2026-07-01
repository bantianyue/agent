import asyncio
import json
import os
import base64
import websockets

OUTPUT_DIR = "D:/06_Hermes/articles/xhs-red-skill/cards/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

PAGE_WS = "ws://localhost:9222/devtools/page/E023609022A636D83F2C1D5F62EA2C82"

async def render():
    async with websockets.connect(PAGE_WS, max_size=10*1024*1024) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Page.enable"}))
        await ws.recv()
        await asyncio.sleep(2)

        count = 6
        for i in range(count):
            # Scroll poster into view first
            await ws.send(json.dumps({
                "id": 100+i, "method": "Runtime.evaluate",
                "params": {
                    "expression": f"""
                        (() => {{
                            const p = document.querySelectorAll('section.poster.xhs')[{i}];
                            p.scrollIntoView({{block:'start'}});
                            const r = p.getBoundingClientRect();
                            return JSON.stringify({{x:r.x, y:r.y, w:r.width, h:r.height}});
                        }})()
                    """,
                    "returnByValue": True
                }
            }))
            resp = json.loads(await ws.recv())
            rect = json.loads(resp["result"]["result"]["value"])
            print(f"  Poster {i+1} rect: {rect}")
            await asyncio.sleep(0.5)

            # Now clip screenshot to this poster's viewport coordinates
            await ws.send(json.dumps({
                "id": 200+i, "method": "Page.captureScreenshot",
                "params": {
                    "format": "png",
                    "clip": {
                        "x": rect["x"], "y": rect["y"],
                        "width": rect["w"], "height": rect["h"],
                        "scale": 2
                    }
                }
            }))
            resp = json.loads(await ws.recv())
            img_data = resp["result"]["data"]

            path = os.path.join(OUTPUT_DIR, f"xhs-{i+1:02d}.png")
            with open(path, "wb") as f:
                f.write(base64.b64decode(img_data))
            print(f"  xhs-{i+1:02d}.png saved")

    print("DONE")

asyncio.run(render())

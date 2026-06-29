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
        await asyncio.sleep(1)

        count = 6
        for i in range(count):
            # Set viewport to exactly one poster size so only 1 poster visible at a time
            await ws.send(json.dumps({
                "id": 10+i, "method": "Emulation.setDeviceMetricsOverride",
                "params": {"width": 1080, "height": 1440, "deviceScaleFactor": 2, "mobile": False}
            }))
            await ws.recv()
            await asyncio.sleep(0.3)

            # Scroll poster into view
            await ws.send(json.dumps({
                "id": 100+i, "method": "Runtime.evaluate",
                "params": {
                    "expression": f"""
                        (() => {{
                            const p = document.querySelectorAll('section.poster.xhs')[{i}];
                            p.scrollIntoView({{block:'start'}});
                            return 'scrolled to ' + {i};
                        }})()
                    """,
                    "returnByValue": True
                }
            }))
            await ws.recv()
            await asyncio.sleep(1)

            # Screenshot full page (which is now just this one poster)
            await ws.send(json.dumps({
                "id": 200+i, "method": "Page.captureScreenshot",
                "params": {"format": "png"}
            }))
            resp = json.loads(await ws.recv())
            img_data = resp["result"]["data"]

            path = os.path.join(OUTPUT_DIR, f"xhs-{i+1:02d}.png")
            with open(path, "wb") as f:
                f.write(base64.b64decode(img_data))
            print(f"  xhs-{i+1:02d}.png saved ({len(img_data)} bytes)")

    print("DONE")

asyncio.run(render())

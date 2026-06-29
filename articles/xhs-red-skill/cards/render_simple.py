import asyncio
import json
import os
import base64
import websockets

OUTPUT_DIR = "D:/06_Hermes/articles/xhs-red-skill/cards/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# The card tab is already open at localhost:18999/index.html
PAGE_WS = "ws://localhost:9222/devtools/page/E023609022A636D83F2C1D5F62EA2C82"

async def render():
    async with websockets.connect(PAGE_WS, max_size=10*1024*1024) as ws:
        # Enable Page domain
        await ws.send(json.dumps({"id": 1, "method": "Page.enable"}))
        await ws.recv()
        await asyncio.sleep(2)
        
        # Get poster count
        await ws.send(json.dumps({
            "id": 2, "method": "Runtime.evaluate",
            "params": {"expression": "document.querySelectorAll('section.poster.xhs').length", "returnByValue": True}
        }))
        resp = json.loads(await ws.recv())
        count = resp["result"]["result"]["value"]
        print(f"Found {count} posters")
        
        for i in range(count):
            # Get poster bounding rect
            await ws.send(json.dumps({
                "id": 100+i, "method": "Runtime.evaluate",
                "params": {
                    "expression": f"""
                        JSON.stringify(document.querySelectorAll('section.poster.xhs')[{i}].getBoundingClientRect())
                    """,
                    "returnByValue": True
                }
            }))
            resp = json.loads(await ws.recv())
            rect = json.loads(resp["result"]["result"]["value"])
            
            # Screenshot with clip
            await ws.send(json.dumps({
                "id": 200+i, "method": "Page.captureScreenshot",
                "params": {
                    "format": "png",
                    "clip": {
                        "x": rect["x"], "y": rect["y"],
                        "width": rect["width"], "height": rect["height"],
                        "scale": 2
                    }
                }
            }))
            resp = json.loads(await ws.recv())
            img_data = resp["result"]["data"]
            
            path = os.path.join(OUTPUT_DIR, f"xhs-{i+1:02d}.png")
            with open(path, "wb") as f:
                f.write(base64.b64decode(img_data))
            print(f"  xhs-{i+1:02d}.png: {int(rect['width'])}x{int(rect['height'])} @2x")
    
    print("DONE")

asyncio.run(render())

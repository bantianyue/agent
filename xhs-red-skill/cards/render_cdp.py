import asyncio
import json
import os
import base64
import urllib.request
import urllib.parse
import websockets

CARDS_DIR = "D:/06_Hermes/articles/xhs-red-skill/cards"
HTML_PATH = os.path.join(CARDS_DIR, "index.html")
OUTPUT_DIR = os.path.join(CARDS_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

async def render():
    # Start a simple HTTP server in background for the HTML
    import subprocess
    server_proc = subprocess.Popen(
        ["python", "-m", "http.server", "18999", "--directory", CARDS_DIR],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    await asyncio.sleep(1)
    
    try:
        # Get CDP page WS
        resp = urllib.request.urlopen("http://localhost:9222/json")
        tabs = json.loads(resp.read())
        
        # Create new tab via PUT
        req = urllib.request.Request(
            "http://localhost:9222/json/new?" + urllib.parse.quote("http://localhost:18999/index.html", safe=''),
            method="PUT"
        )
        resp = urllib.request.urlopen(req)
        tab = json.loads(resp.read())
        page_ws = tab["webSocketDebuggerUrl"]
        
        async with websockets.connect(page_ws, max_size=10*1024*1024) as ws:
            await ws.send(json.dumps({"id": 1, "method": "Page.enable"}))
            await ws.recv()
            await asyncio.sleep(3)
            
            # Get poster count
            await ws.send(json.dumps({
                "id": 2, "method": "Runtime.evaluate",
                "params": {"expression": "document.querySelectorAll('section.poster.xhs').length", "returnByValue": True}
            }))
            resp = json.loads(await ws.recv())
            count = resp["result"]["result"]["value"]
            print(f"Found {count} posters")
            
            for i in range(count):
                # Set viewport to 1080x1440 @2x
                await ws.send(json.dumps({
                    "id": 100+i, "method": "Emulation.setDeviceMetricsOverride",
                    "params": {"width": 1080, "height": 1440, "deviceScaleFactor": 2, "mobile": False}
                }))
                await ws.recv()
                await asyncio.sleep(0.3)
                
                # Scroll to poster i
                await ws.send(json.dumps({
                    "id": 200+i, "method": "Runtime.evaluate",
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
                await asyncio.sleep(0.5)
                
                # Screenshot just this poster
                await ws.send(json.dumps({
                    "id": 300+i, "method": "Page.captureScreenshot",
                    "params": {
                        "format": "png",
                        "clip": {
                            "x": rect["x"], "y": rect["y"],
                            "width": rect["w"], "height": rect["h"],
                            "scale": 1
                        }
                    }
                }))
                resp = json.loads(await ws.recv())
                img_data = resp["result"]["data"]
                
                with open(os.path.join(OUTPUT_DIR, f"xhs-{i+1:02d}.png"), "wb") as f:
                    f.write(base64.b64decode(img_data))
                print(f"  xhs-{i+1:02d}.png: {int(rect['w'])}x{int(rect['h'])}")
            
            # Close tab
            await ws.send(json.dumps({"id": 999, "method": "Page.close"}))
            await ws.recv()
    
    finally:
        server_proc.terminate()
    
    print("DONE")

asyncio.run(render())

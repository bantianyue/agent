import asyncio
import json
import websockets

PAGE_WS = "ws://localhost:9222/devtools/page/E023609022A636D83F2C1D5F62EA2C82"

async def check_note():
    async with websockets.connect(PAGE_WS, max_size=10*1024*1024) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Page.enable"}))
        await ws.recv()
        
        # Navigate to our note
        await ws.send(json.dumps({
            "id": 2, "method": "Page.navigate",
            "params": {"url": "https://www.xiaohongshu.com/explore/6a3cd420000000000f0280d7"}
        }))
        await asyncio.sleep(5)
        
        # Check current URL
        await ws.send(json.dumps({
            "id": 3, "method": "Runtime.evaluate",
            "params": {"expression": "window.location.href", "returnByValue": True}
        }))
        resp = json.loads(await ws.recv())
        print("URL:", resp.get("result", {}).get("result", {}).get("value", "N/A"))
        
        # Get full page text
        await ws.send(json.dumps({
            "id": 4, "method": "Runtime.evaluate",
            "params": {"expression": "document.body.innerText.substring(0, 5000)", "returnByValue": True}
        }))
        resp = json.loads(await ws.recv())
        text = resp.get("result", {}).get("result", {}).get("value", "N/A")
        print("BODY TEXT:")
        print(text)

asyncio.run(check_note())

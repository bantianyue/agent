"""Try to find our note in creator studio."""
import asyncio
import json
import websockets

PAGE_WS = "ws://localhost:9222/devtools/page/E023609022A636D83F2C1D5F62EA2C82"

async def browse():
    async with websockets.connect(PAGE_WS, max_size=10*1024*1024) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Page.enable"}))
        await ws.recv()
        
        # Go to creator studio
        await ws.send(json.dumps({
            "id": 2, "method": "Page.navigate",
            "params": {"url": "https://creator.xiaohongshu.com/creator/notes"}
        }))
        await asyncio.sleep(8)
        
        # Get URL
        await ws.send(json.dumps({"id": 3, "method": "Runtime.evaluate", "params": {"expression": "window.location.href", "returnByValue": True}}))
        resp = json.loads(await ws.recv())
        print(f"URL: {resp.get('result',{}).get('result',{}).get('value','')}")
        
        # Get page text
        await ws.send(json.dumps({"id": 4, "method": "Runtime.evaluate", "params": {"expression": "document.body.innerText.substring(0, 5000)", "returnByValue": True}}))
        resp = json.loads(await ws.recv())
        text = resp.get("result",{}).get("result",{}).get("value","")
        print(f"\n=== PAGE TEXT ===")
        print(text)

asyncio.run(browse())

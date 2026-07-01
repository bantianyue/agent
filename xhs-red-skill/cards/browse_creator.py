"""Open xiaohongshu creator studio to see how topics work in the editor."""
import asyncio
import json
import websockets

PAGE_WS = "ws://localhost:9222/devtools/page/E023609022A636D83F2C1D5F62EA2C82"

async def browse():
    async with websockets.connect(PAGE_WS, max_size=10*1024*1024) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Page.enable"}))
        await ws.recv()
        
        # Go to creator studio to see our note
        await ws.send(json.dumps({
            "id": 2, "method": "Page.navigate",
            "params": {"url": "https://creator.xiaohongshu.com/publish/publish"}
        }))
        await asyncio.sleep(6)
        
        # Get page content
        await ws.send(json.dumps({"id": 3, "method": "Runtime.evaluate", "params": {"expression": "document.body.innerText.substring(0, 5000)", "returnByValue": True}}))
        resp = json.loads(await ws.recv())
        text = resp.get("result",{}).get("result",{}).get("value","")
        print("=== Creator Studio Page ===")
        print(text)

asyncio.run(browse())

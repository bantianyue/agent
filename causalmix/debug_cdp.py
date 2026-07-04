import json, asyncio, websockets, os

async def main():
    tmp = os.environ.get('TMP', 'C:\\Users\\twfehh7\\AppData\\Local\\Temp')
    with open(os.path.join(tmp, 'causalmix_tab.txt')) as f:
        tab_id = f.read().strip()
    ws_url = f"ws://localhost:9222/devtools/page/{tab_id}"
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        await asyncio.sleep(2)
        # First, extract page title to verify CDP works
        script = 'document.title'
        cmd = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": script, "returnByValue": True}}
        await ws.send(json.dumps(cmd))
        resp = json.loads(await ws.recv())
        print("Title response:", json.dumps(resp, indent=2)[:500])
        
        # Then try to list all img elements
        script2 = 'document.querySelectorAll("img").length'
        cmd2 = {"id": 2, "method": "Runtime.evaluate", "params": {"expression": script2, "returnByValue": True}}
        await ws.send(json.dumps(cmd2))
        resp2 = json.loads(await ws.recv())
        print("Img count response:", json.dumps(resp2, indent=2)[:500])

asyncio.run(main())

import json, asyncio, websockets, os

async def main():
    tmp = os.environ.get('TMP', 'C:\\Users\\twfehh7\\AppData\\Local\\Temp')
    with open(os.path.join(tmp, 'causalmix_tab.txt')) as f:
        tab_id = f.read().strip()
    ws_url = f"ws://localhost:9222/devtools/page/{tab_id}"
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        await asyncio.sleep(1)
        # Extract all text from article tag
        script = 'document.querySelector("article") ? document.querySelector("article").innerText : document.body.innerText'
        cmd = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": script, "returnByValue": True}}
        await ws.send(json.dumps(cmd))
        resp = json.loads(await ws.recv())
        text = resp["result"]["result"]["value"]
        print(text[:300])
        print("...")
        print(f"Total: {len(text)} chars")

asyncio.run(main())

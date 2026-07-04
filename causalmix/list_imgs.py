import json, asyncio, websockets, os

async def main():
    tmp = os.environ.get('TMP', 'C:\\Users\\twfehh7\\AppData\\Local\\Temp')
    with open(os.path.join(tmp, 'causalmix_tab.txt')) as f:
        tab_id = f.read().strip()
    ws_url = f"ws://localhost:9222/devtools/page/{tab_id}"
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        await asyncio.sleep(2)
        script = '''
JSON.stringify(
  Array.from(document.querySelectorAll("img"))
    .map(i => ({src: i.src.substring(0,200), w: i.naturalWidth, h: i.naturalHeight, alt: (i.alt || "").substring(0,80), cls: (i.className || "").substring(0,40)}))
)
'''
        cmd = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": script, "returnByValue": True}}
        await ws.send(json.dumps(cmd))
        resp = json.loads(await ws.recv())
        imgs = json.loads(resp["result"]["result"]["value"])
        print(f"Total images: {len(imgs)}")
        for img in imgs:
            print(f"  {img['w']}x{img['h']} | {img['alt'][:50]} | {img['src'][:120]}")

asyncio.run(main())

import json, asyncio, websockets

async def main():
    import os
    tmp = os.environ.get('TMP', 'C:\\Users\\twfehh7\\AppData\\Local\\Temp')
    with open(os.path.join(tmp, 'causalmix_tab.txt')) as f:
        tab_id = f.read().strip()
    ws_url = f"ws://localhost:9222/devtools/page/{tab_id}"
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        await asyncio.sleep(2)
        script = '''
JSON.stringify(
  Array.from(document.querySelectorAll("img[src*=\"://\"]"))
    .filter(i => !i.src.includes("profile_images") && !i.src.includes("emoji") && !i.src.includes("icon") && !i.src.includes("logo") && !i.src.includes("button") && !i.src.includes("arxiv") && !i.src.includes("static/base"))
    .map(i => ({src: i.src.split("?")[0], w: i.naturalWidth, h: i.naturalHeight, alt: (i.alt || "").substring(0,80)}))
)
'''
        cmd = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": script, "returnByValue": True}}
        await ws.send(json.dumps(cmd))
        resp = json.loads(await ws.recv())
        imgs = json.loads(resp["result"]["result"]["value"])
        print(f"Total images: {len(imgs)}")
        for img in imgs:
            ratio = img["w"] / max(img["h"], 1)
            label = "HERO" if ratio >= 2.0 else "BODY"
            print(f"{label} | {img['w']}x{img['h']} | {img['alt']} | {img['src']}")

asyncio.run(main())

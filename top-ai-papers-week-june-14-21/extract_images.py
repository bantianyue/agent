import asyncio, json, websockets

async def main():
    PAGE_WS = "ws://localhost:9222/devtools/page/59E208E32E0999BE60C2FEADF59B1867"
    async with websockets.connect(PAGE_WS, max_size=10*1024*1024) as ws:
        await asyncio.sleep(3)
        
        # Get all images
        await ws.send(json.dumps({
            "id": 1, "method": "Runtime.evaluate",
            "params": {
                "expression": "JSON.stringify(Array.from(document.querySelectorAll('img')).filter(i=>i.src&&i.naturalWidth>0).map(i=>({src:i.src,alt:i.alt,w:i.naturalWidth,h:i.naturalHeight})))",
                "returnByValue": True
            }
        }))
        resp = json.loads(await ws.recv())
        if 'result' in resp and 'result' in resp['result']:
            imgs = json.loads(resp['result']['result']['value'])
            print(f"Found {len(imgs)} images:")
            for i, img in enumerate(imgs):
                print(f"  [{i}] {img['w']}x{img['h']} | {img['alt'][:80] if img['alt'] else 'no alt'} | {img['src'][:120]}")
        else:
            print("Unexpected response:", json.dumps(resp, indent=2)[:1000])

asyncio.run(main())

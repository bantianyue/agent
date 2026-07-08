"""Get high-res images from NVIDIA Vera Rubin page."""
import asyncio, json, websockets

WS_URL = "ws://localhost:9222/devtools/page/EB1D6F465521E1826C3418675EFFCA81"

async def evaluate(ws, expr):
    msg_id = int(asyncio.get_running_loop().time() * 1000) % 100000
    await ws.send(json.dumps({"id": msg_id, "method": "Runtime.evaluate", "params": {"expression": expr}}))
    while True:
        resp = json.loads(await ws.recv())
        if resp.get("id") == msg_id:
            return resp.get("result", {}).get("result", {}).get("value")

async def get_imgs():
    async with websockets.connect(WS_URL) as ws:
        # Navigate to nvidia page
        await ws.send(json.dumps({"id": 101, "method": "Page.enable"}))
        await ws.recv()
        await ws.send(json.dumps({
            "id": 102, "method": "Page.navigate",
            "params": {"url": "https://www.nvidia.com/en-us/data-center/vera-rubin-nvl72"}
        }))
        for _ in range(50):
            resp = json.loads(await ws.recv())
            if resp.get("id") == 102:
                break
        
        await asyncio.sleep(8)
        
        # Get all images with naturalWidth > 200 (skip icons)
        big_imgs = await evaluate(ws, '''
JSON.stringify(
    Array.from(document.querySelectorAll('img'))
        .filter(i => i.naturalWidth > 200)
        .map(i => ({src: i.src, w: i.naturalWidth, h: i.naturalHeight, ratio: (i.naturalWidth/i.naturalHeight).toFixed(2)}))
)
''')
        print("=== BIG IMAGES ===")
        print(big_imgs or "[]")
        
        # Try to find hero image in srcset/picture
        hero = await evaluate(ws, '''
JSON.stringify(
    Array.from(document.querySelectorAll('picture source, img[srcset]'))
        .map(el => ({src: el.src || el.srcset, currentSrc: el.currentSrc || ''}))
)
''')
        print("\n=== PICTURE/SRCSET ===")
        print(hero or "[]")
        
        # Also try getty images
        await ws.send(json.dumps({
            "id": 103, "method": "Page.navigate",
            "params": {"url": "https://www.gettyimages.com/photos/vera-rubin?family=editorial&phrase=vera%20rubin&sort=mostpopular"}
        }))
        for _ in range(50):
            resp = json.loads(await ws.recv())
            if resp.get("id") == 103:
                break
        
        await asyncio.sleep(8)
        getty_imgs = await evaluate(ws, '''
JSON.stringify(
    Array.from(document.querySelectorAll('img[src*="gettyimages"]'))
        .filter(i => i.naturalWidth > 200)
        .map(i => ({src: i.src, w: i.naturalWidth, h: i.naturalHeight}))
        .slice(0, 10)
)
''')
        print("\n=== GETTY IMAGES ===")
        print(getty_imgs or "[]")

asyncio.run(get_imgs())

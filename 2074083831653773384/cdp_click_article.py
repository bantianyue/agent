#!/usr/bin/env python
"""Extract from existing page tab."""
import asyncio, json, websockets, sys

WS_URL = "ws://localhost:9222/devtools/page/EB1D6F465521E1826C3418675EFFCA81"

async def evaluate(ws, expr):
    msg_id = int(asyncio.get_running_loop().time() * 1000) % 100000
    await ws.send(json.dumps({"id": msg_id, "method": "Runtime.evaluate", "params": {"expression": expr}}))
    while True:
        resp = json.loads(await ws.recv())
        if resp.get("id") == msg_id:
            result = resp.get("result", {}).get("result", {})
            return result.get("value")

async def extract():
    async with websockets.connect(WS_URL) as ws:
        await asyncio.sleep(3)
        
        # Try clicking on the article link if present
        click_result = await evaluate(ws, '''
(() => {
    let links = document.querySelectorAll('a');
    for (let a of links) {
        if (a.href && a.href.includes('/i/article/')) {
            console.log("Found article link:", a.href);
            a.click();
            return "Clicked: " + a.href;
        }
    }
    return "No article link found";
})()
''')
        print("Click result:", click_result)
        await asyncio.sleep(8)
        
        # Get page text after navigation
        page_text = await evaluate(ws, "document.body.innerText")
        print("\n=== PAGE TEXT ===")
        print((page_text or "")[:10000])
        
        # Get images
        imgs = await evaluate(ws, '''
JSON.stringify(
    Array.from(document.querySelectorAll('img[src*="pbs.twimg.com/media/"]'))
        .filter(i => i.naturalWidth > 0)
        .map(i => ({src: i.src, w: i.naturalWidth, h: i.naturalHeight, ratio: (i.naturalWidth/i.naturalHeight).toFixed(2)}))
)
''')
        print("\n=== IMGS ===")
        print(imgs)

asyncio.run(extract())

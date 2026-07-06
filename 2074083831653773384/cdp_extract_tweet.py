#!/usr/bin/env python
"""Extract X tweet content via CDP Chrome WebSocket."""
import asyncio, json, websockets, urllib.request, os, sys
from urllib.parse import urlparse

WS_URL = "ws://localhost:9222/devtools/page/EB1D6F465521E1826C3418675EFFCA81"

async def evaluate(ws, expr):
    msg_id = int(asyncio.get_running_loop().time() * 1000) % 100000
    await ws.send(json.dumps({"id": msg_id, "method": "Runtime.evaluate", "params": {"expression": expr}}))
    while True:
        resp = json.loads(await ws.recv())
        if resp.get("id") == msg_id:
            result = resp.get("result", {}).get("result", {})
            if "exceptionDetails" in resp.get("result", {}):
                print(f"JS Error: {resp['result']['exceptionDetails']}", file=sys.stderr)
            return result.get("value")

async def extract_tweet():
    async with websockets.connect(WS_URL) as ws:
        # Enable domains
        await evaluate(ws, "1")
        await evaluate(ws, "2")
        
        # Navigate
        await ws.send(json.dumps({"id": 100, "method": "Page.enable"}))
        await ws.recv()
        await ws.send(json.dumps({
            "id": 101, "method": "Page.navigate",
            "params": {"url": "https://x.com/LMDFinance/status/2074083831653773384"}
        }))
        
        # Wait for navigation complete
        for _ in range(40):
            resp = json.loads(await ws.recv())
            if resp.get("id") == 101:
                break
        
        # Wait for DOM to render
        await asyncio.sleep(6)
        
        # Get tweet text - try multiple selectors
        text_expr = '''
(() => {
    let el = document.querySelector('[data-testid="tweetText"]');
    if (el) return el.innerText;
    el = document.querySelector('article');
    if (el) return el.innerText.substring(0, 20000);
    return document.body.innerText.substring(0, 20000);
})()
'''
        text = await evaluate(ws, text_expr)
        
        # Get all images with pbs.twimg
        imgs_expr = '''
JSON.stringify(
    Array.from(document.querySelectorAll('img[src*="pbs.twimg.com/media/"]'))
        .filter(i => i.naturalWidth > 0)
        .map(i => ({src: i.src, w: i.naturalWidth, h: i.naturalHeight}))
)
'''
        imgs_json = await evaluate(ws, imgs_expr)
        imgs = json.loads(imgs_json) if imgs_json else []
        
        # Check for hero/cover images (wider images)
        all_imgs_expr = '''
JSON.stringify(
    Array.from(document.querySelectorAll('img'))
        .filter(i => i.naturalWidth > 0 && i.naturalHeight > 0)
        .map(i => ({src: i.src, w: i.naturalWidth, h: i.naturalHeight}))
)
'''
        all_imgs_json = await evaluate(ws, all_imgs_expr)
        all_imgs = json.loads(all_imgs_json) if all_imgs_json else []
        
        # Get user info
        user_expr = '''
(() => {
    let el = document.querySelector('[data-testid="User-Name"]');
    if (el) return el.innerText;
    let spans = document.querySelectorAll('article span');
    for (let s of spans) {
        if (s.innerText.includes('@')) return s.innerText;
    }
    return '';
})()
'''
        user_info = await evaluate(ws, user_expr)
        
        # Get page title
        title_expr = 'document.title'
        title = await evaluate(ws, title_expr)
        
        return {
            "text": text or "",
            "user": user_info or "",
            "title": title or "",
            "imgs": imgs,
            "all_imgs": all_imgs
        }

result = asyncio.run(extract_tweet())
print(json.dumps(result, ensure_ascii=False, indent=2))

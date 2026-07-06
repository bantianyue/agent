#!/usr/bin/env python
"""Extract X Article content via CDP Chrome WebSocket."""
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

async def extract_article():
    async with websockets.connect(WS_URL) as ws:
        # Navigate
        await ws.send(json.dumps({"id": 101, "method": "Page.enable"}))
        await ws.recv()
        await ws.send(json.dumps({
            "id": 102, "method": "Page.navigate",
            "params": {"url": "https://x.com/i/article/2067208685227794432"}
        }))
        for _ in range(40):
            resp = json.loads(await ws.recv())
            if resp.get("id") == 102:
                break
        
        await asyncio.sleep(8)
        
        # Get article title
        title_expr = 'document.title'
        title = await evaluate(ws, title_expr)
        
        # Get article text - try different selectors
        text_expr = '''
(() => {
    // Try article-specific selectors
    let sel = document.querySelector('article');
    if (sel) return sel.innerText.substring(0, 30000);
    // Try main content area
    sel = document.querySelector('[data-testid="tweetText"]');
    if (sel) return sel.innerText.substring(0, 30000);
    // Try body
    return document.body.innerText.substring(0, 30000);
})()
'''
        text = await evaluate(ws, text_expr)
        
        # Get page HTML for structure analysis
        html_expr = '''
(() => {
    let article = document.querySelector('article');
    if (article) return article.innerHTML.substring(0, 50000);
    return document.body.innerHTML.substring(0, 50000);
})()
'''
        html = await evaluate(ws, html_expr)
        
        # Get all media images
        imgs_expr = '''
JSON.stringify(
    Array.from(document.querySelectorAll('img[src*="pbs.twimg.com/media/"]'))
        .filter(i => i.naturalWidth > 0)
        .map(i => ({src: i.src, w: i.naturalWidth, h: i.naturalHeight, ratio: i.naturalWidth/i.naturalHeight}))
)
'''
        imgs_json = await evaluate(ws, imgs_expr)
        imgs = json.loads(imgs_json) if imgs_json else []
        
        # Check for hero/cover images
        hero_expr = '''
JSON.stringify(
    Array.from(document.querySelectorAll('img'))
        .filter(i => i.naturalWidth > 200 && i.naturalHeight > 50)
        .map(i => ({src: i.src, w: i.naturalWidth, h: i.naturalHeight, ratio: (i.naturalWidth/i.naturalHeight).toFixed(2)}))
)
'''
        hero_json = await evaluate(ws, hero_expr)
        all_imgs = json.loads(hero_json) if hero_json else []
        
        return {
            "title": title or "",
            "text": text or "",
            "html_preview": (html or "")[:5000],
            "imgs": imgs,
            "all_imgs": all_imgs
        }

result = asyncio.run(extract_article())
print(json.dumps(result, ensure_ascii=False, indent=2))

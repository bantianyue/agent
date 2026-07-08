#!/usr/bin/env python
"""Extract X Article content via CDP - try opening tweet URL and clicking the article link."""
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

async def scroll_and_wait(ws, seconds=3):
    await evaluate(ws, "window.scrollTo(0, document.body.scrollHeight)")
    await asyncio.sleep(seconds)

async def extract():
    async with websockets.connect(WS_URL) as ws:
        # Enable domains
        await ws.send(json.dumps({"id": 1, "method": "Page.enable"}))
        await ws.recv()
        
        # Navigate to the tweet page
        await ws.send(json.dumps({
            "id": 2, "method": "Page.navigate",
            "params": {"url": "https://x.com/LMDFinance/status/2074083831653773384"}
        }))
        for _ in range(50):
            resp = json.loads(await ws.recv())
            if resp.get("id") == 2:
                break
        
        await asyncio.sleep(8)
        
        # Get the full page text
        page_text = await evaluate(ws, "document.body.innerText")
        
        # Check for article links
        article_links = await evaluate(ws, '''
(() => {
    return JSON.stringify(
        Array.from(document.querySelectorAll('a[href*="/i/article/"]'))
            .map(a => ({href: a.href, text: a.innerText.substring(0, 200)}))
    );
})()
''')
        
        # Get all tweet images 
        tweet_imgs = await evaluate(ws, '''
(() => {
    return JSON.stringify(
        Array.from(document.querySelectorAll('img[src*="pbs.twimg.com/media/"]'))
            .filter(i => i.naturalWidth > 0)
            .map(i => ({src: i.src, w: i.naturalWidth, h: i.naturalHeight}))
    );
})()
''')
        
        # Get tweet text specifically
        tweet_text = await evaluate(ws, '''
(() => {
    let el = document.querySelector('[data-testid="tweetText"]');
    if (el) return el.innerText;
    // Look for article content
    let article = document.querySelector('article');
    if (article) return article.innerText.substring(0, 30000);
    return '';
})()
''')
        
        # Get user info
        user_info = await evaluate(ws, '''
(() => {
    let el = document.querySelector('[data-testid="User-Name"]');
    if (el) return el.innerText;
    // Try finding @handle
    let spans = document.querySelectorAll('article span');
    for (let s of spans) {
        if (s.innerText && (s.innerText.includes('@') || s.innerText.includes('老马'))) 
            return s.innerText;
    }
    return '';
})()
''')
        
        return {
            "page_text": (page_text or "")[:5000],
            "tweet_text": tweet_text or "",
            "user_info": user_info or "",
            "article_links": article_links or "[]",
            "tweet_imgs": tweet_imgs or "[]"
        }

result = asyncio.run(extract())
print(json.dumps(result, ensure_ascii=False, indent=2))

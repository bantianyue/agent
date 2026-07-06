"""Check for images in X Article page."""
import asyncio, json, websockets

WS_URL = "ws://localhost:9222/devtools/page/EB1D6F465521E1826C3418675EFFCA81"

async def evaluate(ws, expr):
    msg_id = int(asyncio.get_running_loop().time() * 1000) % 100000
    await ws.send(json.dumps({"id": msg_id, "method": "Runtime.evaluate", "params": {"expression": expr}}))
    while True:
        resp = json.loads(await ws.recv())
        if resp.get("id") == msg_id:
            return resp.get("result", {}).get("result", {}).get("value")

async def extract():
    async with websockets.connect(WS_URL) as ws:
        # Check all img tags
        all_srcs = await evaluate(ws, '''
JSON.stringify(
    Array.from(document.querySelectorAll('img'))
        .map(i => ({src: i.src, w: i.naturalWidth, h: i.naturalHeight, alt: (i.alt||'').substring(0,100), complete: i.complete, visible: i.offsetParent !== null}))
)
''')
        print("=== ALL IMG TAGS ===")
        print(all_srcs or "[]")
        
        # Check for figure elements
        figs = await evaluate(ws, '''
JSON.stringify(
    Array.from(document.querySelectorAll('figure'))
        .map(f => ({html: f.innerHTML.substring(0, 200), text: (f.innerText||'').substring(0, 200)}))
)
''')
        print("\n=== FIGURE ELEMENTS ===")
        print(figs or "[]")
        
        # Check article-specific markup
        article_content = await evaluate(ws, '''
(() => {
    let el = document.querySelector('[data-testid="tweetText"]');
    if (el) return el.innerHTML.substring(0, 50000);
    return "no tweet text found";
})()
''')
        print("\n=== TWEET TEXT HTML ===")
        print((article_content or "")[:5000])

asyncio.run(extract())

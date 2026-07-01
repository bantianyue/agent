import asyncio
import json
import websockets

PAGE_WS = "ws://localhost:9222/devtools/page/F191260D7825F557EA90D9F7D0505847"

async def main():
    async with websockets.connect(PAGE_WS, max_size=10*1024*1024) as ws:
        # Wait for page ready
        await asyncio.sleep(2)
        
        # Get full page text
        await ws.send(json.dumps({
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {
                "expression": "document.body.innerText",
                "returnByValue": True
            }
        }))
        resp = await ws.recv()
        result = json.loads(resp)
        full_text = result.get("result", {}).get("result", {}).get("value", "")
        
        print("=== FULL TEXT ===")
        print(full_text[:15000])
        print("\n=== END FULL TEXT ===")
        
        # Get all images
        await ws.send(json.dumps({
            "id": 2,
            "method": "Runtime.evaluate",
            "params": {
                "expression": "JSON.stringify(Array.from(document.querySelectorAll('img')).filter(i => i.src && i.naturalWidth > 0).map(i => ({src: i.src, alt: i.alt, w: i.naturalWidth, h: i.naturalHeight})))",
                "returnByValue": True
            }
        }))
        resp = await ws.recv()
        img_result = json.loads(resp)
        imgs_json = img_result.get("result", {}).get("result", {}).get("value", "[]")
        imgs = json.loads(imgs_json)
        
        print("\n=== IMAGES ===")
        for img in imgs:
            print(f"  {img.get('w')}x{img.get('h')} | {img.get('alt','')[:80]} | {img.get('src','')}")
        
        # Get article content
        await ws.send(json.dumps({
            "id": 3,
            "method": "Runtime.evaluate",
            "params": {
                "expression": """
(function() {
    const article = document.querySelector('article');
    if (article) return article.innerText.substring(0, 30000);
    return 'NO_ARTICLE';
})()
""",
                "returnByValue": True
            }
        }))
        resp = await ws.recv()
        art_result = json.loads(resp)
        article_text = art_result.get("result", {}).get("result", {}).get("value", "")
        
        print("\n=== ARTICLE TEXT ===")
        print(article_text[:20000])
        print("\n=== END ARTICLE ===")

asyncio.run(main())

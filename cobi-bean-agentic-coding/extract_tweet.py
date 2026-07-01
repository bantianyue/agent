import asyncio
import json
import websockets
import re

TAB_ID = "F191260D7825F557EA90D9F7D0505847"
WS_URL = "ws://localhost:9222/devtools/browser/27fdf793-7a41-4479-a222-5e28e0ed0994"

async def main():
    async with websockets.connect(WS_URL, max_size=10*1024*1024) as ws:
        # Get targets
        await ws.send(json.dumps({"id": 1, "method": "Target.getTargets"}))
        resp = await ws.recv()
        targets = json.loads(resp)
        
        # Find our tab
        target_id = None
        for t in targets.get("result", {}).get("targetInfos", []):
            if "cobi_bean/status/2064848575708922093" in t.get("url", ""):
                target_id = t["targetId"]
                break
        
        if not target_id:
            print("ERROR: Target tab not found")
            return
        
        # Attach to target
        await ws.send(json.dumps({
            "id": 2,
            "method": "Target.attachToTarget",
            "params": {"targetId": target_id, "flatten": True}
        }))
        resp = await ws.recv()
        attach_result = json.loads(resp)
        session_id = attach_result.get("result", {}).get("sessionId")
        
        if not session_id:
            print("ERROR: Could not attach to target")
            return
        
        # Wait for page to be fully loaded
        await asyncio.sleep(3)
        
        # Get full page text content
        await ws.send(json.dumps({
            "id": 3,
            "sessionId": session_id,
            "method": "Runtime.evaluate",
            "params": {
                "expression": "document.body.innerText",
                "returnByValue": True
            }
        }))
        resp = await ws.recv()
        text_result = json.loads(resp)
        full_text = text_result.get("result", {}).get("result", {}).get("value", "")
        
        print("=== FULL TEXT ===")
        print(full_text[:10000])
        print("\n=== END FULL TEXT ===")
        
        # Get all images
        await ws.send(json.dumps({
            "id": 4,
            "sessionId": session_id,
            "method": "Runtime.evaluate",
            "params": {
                "expression": "JSON.stringify(Array.from(document.querySelectorAll('img[src*=\"pbs.twimg.com\"]')).map(i => ({src: i.src, alt: i.alt, w: i.naturalWidth, h: i.naturalHeight})))",
                "returnByValue": True
            }
        }))
        resp = await ws.recv()
        img_result = json.loads(resp)
        imgs_json = img_result.get("result", {}).get("result", {}).get("value", "[]")
        imgs = json.loads(imgs_json)
        
        print("\n=== IMAGES ===")
        for img in imgs:
            print(f"  {img.get('w')}x{img.get('h')} | {img.get('alt','')[:60]} | {img.get('src','')}")
        
        # Get article content specifically (for X articles)
        await ws.send(json.dumps({
            "id": 5,
            "sessionId": session_id,
            "method": "Runtime.evaluate",
            "params": {
                "expression": """
(function() {
    // Try to find article content
    const article = document.querySelector('article');
    if (article) return article.innerText.substring(0, 20000);
    return 'NO_ARTICLE_FOUND';
})()
""",
                "returnByValue": True
            }
        }))
        resp = await ws.recv()
        article_result = json.loads(resp)
        article_text = article_result.get("result", {}).get("result", {}).get("value", "")
        
        print("\n=== ARTICLE TEXT ===")
        print(article_text[:15000])
        print("\n=== END ARTICLE ===")

asyncio.run(main())

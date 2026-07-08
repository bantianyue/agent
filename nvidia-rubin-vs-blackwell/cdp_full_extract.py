#!/usr/bin/env python
"""Extract full text and images from the loaded X Article page."""
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
        # Full page text
        full_text = await evaluate(ws, "document.body.innerText")
        
        # Expanded image search - try various selectors
        all_imgs = await evaluate(ws, '''
JSON.stringify(
    Array.from(document.querySelectorAll('img'))
        .filter(i => i.naturalWidth > 0 && !i.src.includes('emoji') && !i.src.includes('logo'))
        .map(i => ({src: i.src, w: i.naturalWidth, h: i.naturalHeight, ratio: (i.naturalWidth/i.naturalHeight).toFixed(2)}))
)
''')
        
        # Check for div background images
        bg_img_els = await evaluate(ws, '''
(() => {
    // Look for article content images in div backgrounds
    let els = document.querySelectorAll('[style*="background-image"], [style*="background"], figure img, img:not([src*="emoji"])');
    let results = [];
    els.forEach(el => {
        let src = el.src || '';
        let bg = window.getComputedStyle(el).backgroundImage || '';
        if (src && !src.includes('emoji') && !src.includes('logo') && !src.includes('svg')) {
            results.push({src: src, w: el.naturalWidth, h: el.naturalHeight});
        }
    });
    return JSON.stringify(results);
})()
''')
        
        # Check article content structure
        article_html = await evaluate(ws, '''
(() => {
    // Find the main article content
    let article = document.querySelector('article');
    if (article) return article.innerHTML.substring(0, 80000);
    // Try other selectors
    let main = document.querySelector('main');
    if (main) return main.innerHTML.substring(0, 80000);
    return document.body.innerHTML.substring(0, 80000);
})()
''')
        
        print("=== FULL TEXT ===")
        print(full_text or "")
        
        print("\n=== IMAGES (all) ===")
        print(all_imgs or "[]")
        
        print("\n=== BACKGROUND IMAGES ===")
        print(bg_img_els or "[]")
        
        # Save full text
        if full_text:
            with open('full_text.txt', 'w', encoding='utf-8') as f:
                f.write(full_text)
            print(f"\nSaved full_text.txt ({len(full_text)} chars)")

asyncio.run(extract())

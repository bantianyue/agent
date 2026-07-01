import asyncio, json, websockets, base64, os

PAGE_WS = 'ws://localhost:9222/devtools/page/A4E36D16A56D515C9E65F79DB438032E'
SAVE_DIR = 'D:/06_Hermes/articles/8-interview-winning-answers'

PROMPT = '''Generate a 2.35:1 WeChat public account cover image for an article titled 'AI面试15问，他用一套框架通杀'.

The article teaches 15 interview frameworks:
1. Frame Control (why are you leaving)
2. Introduction Pivot (tell me about yourself)
3. Weakness Trap (biggest weakness)
4. Take-Home Pushback
5. Tech Stack Agnosticism
6. Why Us Reversal
7. System Design Boundaries
8. Behavioral Metrics
9. Manager Alignment
10. Incident Response Audit
11. Scope Clarification
12. Competing Offer Leverage
13. Promotion Pathway
14. Tech Debt Reality
15. Two-Way Interview Mindset

Design requirements:
- Dark navy/charcoal background, modern tech recruiting aesthetic
- Show 'AI面试' and '15' prominently
- Use gold/amber color for highlights
- Clean, professional visual style
- 2.35:1 aspect ratio (suitable for 900x383)
- Minimalist corporate design with subtle interview/tech iconography
'''

async def main():
    async with websockets.connect(PAGE_WS, max_size=20*1024*1024) as ws:
        await asyncio.sleep(3)
        
        # 1. Set download path
        await ws.send(json.dumps({
            'id': 1, 'method': 'Page.setDownloadBehavior',
            'params': {'behavior': 'allow', 'downloadPath': SAVE_DIR}
        }))
        await ws.recv()
        print('[1] Download path set')
        
        # 2. Clear contenteditable
        await ws.send(json.dumps({
            'id': 2, 'method': 'Runtime.evaluate',
            'params': {'expression': '''
(function() {
    const el = document.querySelector('[contenteditable="true"]');
    if (!el) return 'not found';
    el.focus();
    el.textContent = '';
    return 'cleared';
})()
            ''', 'returnByValue': True}
        }))
        resp = json.loads(await ws.recv())
        print(f'[2] Clear: {resp.get("result",{}).get("result",{}).get("value","?")}')
        await asyncio.sleep(1)
        
        # 3. Insert text
        await ws.send(json.dumps({
            'id': 3, 'method': 'Input.insertText',
            'params': {'text': PROMPT}
        }))
        await ws.recv()
        print('[3] Text inserted')
        await asyncio.sleep(2)
        
        # 4. Send with Enter
        await ws.send(json.dumps({
            'id': 4, 'method': 'Input.dispatchKeyEvent',
            'params': {'type': 'keyDown', 'key': 'Enter', 'windowsVirtualKeyCode': 13}
        }))
        await ws.recv()
        await ws.send(json.dumps({
            'id': 5, 'method': 'Input.dispatchKeyEvent',
            'params': {'type': 'keyUp', 'key': 'Enter', 'windowsVirtualKeyCode': 13}
        }))
        await ws.recv()
        print('[4] Sent! Waiting for generation...')
        
        # 5. Wait for generation
        for i in range(3):
            print(f'[5] Waiting... ({i+1}/3 chunks of 20s)')
            await asyncio.sleep(20)
            
            # Check for images
            await ws.send(json.dumps({
                'id': 10+i, 'method': 'Runtime.evaluate',
                'params': {'expression': '''
JSON.stringify(Array.from(document.querySelectorAll('img')).filter(i => i.naturalWidth > 100).map(i => ({w: i.naturalWidth, h: i.naturalHeight, blob: i.src.startsWith('blob')})))
                ''', 'returnByValue': True}
            }))
            resp = json.loads(await ws.recv())
            imgs = json.loads(resp.get('result',{}).get('result',{}).get('value','[]'))
            if imgs:
                print(f'  Found {len(imgs)} images, largest: {max(i["w"] for i in imgs)}x{max(i["h"] for i in imgs)}')
                if any(i['w'] >= 500 for i in imgs):
                    print('  Large image detected!')
                    break
        
        await asyncio.sleep(10)  # extra wait for finish
        
        # 6. Try download button first
        await ws.send(json.dumps({
            'id': 20, 'method': 'Runtime.evaluate',
            'params': {'expression': '''
(function() {
    const btns = document.querySelectorAll('button');
    for (const btn of btns) {
        const label = btn.getAttribute('aria-label') || '';
        if (label.includes('下载') || label.includes('Download') || label.includes('full') || label.includes('complete')) {
            btn.click();
            return 'clicked: ' + label.substring(0,60);
        }
    }
    return 'no download btn';
})()
            ''', 'returnByValue': True}
        }))
        resp = json.loads(await ws.recv())
        print(f'[6] Download btn: {resp.get("result",{}).get("result",{}).get("value","?")}')
        await asyncio.sleep(5)
        
        # 7. Canvas-to-dataURL as primary method
        print('[7] Trying canvas-to-dataURL...')
        await ws.send(json.dumps({
            'id': 25, 'method': 'Runtime.evaluate',
            'params': {
                'expression': '''
(async () => {
    const imgs = Array.from(document.querySelectorAll('img')).filter(i => i.naturalWidth > 100);
    if (imgs.length === 0) return null;
    // Pick the largest image
    const img = imgs.reduce((a, b) => a.naturalWidth * a.naturalHeight > b.naturalWidth * b.naturalHeight ? a : b);
    const c = document.createElement('canvas');
    c.width = img.naturalWidth;
    c.height = img.naturalHeight;
    const ctx = c.getContext('2d');
    ctx.drawImage(img, 0, 0);
    return c.toDataURL('image/png');
})()
                ''',
                'returnByValue': True,
                'awaitPromise': True
            }
        }))
        resp = json.loads(await ws.recv())
        data_url = resp.get('result', {}).get('result', {}).get('value', '')
        
        if data_url and data_url.startswith('data:'):
            b64 = data_url.split(',')[1]
            img_data = base64.b64decode(b64)
            save_path = os.path.join(SAVE_DIR, 'gemini_cover.png')
            with open(save_path, 'wb') as f:
                f.write(img_data)
            print(f'[7] Saved: {save_path} ({len(img_data)} bytes, {len(img_data)/1024:.0f}KB)')
        else:
            print(f'[7] Canvas failed: data_url starts with data:={data_url.startswith("data:") if data_url else "empty"}')

asyncio.run(main())

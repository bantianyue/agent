import asyncio, json, websockets, base64, os

PAGE_WS = 'ws://localhost:9222/devtools/page/A4E36D16A56D515C9E65F79DB438032E'
SAVE_DIR = 'D:/06_Hermes/articles/8-interview-winning-answers'

PROMPT = '''Generate a WeChat public account cover image (900x383 pixels, 2.35:1) for a tech interview article.

The cover must include these elements:
- Bold large text at top: "你为什么离职？"
- Below it: "Top AI企业面试秘籍"
- Display the logos/names of these famous AI companies: OpenAI, Anthropic, Google, DeepSeek (as small brand logos or stylized text along the bottom)
- Show "15" as a prominent number

Design requirements:
- Dark navy/charcoal background
- Gold/amber and blue highlights
- Clean professional corporate design
- AI / tech interview theme
- The company names should be visible as visual brand elements
- 2.35:1 aspect ratio
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
        
        # 5. Wait for generation - check periodically
        for i in range(4):
            print(f'[5] Waiting... ({i+1}/4 of 20s)')
            await asyncio.sleep(20)
            
            await ws.send(json.dumps({
                'id': 10+i, 'method': 'Runtime.evaluate',
                'params': {'expression': '''
JSON.stringify(Array.from(document.querySelectorAll('img')).filter(i => i.naturalWidth > 100).map(i => ({w: i.naturalWidth, h: i.naturalHeight, blob: i.src.startsWith('blob')})))
                ''', 'returnByValue': True}
            }))
            resp = json.loads(await ws.recv())
            imgs = json.loads(resp.get('result',{}).get('result',{}).get('value','[]'))
            if imgs:
                max_w = max(i['w'] for i in imgs)
                max_h = max(i['h'] for i in imgs)
                print(f'  Found {len(imgs)} images, largest: {max_w}x{max_h}')
                if max_w >= 600:
                    print('  Good size!')
                    break
        
        await asyncio.sleep(5)
        
        # 6. Try download button
        await ws.send(json.dumps({
            'id': 20, 'method': 'Runtime.evaluate',
            'params': {'expression': '''
(function() {
    const btns = document.querySelectorAll('button');
    for (const btn of btns) {
        const label = btn.getAttribute('aria-label') || '';
        if (label.includes('下载') || label.includes('Download') || label.includes('full')) {
            btn.click();
            return 'clicked: ' + label.substring(0,60);
        }
    }
    return 'no download btn';
})()
            ''', 'returnByValue': True}
        }))
        resp = json.loads(await ws.recv())
        print(f'[6] Download: {resp.get("result",{}).get("result",{}).get("value","?")}')
        await asyncio.sleep(5)
        
        # 7. Canvas-to-dataURL
        print('[7] Canvas-to-dataURL...')
        await ws.send(json.dumps({
            'id': 25, 'method': 'Runtime.evaluate',
            'params': {
                'expression': '''
(async () => {
    const imgs = Array.from(document.querySelectorAll('img')).filter(i => i.naturalWidth > 100);
    if (imgs.length === 0) return null;
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
            print(f'[7] OK: {len(img_data)} bytes, {len(img_data)/1024:.0f}KB')
        else:
            print(f'[7] Failed')

asyncio.run(main())

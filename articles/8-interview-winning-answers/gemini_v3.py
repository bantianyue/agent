import asyncio, json, websockets, base64, os

PAGE_WS = 'ws://localhost:9222/devtools/page/D986BE898FAA12015CF3A4E860E7726D'
SAVE_DIR = 'D:/06_Hermes/articles/8-interview-winning-answers'

PROMPT = '''Generate a WeChat public account cover image (900x383, 2.35:1) for an interview article.

Must include visually:
- Bold headline "你为什么离职？"
- Subtitle "Top AI企业面试秘籍"
- Number "15" prominently
- Company logos/names: OpenAI, Anthropic, Google, DeepSeek as brand elements at bottom

Dark navy/charcoal background, gold/amber highlights, clean corporate tech design. 2.35:1 aspect ratio.
'''

async def fast_check(ws):
    await ws.send(json.dumps({'id':99,'method':'Runtime.evaluate','params':{'expression':'JSON.stringify(Array.from(document.querySelectorAll(\"img\")).filter(i=>i.naturalWidth>100).map(i=>({w:i.naturalWidth,h:i.naturalHeight})))','returnByValue':True}}))
    resp = json.loads(await ws.recv())
    return json.loads(resp.get('result',{}).get('result',{}).get('value','[]'))

async def main():
    async with websockets.connect(PAGE_WS, max_size=20*1024*1024) as ws:
        await asyncio.sleep(2)
        
        # Set download path
        await ws.send(json.dumps({'id':1,'method':'Page.setDownloadBehavior','params':{'behavior':'allow','downloadPath':SAVE_DIR}}))
        await ws.recv()
        
        # Clear
        await ws.send(json.dumps({'id':2,'method':'Runtime.evaluate','params':{'expression':'(function(){const el=document.querySelector(\"[contenteditable=true]\");if(!el)return\"not found\";el.focus();el.textContent=\"\";return\"cleared\";})()','returnByValue':True}}))
        resp = json.loads(await ws.recv())
        print('Clear:', resp.get('result',{}).get('result',{}).get('value'))
        await asyncio.sleep(1)
        
        # Insert
        await ws.send(json.dumps({'id':3,'method':'Input.insertText','params':{'text':PROMPT}}))
        await ws.recv()
        await asyncio.sleep(1)
        
        # Send
        await ws.send(json.dumps({'id':4,'method':'Input.dispatchKeyEvent','params':{'type':'keyDown','key':'Enter','windowsVirtualKeyCode':13}}))
        await ws.recv()
        await ws.send(json.dumps({'id':5,'method':'Input.dispatchKeyEvent','params':{'type':'keyUp','key':'Enter','windowsVirtualKeyCode':13}}))
        await ws.recv()
        print('Sent!')
        
        # Poll every 5s for images, exit early when found
        found = False
        for i in range(30):  # up to 150s
            await asyncio.sleep(5)
            imgs = await fast_check(ws)
            if imgs:
                max_w = max(i['w'] for i in imgs)
                max_h = max(i['h'] for i in imgs)
                print(f'  {i*5+5}s: {len(imgs)} imgs, largest {max_w}x{max_h}')
                if max_w >= 400:
                    found = True
                    break
            if i % 6 == 0:
                print(f'  {i*5+5}s: checking...')
        
        if not found:
            print('No image found after 150s')
            return
        
        await asyncio.sleep(5)
        
        # Canvas-to-dataURL
        await ws.send(json.dumps({
            'id': 50, 'method': 'Runtime.evaluate',
            'params': {
                'expression': '''
(async () => {
    const imgs = Array.from(document.querySelectorAll('img')).filter(i => i.naturalWidth > 100);
    if (imgs.length === 0) return null;
    const img = imgs.reduce((a,b) => a.naturalWidth*a.naturalHeight > b.naturalWidth*b.naturalHeight ? a : b);
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
        data_url = resp.get('result',{}).get('result',{}).get('value','')
        
        if data_url and data_url.startswith('data:'):
            b64 = data_url.split(',')[1]
            img_data = base64.b64decode(b64)
            path = os.path.join(SAVE_DIR, 'gemini_cover.png')
            with open(path, 'wb') as f:
                f.write(img_data)
            print(f'Saved: {len(img_data)} bytes, {len(img_data)/1024:.0f}KB')
        else:
            print(f'Canvas failed')

asyncio.run(main())

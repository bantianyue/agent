import asyncio, json, websockets, base64, os

PAGE_WS = 'ws://localhost:9222/devtools/page/440BD9A43C168FA0909DAFAFACEC4778'
SAVE_DIR = 'D:/06_Hermes/articles/8-interview-winning-answers'

PROMPT = 'create an image for a WeChat cover. Title: "你为什么离职？" Subtitle: "Top AI企业面试秘籍". Include company logos of OpenAI, Anthropic, Google, DeepSeek. Dark blue background, tech style. 2.35:1 aspect ratio. Show number 15 prominently.'

async def main():
    async with websockets.connect(PAGE_WS, max_size=20*1024*1024) as ws:
        await asyncio.sleep(5)
        
        # Check if loaded
        await ws.send(json.dumps({'id':0,'method':'Runtime.evaluate','params':{'expression':'document.title + " | " + (document.querySelector("[contenteditable=true]") ? "ready" : "loading")','returnByValue':True}}))
        resp = json.loads(await ws.recv())
        print('Status:', resp.get('result',{}).get('result',{}).get('value',''))
        
        if 'loading' in str(resp):
            await asyncio.sleep(8)
        
        # Set download path
        await ws.send(json.dumps({'id':1,'method':'Page.setDownloadBehavior','params':{'behavior':'allow','downloadPath':SAVE_DIR}}))
        await ws.recv()
        
        # Focus and clear input
        await ws.send(json.dumps({'id':2,'method':'Runtime.evaluate','params':{'expression':'''
(function(){
    const el = document.querySelector('[contenteditable="true"]');
    if(!el) return 'no input';
    el.focus();
    el.textContent = '';
    return 'cleared';
})()
        ''','returnByValue':True}}))
        resp = json.loads(await ws.recv())
        c = resp.get('result',{}).get('result',{}).get('value','')
        print(f'Input: {c}')
        await asyncio.sleep(1)
        
        # Insert prompt text
        await ws.send(json.dumps({'id':3,'method':'Input.insertText','params':{'text':PROMPT}}))
        await ws.recv()
        print('Text inserted')
        await asyncio.sleep(1)
        
        # Press Enter to send
        await ws.send(json.dumps({'id':4,'method':'Input.dispatchKeyEvent','params':{'type':'keyDown','key':'Enter','windowsVirtualKeyCode':13}}))
        await ws.recv()
        await ws.send(json.dumps({'id':5,'method':'Input.dispatchKeyEvent','params':{'type':'keyUp','key':'Enter','windowsVirtualKeyCode':13}}))
        await ws.recv()
        print('Sent! Waiting for image...')
        
        # Poll for images every 3 seconds (faster check)
        for i in range(50):
            await asyncio.sleep(3)
            await ws.send(json.dumps({'id':10+i,'method':'Runtime.evaluate','params':{'expression':'JSON.stringify(Array.from(document.querySelectorAll(\"img\")).filter(i=>i.naturalWidth>100).map(i=>({w:i.naturalWidth,h:i.naturalHeight})))','returnByValue':True}}))
            resp = json.loads(await ws.recv())
            imgs = json.loads(resp.get('result',{}).get('result',{}).get('value','[]'))
            
            big = [x for x in imgs if x['w'] >= 400]
            if big:
                best = max(big, key=lambda x: x['w']*x['h'])
                print(f'GOT IMAGE at {(i+1)*3}s: {best["w"]}x{best["h"]}')
                
                # Canvas save
                await ws.send(json.dumps({'id':50,'method':'Runtime.evaluate','params':{'expression':'(async()=>{const imgs=Array.from(document.querySelectorAll(\"img\")).filter(i=>i.naturalWidth>100);if(!imgs.length)return null;const img=imgs.reduce((a,b)=>a.naturalWidth*a.naturalHeight>b.naturalWidth*b.naturalHeight?a:b);const c=document.createElement(\"canvas\");c.width=img.naturalWidth;c.height=img.naturalHeight;c.getContext(\"2d\").drawImage(img,0,0);return c.toDataURL(\"image/png\");})()','returnByValue':True,'awaitPromise':True}}))
                resp = json.loads(await ws.recv())
                du = resp.get('result',{}).get('result',{}).get('value','')
                if du.startswith('data:'):
                    b = base64.b64decode(du.split(',')[1])
                    p = os.path.join(SAVE_DIR, 'gemini_cover.png')
                    with open(p,'wb') as f:
                        f.write(b)
                    print(f'Saved: {len(b)} bytes ({len(b)/1024:.0f}KB)')
                return
            
            if i % 5 == 0:
                sizes = [f'{x["w"]}x{x["h"]}' for x in imgs]
                print(f'  {(i+1)*3}s: checking ({len(imgs)} imgs: {", ".join(sizes)})')
        
        print('No image generated')

asyncio.run(main())

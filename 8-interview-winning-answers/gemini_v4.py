import asyncio, json, websockets, base64, os

PAGE_WS = 'ws://localhost:9222/devtools/page/58FBF2ECB7A1D4A2FA33AD20E807C1EB'
SAVE_DIR = 'D:/06_Hermes/articles/8-interview-winning-answers'

PROMPT = '''Generate a WeChat public account cover image (900x383, 2.35:1) for an interview article.

Must include visually:
- Bold headline "你为什么离职？"
- Subtitle "Top AI企业面试秘籍"  
- Number "15" prominently
- Company names/logos: OpenAI, Anthropic, Google, DeepSeek as brand elements at bottom

Dark navy/charcoal background, gold/amber highlights, clean corporate tech design.
'''

async def main():
    async with websockets.connect(PAGE_WS, max_size=20*1024*1024) as ws:
        await asyncio.sleep(2)
        
        # Navigate to a fresh app page first (new conversation)
        await ws.send(json.dumps({'id':0,'method':'Page.navigate','params':{'url':'https://gemini.google.com/app'}}))
        await ws.recv()
        print('Navigating to fresh Gemini...')
        await asyncio.sleep(5)
        
        # Set download path
        await ws.send(json.dumps({'id':1,'method':'Page.setDownloadBehavior','params':{'behavior':'allow','downloadPath':SAVE_DIR}}))
        await ws.recv()
        
        # Clear
        await ws.send(json.dumps({'id':2,'method':'Runtime.evaluate','params':{'expression':'(function(){const el=document.querySelector("[contenteditable=true]");if(!el)return"NF";el.focus();el.textContent="";return"OK";})()','returnByValue':True}}))
        resp = json.loads(await ws.recv())
        print('Clear:', resp.get('result',{}).get('result',{}).get('value'))
        await asyncio.sleep(1)
        
        # Insert
        await ws.send(json.dumps({'id':3,'method':'Input.insertText','params':{'text':PROMPT}}))
        await ws.recv()
        await asyncio.sleep(1)
        
        # Submit
        await ws.send(json.dumps({'id':4,'method':'Input.dispatchKeyEvent','params':{'type':'keyDown','key':'Enter','windowsVirtualKeyCode':13}}))
        await ws.recv()
        await ws.send(json.dumps({'id':5,'method':'Input.dispatchKeyEvent','params':{'type':'keyUp','key':'Enter','windowsVirtualKeyCode':13}}))
        await ws.recv()
        print('Submitted, waiting...')
        
        # Quick poll
        for i in range(24):
            await asyncio.sleep(5)
            await ws.send(json.dumps({'id':10+i,'method':'Runtime.evaluate','params':{'expression':'JSON.stringify(Array.from(document.querySelectorAll(\"img\")).filter(i=>i.naturalWidth>100).map(i=>({w:i.naturalWidth,h:i.naturalHeight})))','returnByValue':True}}))
            resp = json.loads(await ws.recv())
            imgs = json.loads(resp.get('result',{}).get('result',{}).get('value','[]'))
            large = [x for x in imgs if x['w'] >= 400]
            if large:
                print(f'Found large image at {(i+1)*5}s: {large[0]["w"]}x{large[0]["h"]}')
                
                # Canvas save
                await ws.send(json.dumps({'id':50,'method':'Runtime.evaluate','params':{'expression':'(async()=>{const imgs=Array.from(document.querySelectorAll(\"img\")).filter(i=>i.naturalWidth>100);const img=imgs.reduce((a,b)=>a.naturalWidth*a.naturalHeight>b.naturalWidth*b.naturalHeight?a:b);const c=document.createElement(\"canvas\");c.width=img.naturalWidth;c.height=img.naturalHeight;c.getContext(\"2d\").drawImage(img,0,0);return c.toDataURL(\"image/png\");})()','returnByValue':True,'awaitPromise':True}}))
                resp = json.loads(await ws.recv())
                du = resp.get('result',{}).get('result',{}).get('value','')
                if du.startswith('data:'):
                    b = base64.b64decode(du.split(',')[1])
                    with open(os.path.join(SAVE_DIR,'gemini_cover.png'),'wb') as f:
                        f.write(b)
                    print(f'Saved: {len(b)} bytes, {len(b)/1024:.0f}KB')
                return
            
            if i % 6 == 0:
                print(f'  {(i+1)*5}s: no large image yet ({len(imgs)} small imgs)')
        
        print('Timed out without large image')

asyncio.run(main())

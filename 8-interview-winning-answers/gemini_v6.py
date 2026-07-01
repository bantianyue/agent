import asyncio, json, websockets, base64, os

PAGE_WS = 'ws://localhost:9222/devtools/page/DBA90C9F7980D20E50301426774B45AD'
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
        
        await ws.send(json.dumps({'id':0,'method':'Runtime.evaluate','params':{'expression':'JSON.stringify({title:document.title,url:window.location.href})','returnByValue':True}}))
        resp = json.loads(await ws.recv())
        info = json.loads(resp.get('result',{}).get('result',{}).get('value','{}'))
        print(f'URL: {info.get("url","")[:80]}')
        
        await ws.send(json.dumps({'id':1,'method':'Page.setDownloadBehavior','params':{'behavior':'allow','downloadPath':SAVE_DIR}}))
        await ws.recv()
        
        await ws.send(json.dumps({'id':2,'method':'Runtime.evaluate','params':{'expression':'(function(){const el=document.querySelector("[contenteditable=true]");if(!el)return"NF";el.focus();el.textContent="";return"OK";})()','returnByValue':True}}))
        resp = json.loads(await ws.recv())
        print('Clear:', resp.get('result',{}).get('result',{}).get('value'))
        await asyncio.sleep(1)
        
        await ws.send(json.dumps({'id':3,'method':'Input.insertText','params':{'text':PROMPT}}))
        await ws.recv()
        await asyncio.sleep(1)
        
        await ws.send(json.dumps({'id':4,'method':'Input.dispatchKeyEvent','params':{'type':'keyDown','key':'Enter','windowsVirtualKeyCode':13}}))
        await ws.recv()
        await ws.send(json.dumps({'id':5,'method':'Input.dispatchKeyEvent','params':{'type':'keyUp','key':'Enter','windowsVirtualKeyCode':13}}))
        await ws.recv()
        print('Sent!')
        
        for i in range(30):
            await asyncio.sleep(5)
            await ws.send(json.dumps({'id':10+i,'method':'Runtime.evaluate','params':{'expression':'JSON.stringify(Array.from(document.querySelectorAll(\"img\")).filter(i=>i.naturalWidth>100).map(i=>({w:i.naturalWidth,h:i.naturalHeight})))','returnByValue':True}}))
            resp = json.loads(await ws.recv())
            imgs = json.loads(resp.get('result',{}).get('result',{}).get('value','[]'))
            large = [x for x in imgs if x['w'] >= 400]
            if large:
                best = max(large, key=lambda x: x['w']*x['h'])
                print(f'GOT IMAGE at {(i+1)*5}s: {best["w"]}x{best["h"]}')
                await ws.send(json.dumps({'id':50,'method':'Runtime.evaluate','params':{'expression':'(async()=>{const imgs=Array.from(document.querySelectorAll(\"img\")).filter(i=>i.naturalWidth>100);if(!imgs.length)return null;const img=imgs.reduce((a,b)=>a.naturalWidth*a.naturalHeight>b.naturalWidth*b.naturalHeight?a:b);const c=document.createElement(\"canvas\");c.width=img.naturalWidth;c.height=img.naturalHeight;c.getContext(\"2d\").drawImage(img,0,0);return c.toDataURL(\"image/png\");})()','returnByValue':True,'awaitPromise':True}}))
                resp = json.loads(await ws.recv())
                du = resp.get('result',{}).get('result',{}).get('value','')
                if du.startswith('data:'):
                    b = base64.b64decode(du.split(',')[1])
                    p = os.path.join(SAVE_DIR, 'gemini_cover.png')
                    with open(p,'wb') as f:
                        f.write(b)
                    print(f'Saved: {len(b)} bytes, {len(b)/1024:.0f}KB')
                return
            if i % 4 == 0:
                print(f'  {(i+1)*5}s: {len(imgs)} small imgs')

asyncio.run(main())

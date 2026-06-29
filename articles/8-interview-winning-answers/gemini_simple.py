import asyncio, json, websockets, base64, os

PAGE_WS = 'ws://localhost:9222/devtools/page/440BD9A43C168FA0909DAFAFACEC4778'
SAVE_DIR = 'D:/06_Hermes/articles/8-interview-winning-answers'

async def main():
    async with websockets.connect(PAGE_WS, max_size=30*1024*1024) as ws:
        await asyncio.sleep(2)
        
        # Set download path
        await ws.send(json.dumps({'id':1,'method':'Page.setDownloadBehavior','params':{'behavior':'allow','downloadPath':SAVE_DIR}}))
        await ws.recv()
        
        # Clear and send simpler prompt
        await ws.send(json.dumps({'id':2,'method':'Runtime.evaluate','params':{'expression':'(function(){const el=document.querySelector("[contenteditable=true]");if(!el)return;el.focus();el.textContent="";return 1;})()','returnByValue':True}}))
        await ws.recv()
        await asyncio.sleep(1)
        
        await ws.send(json.dumps({'id':3,'method':'Input.insertText','params':{'text':'Create a simple dark blue tech cover image for a WeChat article about AI interviews. Just a clean tech background with the text "AI面试" on it. 2.35:1 ratio.'}}))
        await ws.recv()
        await asyncio.sleep(1)
        
        await ws.send(json.dumps({'id':4,'method':'Input.dispatchKeyEvent','params':{'type':'keyDown','key':'Enter','windowsVirtualKeyCode':13}}))
        await ws.recv()
        await ws.send(json.dumps({'id':5,'method':'Input.dispatchKeyEvent','params':{'type':'keyUp','key':'Enter','windowsVirtualKeyCode':13}}))
        await ws.recv()
        print('Sent simple prompt')
        
        for i in range(40):
            await asyncio.sleep(5)
            await ws.send(json.dumps({'id':10+i,'method':'Runtime.evaluate','params':{'expression':'''
(function(){
    const imgs = Array.from(document.querySelectorAll("img")).filter(i => i.naturalWidth > 100);
    const text = document.body.innerText;
    const creating = text.includes("正在创建") || text.includes("Creating");
    const hasResponse = text.includes("Gemini 说") || text.includes("Here") || text.includes("这是我");
    return JSON.stringify({count: imgs.length, sizes: imgs.map(i=>i.naturalWidth+"x"+i.naturalHeight), creating, hasResponse});
})()
            ''','returnByValue':True}}))
            resp = json.loads(await ws.recv())
            val = json.loads(resp.get('result',{}).get('result',{}).get('value','{}'))
            
            print(f'  {(i+1)*5}s: {val}')
            
            if val.get('count',0) > 0:
                await asyncio.sleep(3)
                # Canvas save
                await ws.send(json.dumps({'id':50,'method':'Runtime.evaluate','params':{'expression':'(async()=>{const imgs=Array.from(document.querySelectorAll(\"img\")).filter(i=>i.naturalWidth>100);if(!imgs.length)return null;const img=imgs.reduce((a,b)=>a.naturalWidth*a.naturalHeight>b.naturalWidth*b.naturalHeight?a:b);const c=document.createElement(\"canvas\");c.width=img.naturalWidth;c.height=img.naturalHeight;c.getContext(\"2d\").drawImage(img,0,0);return c.toDataURL(\"image/png\");})()','returnByValue':True,'awaitPromise':True}}))
                resp = json.loads(await ws.recv())
                du = resp.get('result',{}).get('result',{}).get('value','')
                if du.startswith('data:'):
                    b = base64.b64decode(du.split(',')[1])
                    p = os.path.join(SAVE_DIR, 'gemini_cover.png')
                    with open(p,'wb') as f:
                        f.write(b)
                    print(f'SAVED: {len(b)} bytes ({len(b)/1024:.0f}KB)')
                return

asyncio.run(main())

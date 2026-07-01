import asyncio, json, websockets, base64, os

PAGE_WS = 'ws://localhost:9222/devtools/page/440BD9A43C168FA0909DAFAFACEC4778'
SAVE_DIR = 'D:/06_Hermes/articles/8-interview-winning-answers'

async def main():
    async with websockets.connect(PAGE_WS, max_size=30*1024*1024) as ws:
        await asyncio.sleep(2)
        
        # Keep polling until we find a loaded image or 180s
        for i in range(60):
            await asyncio.sleep(3)
            
            await ws.send(json.dumps({'id':i,'method':'Runtime.evaluate','params':{'expression':'''
(function(){
    const imgs = Array.from(document.querySelectorAll("img")).filter(i => i.naturalWidth > 100);
    const blobs = Array.from(document.querySelectorAll("img[src*=\\"blob\\"]"));
    const text = document.body.innerText;
    const creating = text.includes("正在创建") || text.includes("Creating");
    return JSON.stringify({
        count: imgs.length,
        largest: imgs.length > 0 ? Math.max(...imgs.map(i => i.naturalWidth)) + "x" + Math.max(...imgs.map(i => i.naturalHeight)) : "none",
        blobs: blobs.length,
        creating: creating,
        hasResponse: text.includes("Gemini 说") && !creating
    });
})()
            ''','returnByValue':True}}))
            resp = json.loads(await ws.recv())
            val = json.loads(resp.get('result',{}).get('result',{}).get('value','{}'))
            
            if val.get('count',0) > 0 and not val.get('creating',True):
                print(f'IMAGE READY at {(i+1)*3}s: {val.get("largest")}')
                
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
            
            if i % 5 == 0:
                status = 'creating' if val.get('creating') else 'waiting'
                print(f'  {(i+1)*3}s: {status}, imgs={val.get("count")}, blobs={val.get("blobs")}')
        
        print('TIMEOUT')

asyncio.run(main())

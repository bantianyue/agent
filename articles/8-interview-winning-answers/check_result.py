import asyncio, json, websockets, base64, os

PAGE_WS = 'ws://localhost:9222/devtools/page/440BD9A43C168FA0909DAFAFACEC4778'
SAVE_DIR = 'D:/06_Hermes/articles/8-interview-winning-answers'

async def main():
    async with websockets.connect(PAGE_WS, max_size=30*1024*1024) as ws:
        await asyncio.sleep(2)
        
        # Wait a fixed amount for generation to finish
        print('Waiting 60s for Gemini to finish generating...')
        await asyncio.sleep(60)
        
        # Check page status
        await ws.send(json.dumps({'id':1,'method':'Runtime.evaluate','params':{'expression':'document.body.innerText.substring(0,500)','returnByValue':True}}))
        resp = json.loads(await ws.recv())
        text = resp.get('result',{}).get('result',{}).get('value','')
        print(f'Status: {text[:300]}')
        
        # Find ALL images, including those with zero naturalWidth but has src
        await ws.send(json.dumps({'id':2,'method':'Runtime.evaluate','params':{'expression':'''
JSON.stringify({
    allImgs: Array.from(document.querySelectorAll("img")).map(i => ({
        w: i.naturalWidth,
        h: i.naturalHeight,
        src: (i.src || "").substring(0, 100),
        hasSrc: !!i.src
    })),
    withBg: Array.from(document.querySelectorAll("[style*=\\"background\\"]")).filter(e => {
        const s = e.style.backgroundImage || e.style.background || "";
        return s.includes("url") || s.includes("blob");
    }).length,
    canvasCount: document.querySelectorAll("canvas").length
})
        ''','returnByValue':True}}))
        resp = json.loads(await ws.recv())
        data = json.loads(resp.get('result',{}).get('result',{}).get('value','{}'))
        
        print(f'Canvas elements: {data.get("canvasCount",0)}')
        print(f'Elements with bg image: {data.get("withBg",0)}')
        print(f'All img tags: {len(data.get("allImgs",[]))}')
        
        imgs = data.get('allImgs', [])
        big = [i for i in imgs if i['w'] > 300 or 'blob' in i.get('src','')]
        if big:
            print(f'Found {len(big)} interesting images:')
            for i in big:
                print(f'  {i["w"]}x{i["h"]} src={i["src"][:80]}')
        else:
            print('Small imgs only:')
            for i in imgs[:5]:
                print(f'  {i["w"]}x{i["h"]} src={i["src"][:60]}')
        
        # Try to get all images via blob URL extraction
        await ws.send(json.dumps({'id':3,'method':'Runtime.evaluate','params':{'expression':'''
JSON.stringify(Array.from(document.querySelectorAll("img[src*=\\"blob\\"]")).map(i => ({
    w: i.naturalWidth,
    h: i.naturalHeight,
    srcLen: (i.src || "").length
})))
        ''','returnByValue':True}}))
        resp = json.loads(await ws.recv())
        blobs = json.loads(resp.get('result',{}).get('result',{}).get('value','[]'))
        print(f'Blob images: {len(blobs)}')
        for b in blobs:
            print(f'  {b}')

asyncio.run(main())

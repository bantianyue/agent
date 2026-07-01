import asyncio, json, websockets

PAGE_WS = 'ws://localhost:9222/devtools/page/440BD9A43C168FA0909DAFAFACEC4778'

async def main():
    async with websockets.connect(PAGE_WS, max_size=20*1024*1024) as ws:
        await asyncio.sleep(2)
        
        # Get full page text
        await ws.send(json.dumps({'id':1,'method':'Runtime.evaluate','params':{'expression':'document.body.innerText','returnByValue':True}}))
        resp = json.loads(await ws.recv())
        text = resp.get('result',{}).get('result',{}).get('value','')
        print(text[:2000])

asyncio.run(main())

import asyncio, json, websockets

PAGE_WS = 'ws://localhost:9222/devtools/page/58FBF2ECB7A1D4A2FA33AD20E807C1EB'

async def main():
    async with websockets.connect(PAGE_WS, max_size=20*1024*1024) as ws:
        await asyncio.sleep(2)
        
        # Check page content
        await ws.send(json.dumps({'id':1,'method':'Runtime.evaluate','params':{'expression':'document.body.innerText.substring(0,1000)','returnByValue':True}}))
        resp = json.loads(await ws.recv())
        text = resp.get('result',{}).get('result',{}).get('value','')
        print('=== Page content (first 1000 chars) ===')
        print(text[:1000])
        print()
        
        # Check for login/signup elements
        await ws.send(json.dumps({'id':2,'method':'Runtime.evaluate','params':{'expression':'JSON.stringify({login: !!document.querySelector(\"[href*=\\\"sign\\\"]\"), signin: document.body.innerText.includes(\"Sign in\"), signup: document.body.innerText.includes(\"Sign up\"), chat: !!(document.querySelector(\"[contenteditable=true]\") && document.querySelector(\"[contenteditable=true]\").offsetHeight > 0) })','returnByValue':True}}))
        resp = json.loads(await ws.recv())
        print('Status:', resp.get('result',{}).get('result',{}).get('value',''))

asyncio.run(main())

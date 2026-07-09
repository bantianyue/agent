import os, json, asyncio, urllib.request, time
os.environ['no_proxy']='localhost,127.0.0.1'; os.environ['NO_PROXY']='localhost,127.0.0.1'
BASE=r'D:\06_Hermes\articles\test'
import websockets

ver=json.loads(urllib.request.urlopen('http://localhost:9222/json/version',timeout=5).read())
ws_url=ver['webSocketDebuggerUrl']

async def run(name, url):
    t0=time.time()
    async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
        # create a new target tab (reuse browser context => keeps login cookies)
        await ws.send(json.dumps({"id":1,"method":"Target.createTarget","params":{"url":"about:blank"}}))
        rep=json.loads(await ws.recv())
        target_id=rep['result']['targetId']
        # get target ws
        targets=json.loads(urllib.request.urlopen('http://localhost:9222/json/targets',timeout=5).read())
        tws=None
        for t in targets:
            if t['targetId']==target_id:
                tws=t['webSocketDebuggerUrl']; break
        print(name,'tab created', round(time.time()-t0,1))
        async with websockets.connect(tws, max_size=50*1024*1024) as tw:
            await tw.send(json.dumps({"id":1,"method":"Page.enable","params":{}})); await tw.recv()
            await tw.send(json.dumps({"id":2,"method":"Page.navigate","params":{"url":url}}))
            await asyncio.sleep(4)
            # scroll
            for _ in range(10):
                await tw.send(json.dumps({"id":3,"method":"Runtime.evaluate","params":{"expression":"window.scrollBy(0,1200)","awaitPromise":False}}))
                await asyncio.sleep(0.5)
            await asyncio.sleep(1)
            # extract
            await tw.send(json.dumps({"id":10,"method":"Runtime.evaluate","params":{"expression":"document.title","returnByValue":True}}))
            title=json.loads(await tw.recv())['result']['result']['value']
            await tw.send(json.dumps({"id":11,"method":"Runtime.evaluate","params":{"expression":"document.body.innerText","returnByValue":True}}))
            text=json.loads(await tw.recv())['result']['result']['value']
            exp='''(()=>{const els=[...document.querySelectorAll('img')].filter(e=>e.src.includes('pbs.twimg.com')&&!e.src.includes('profile_images')&&e.naturalWidth>0);return els.map(e=>({s:e.src,w:e.naturalWidth,h:e.naturalHeight}));})()'''
            await tw.send(json.dumps({"id":12,"method":"Runtime.evaluate","params":{"expression":exp,"returnByValue":True}}))
            imgs=json.loads(await tw.recv())['result']['result']['value']
            d=os.path.join(BASE,name); os.makedirs(d,exist_ok=True)
            open(os.path.join(d,'text.txt'),'w',encoding='utf-8').write(text)
            urls=[o['s'] for o in imgs]
            heroes=[o['s'] for o in imgs if o['w'] and o['h'] and o['w']/o['h']>=2.0]
            open(os.path.join(d,'imgs.txt'),'w',encoding='utf-8').write('\n'.join(urls))
            open(os.path.join(d,'hero.txt'),'w',encoding='utf-8').write('\n'.join(heroes))
            print(name,'TITLE:',title[:40],'TEXT_LEN',len(text),'PBS_IMGS',len(urls),'HERO',len(heroes),round(time.time()-t0,1),'s')
            # close target
            await ws.send(json.dumps({"id":99,"method":"Target.closeTarget","params":{"targetId":target_id}}))

async def main():
    await run('x_sergio','https://x.com/SergioPaniego/status/2074863503312044499')
    await run('x_christine','https://x.com/christinexzhu/status/2074847461588267466')
asyncio.run(main())
print('DONE')

import asyncio, json, os
os.environ["NO_PROXY"]="localhost,127.0.0.1"
import websockets
PAGE_WS="ws://localhost:9222/devtools/page/226240C84F15C702D43DACEC659A9C46"
async def main():
    async with websockets.connect(PAGE_WS, max_size=20*1024*1024, ping_interval=None) as ws:
        c=[0]
        async def send(m,p=None,wp=False):
            c[0]+=1
            await ws.send(json.dumps({"id":c[0],"method":m,"params":p or {},**({"awaitPromise":True,"returnByValue":True} if wp else {})}))
            while True:
                r=json.loads(await ws.recv())
                if r.get("id")==c[0]: return r
        r=await send("Runtime.evaluate",{"expression":'JSON.stringify({url:location.href, title:document.title, ce:!!document.querySelector(\'[contenteditable="true"]\'), btns:document.querySelectorAll("button").length, imgs:document.querySelectorAll("img").length})'},True)
        print(r.get("result",{}).get("result",{}).get("value"))
asyncio.run(main())

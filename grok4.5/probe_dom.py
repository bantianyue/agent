import asyncio, json, os
os.environ["NO_PROXY"]="localhost,127.0.0.1"
import websockets
PAGE_WS="ws://localhost:9222/devtools/page/226240C84F15C702D43DACEC659A9C46"
async def main():
    async with websockets.connect(PAGE_WS, max_size=30*1024*1024, ping_interval=None) as ws:
        c=[0]
        async def send(m,p=None,wp=False):
            c[0]+=1
            params=dict(p or {})
            if wp: params.update({"awaitPromise":True,"returnByValue":True})
            await ws.send(json.dumps({"id":c[0],"method":m,"params":params}))
            while True:
                r=json.loads(await ws.recv())
                if r.get("id")==c[0]: return r
        r=await send("Runtime.evaluate",{"expression":'JSON.stringify(Array.from(document.querySelectorAll("img")).map(function(i){return {src:i.src.substring(0,40),w:i.naturalWidth,h:i.naturalHeight};}))'},True)
        print("RAW:",r.get("result",{}).get("result",{}).get("value"))
        r2=await send("Runtime.evaluate",{"expression":'JSON.stringify(Array.from(document.querySelectorAll("*")).filter(function(e){var s=getComputedStyle(e).backgroundImage;return s && s.indexOf("blob")>=0;}).slice(0,5).map(function(e){return getComputedStyle(e).backgroundImage.substring(0,80);}))'},True)
        print("BG:",r2.get("result",{}).get("result",{}).get("value"))
asyncio.run(main())

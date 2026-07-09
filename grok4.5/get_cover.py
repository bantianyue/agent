import asyncio, json, os, base64
os.environ["NO_PROXY"]="localhost,127.0.0.1"
import websockets
PAGE_WS="ws://localhost:9222/devtools/page/226240C84F15C702D43DACEC659A9C46"
SAVE="D:/06_Hermes/articles/grok4.5/gemini_cover.png"
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
        for attempt in range(4):
            r=await send("Runtime.evaluate",{"expression":'(async()=>{var imgs=Array.from(document.querySelectorAll("img")).filter(function(i){return i.src.indexOf("blob")===0 && i.naturalWidth>300;});if(!imgs.length)return null;var img=imgs[0];var c=document.createElement("canvas");c.width=img.naturalWidth;c.height=img.naturalHeight;var ctx=c.getContext("2d");ctx.drawImage(img,0,0);return c.toDataURL("image/png");})()'},True)
            val=r.get("result",{}).get("result",{}).get("value","")
            if val and val.startswith("data:"):
                b64=val.split(",",1)[1]
                data=base64.b64decode(b64)
                open(SAVE,"wb").write(data)
                print("SAVED",len(data),"bytes")
                return
            print("attempt",attempt,"empty, retry")
            await asyncio.sleep(3)
asyncio.run(main())

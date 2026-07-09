import asyncio, json, os
os.environ["NO_PROXY"]="localhost,127.0.0.1"
os.environ["no_proxy"]="localhost,127.0.0.1"
import websockets

PAGE_WS="ws://localhost:9222/devtools/page/226240C84F15C702D43DACEC659A9C46"
PROMPT="Generate a cinematic 2.35:1 wide promotional banner (900x383) celebrating a tech comeback. Elon Musk stands confidently at center, arms crossed, with a subtle smirk, wearing a dark jacket. Behind him a glowing Grok 4.5 logo and a large upward trending bar chart rising steeply. Visual metaphors: a chess king piece knocking over rival pieces, a rocket lift-off streak, a performance gauge pinned to MAX. Color palette: deep space navy and black background, electric amber/gold and cyan neon accents. Modern, triumphant, high-contrast tech aesthetic. No readable text."

async def main():
    async with websockets.connect(PAGE_WS, max_size=20*1024*1024, ping_interval=None) as ws:
        c=[0]
        async def send(m,p=None,wp=False):
            c[0]+=1
            await ws.send(json.dumps({"id":c[0],"method":m,"params":p or {},**({"awaitPromise":True,"returnByValue":True} if wp else {})}))
            while True:
                r=json.loads(await ws.recv())
                if r.get("id")==c[0]:
                    return r
        r=await send("Runtime.evaluate",{"expression":'(function(){var el=document.querySelector(\'[contenteditable="true"]\');if(!el)return "no";el.focus();el.textContent="";return "cleared";})()'},True)
        print("clear:",r.get("result",{}).get("result",{}).get("value"))
        await asyncio.sleep(1)
        await send("Input.insertText",{"text":PROMPT})
        await asyncio.sleep(1)
        await send("Input.dispatchKeyEvent",{"type":"keyDown","key":"Enter","windowsVirtualKeyCode":13})
        await send("Input.dispatchKeyEvent",{"type":"keyUp","key":"Enter","windowsVirtualKeyCode":13})
        print("sent, waiting 55s...")
        await asyncio.sleep(55)
        r=await send("Runtime.evaluate",{"expression":'JSON.stringify(Array.from(document.querySelectorAll("img")).filter(function(i){return i.naturalWidth>100;}).map(function(i){return {src:i.src.substring(0,60),w:i.naturalWidth,h:i.naturalHeight};}))'},True)
        print("imgs:",r.get("result",{}).get("result",{}).get("value"))
asyncio.run(main())

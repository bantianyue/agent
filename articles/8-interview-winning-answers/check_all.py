import asyncio, json, websockets

async def check_tab(ws_url, label):
    try:
        async with websockets.connect(ws_url, max_size=10*1024*1024, close_timeout=5) as ws:
            await asyncio.sleep(2)
            await ws.send(json.dumps({'id':1,'method':'Runtime.evaluate','params':{'expression':'document.title + " | input:" + (!!document.querySelector("[contenteditable=true]")) + " | imgs:" + document.querySelectorAll("img").length + " | url:" + window.location.href.substring(0,80)','returnByValue':True}}))
            resp = json.loads(await ws.recv())
            print(f'{label}: {resp.get("result",{}).get("result",{}).get("value","?")}')
    except Exception as e:
        print(f'{label}: ERROR {e}')

async def main():
    tabs = [
        ('ws://localhost:9222/devtools/page/58FBF2ECB7A1D4A2FA33AD20E807C1EB', 'SOUL.md'),
        ('ws://localhost:9222/devtools/page/D986BE898FAA12015CF3A4E860E7726D', 'FRESH'),
        ('ws://localhost:9222/devtools/page/DBA90C9F7980D20E50301426774B45AD', 'AI Loop'),
    ]
    await asyncio.gather(*(check_tab(u, l) for u, l in tabs))

asyncio.run(main())

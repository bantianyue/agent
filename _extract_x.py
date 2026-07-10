import asyncio, json, websockets, urllib.request, sys

TWEET_URL = "https://x.com/SergioPaniego/status/2074863503312044499"

async def send_recv(ws, msg, want_id):
    await ws.send(json.dumps(msg))
    while True:
        r = json.loads(await ws.recv())
        if r.get('id') == want_id:
            return r

async def main():
    req = urllib.request.Request("http://127.0.0.1:9222/json/version")
    with urllib.request.urlopen(req, timeout=10) as r:
        version = json.loads(r.read())
    browser_ws = version["webSocketDebuggerUrl"].replace("localhost", "127.0.0.1")
    async with websockets.connect(browser_ws, proxy=None) as ws:
        r = await send_recv(ws, {"id":1,"method":"Target.createTarget","params":{"url":TWEET_URL,"newWindow":False}}, 1)
        target_id = r["result"]["targetId"]
        r = await send_recv(ws, {"id":2,"method":"Target.attachToTarget","params":{"targetId":target_id,"flatten":True}}, 2)
        session_id = r["result"]["sessionId"]
        await asyncio.sleep(18)
        def ev(e,eid): return {"id":eid,"sessionId":session_id,"method":"Runtime.evaluate","params":{"expression":e,"returnByValue":True}}
        r = await send_recv(ws, ev("document.title",3),3)
        print("TITLE:", r["result"]["result"]["value"], file=sys.stderr)
        r = await send_recv(ws, ev("""(()=>{const a=[...document.querySelectorAll('article')];for(const x of a){if(x.querySelector('a[href*="/status/2074863503312044499"]'))return x.innerText.substring(0,800);}return (a[0]?a[0].innerText.substring(0,800):'NO');})()""",5),5)
        print("===TWEET_HEAD==="); print(r["result"]["result"]["value"][:400])
        r = await send_recv(ws, ev("""(()=>{const imgs=[...document.querySelectorAll('img[src*="pbs.twimg.com/media/"]')].filter(i=>!i.src.includes('profile_images'));return JSON.stringify(imgs.map(i=>i.src));})()""",6),6)
        print("===IMGS==="); print(r["result"]["result"]["value"])

asyncio.run(main())

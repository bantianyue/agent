import asyncio, json, websockets, sys

TWEET_URL = "https://x.com/SergioPaniego/status/2074863503312044499"

async def send_recv(ws, msg, want_id):
    await ws.send(json.dumps(msg))
    while True:
        r = json.loads(await ws.recv())
        if r.get('id') == want_id:
            return r

async def main():
    import urllib.request
    req = urllib.request.Request("http://localhost:9222/json/version",
                                 headers={"Host":"localhost"})
    with urllib.request.urlopen(req, timeout=10) as r:
        version = json.loads(r.read())
    browser_ws = version["webSocketDebuggerUrl"]
    print("BWS:", browser_ws, file=sys.stderr)

    async with websockets.connect(browser_ws) as ws:
        # open tab via Target.createTarget (browser-level, loose origin)
        r = await send_recv(ws, {"id":1,"method":"Target.createTarget",
                                 "params":{"url":TWEET_URL,"newWindow":False}}, 1)
        target_id = r["result"]["targetId"]
        print("TARGET:", target_id, file=sys.stderr)
        r = await send_recv(ws, {"id":2,"method":"Target.attachToTarget",
                                 "params":{"targetId":target_id,"flatten":True}}, 2)
        session_id = r["result"]["sessionId"]
        print("SESSION:", session_id, file=sys.stderr)
        await asyncio.sleep(18)
        def ev(expression, eid):
            return {"id":eid,"sessionId":session_id,"method":"Runtime.evaluate",
                    "params":{"expression":expression,"returnByValue":True}}
        r = await send_recv(ws, ev("document.title",3), 3)
        print("TITLE:", r["result"]["result"]["value"], file=sys.stderr)
        r = await send_recv(ws, ev("""(() => {
            const spans = Array.from(document.querySelectorAll('span'));
            for (const s of spans) {
                if (s.textContent === '显示原文' || s.textContent === 'Show original') { s.click(); return 'CLICKED'; }
            }
            return 'NO_TOGGLE';
        })()""",4), 4)
        print("TOGGLE:", r["result"]["result"]["value"], file=sys.stderr)
        await asyncio.sleep(2)
        r = await send_recv(ws, ev("""(() => {
            const articles = Array.from(document.querySelectorAll('article'));
            for (const a of articles) {
                const link = a.querySelector('a[href*="/status/2074863503312044499"]');
                if (link) return a.innerText.substring(0, 4000);
            }
            return (articles[0] ? articles[0].innerText.substring(0,4000) : 'NO_ARTICLE');
        })()""",5), 5)
        print("===TWEET_TEXT===")
        print(r["result"]["result"]["value"])
        r = await send_recv(ws, ev("""(() => {
            const imgs = Array.from(document.querySelectorAll('img[src*="pbs.twimg.com/media/"]'))
                .filter(i => !i.src.includes('profile_images'));
            const out = [];
            for (const img of imgs) {
                let cap = ''; let el = img.parentElement;
                for (let k=0; k<6; k++) {
                    if (!el) break;
                    const t = (el.textContent||'').replace(/\\s+/g,' ').trim();
                    if (t.length > cap.length) cap = t;
                    if (t.length > 40) break;
                    el = el.parentElement;
                }
                out.push({src: img.src, w: img.naturalWidth, h: img.naturalHeight, cap: cap.substring(0,300)});
            }
            return JSON.stringify(out);
        })()""",6), 6)
        print("===IMAGES_JSON===")
        print(r["result"]["result"]["value"])
        r = await send_recv(ws, ev("""(() => {
            const all = Array.from(document.querySelectorAll('img')).filter(i=>i.src.includes('twimg.com'));
            return JSON.stringify(all.map(i=>({src:i.src, w:i.naturalWidth, h:i.naturalHeight})));
        })()""",7), 7)
        print("===ALL_TWIMG===")
        print(r["result"]["result"]["value"])

asyncio.run(main())

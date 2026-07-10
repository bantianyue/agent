import asyncio, json, websockets, urllib.request, sys

TWEET_URL = "https://x.com/SergioPaniego/status/2074863503312044499"
LOGIN_TAB_WS = "ws://localhost:9222/devtools/page/AD0C9C7BF24777FBD279"

async def send_recv(ws, msg, want_id):
    await ws.send(json.dumps(msg))
    while True:
        r = json.loads(await ws.recv())
        if r.get('id') == want_id:
            return r
        # skip events

async def main():
    # 1. open new tab from logged-in tab
    async with websockets.connect(LOGIN_TAB_WS) as ws:
        r = await send_recv(ws, {"id":1,"method":"Target.createTarget","params":{"url":TWEET_URL,"newWindow":False}}, 1)
        target_id = r["result"]["targetId"]
        print("TARGET:", target_id, file=sys.stderr)
    # 2. connect to new tab
    new_ws = f"ws://localhost:9222/devtools/page/{target_id}"
    async with websockets.connect(new_ws) as ws:
        await asyncio.sleep(18)
        # title check
        r = await send_recv(ws, {"id":2,"method":"Runtime.evaluate","params":{"expression":"document.title","returnByValue":True}}, 2)
        title = r["result"]["result"]["value"]
        print("TITLE:", title, file=sys.stderr)
        # click show original if translated
        r = await send_recv(ws, {"id":3,"method":"Runtime.evaluate","params":{"expression":"""(() => {
            const spans = Array.from(document.querySelectorAll('span'));
            for (const s of spans) {
                if (s.textContent === '显示原文' || s.textContent === 'Show original') { s.click(); return 'CLICKED'; }
            }
            return 'NO_TOGGLE';
        })()""","returnByValue":True}}, 3)
        print("TOGGLE:", r["result"]["result"]["value"], file=sys.stderr)
        await asyncio.sleep(2)
        # extract single main tweet text (the root article)
        r = await send_recv(ws, {"id":4,"method":"Runtime.evaluate","params":{"expression":"""(() => {
            const articles = Array.from(document.querySelectorAll('article'));
            // the main tweet article is the first one with the status id in its permalink
            for (const a of articles) {
                const link = a.querySelector('a[href*="/status/2074863503312044499"]');
                if (link) {
                    const txt = a.innerText;
                    return txt.substring(0, 4000);
                }
            }
            return (articles[0] ? articles[0].innerText.substring(0,4000) : 'NO_ARTICLE');
        })()""","returnByValue":True}}, 4)
        text = r["result"]["result"]["value"]
        print("===TWEET_TEXT===")
        print(text)
        # extract images with captions - bind img + preceding text node in same DOM walk
        r = await send_recv(ws, {"id":5,"method":"Runtime.evaluate","params":{"expression":"""(() => {
            const imgs = Array.from(document.querySelectorAll('img[src*="pbs.twimg.com/media/"]'))
                .filter(i => !i.src.includes('profile_images'));
            const out = [];
            for (const img of imgs) {
                // find nearest ancestor that holds a text node sibling (caption)
                let cap = '';
                let el = img.parentElement;
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
        })()""","returnByValue":True}}, 5)
        imgs = r["result"]["result"]["value"]
        print("===IMAGES_JSON===")
        print(imgs)
        # also check for hero / any other twimg
        r = await send_recv(ws, {"id":6,"method":"Runtime.evaluate","params":{"expression":"""(() => {
            const all = Array.from(document.querySelectorAll('img')).filter(i=>i.src.includes('twimg.com'));
            return JSON.stringify(all.map(i=>({src:i.src, w:i.naturalWidth, h:i.naturalHeight})));
        })()""","returnByValue":True}}, 6)
        print("===ALL_TWIMG===")
        print(r["result"]["result"]["value"])

asyncio.run(main())

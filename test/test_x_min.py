import os, json, urllib.request, asyncio, time
from playwright.async_api import async_playwright
os.environ['no_proxy']='localhost,127.0.0.1'
os.environ['NO_PROXY']='localhost,127.0.0.1'
ver=json.loads(urllib.request.urlopen('http://localhost:9222/json/version',timeout=5).read())
ws=ver['webSocketDebuggerUrl']
url='https://x.com/SergioPaniego/status/2074863503312044499'
t0=time.time()
async def main():
    async with async_playwright() as p:
        print('connecting cdp...', round(time.time()-t0,1))
        browser=await p.chromium.connect_over_cdp(ws)
        print('connected ctxs', len(browser.contexts), round(time.time()-t0,1))
        ctx=browser.contexts[0]
        pg=await ctx.new_page()
        print('new_page ok', round(time.time()-t0,1))
        await pg.goto(url,wait_until='domcontentloaded',timeout=45000)
        print('goto done', round(time.time()-t0,1))
        await pg.wait_for_timeout(2000)
        title=await pg.title()
        txt=await pg.evaluate('()=>document.body.innerText')
        imgs=await pg.eval_on_selector_all('img','els=>els.map(e=>e.src).filter(s=>s&&s.includes("pbs.twimg.com")&&!s.includes("profile_images"))')
        print('TITLE:',title[:50])
        print('TEXT_LEN',len(txt),'IMGS',len(imgs))
        await pg.close(); await browser.close()
    print('total', round(time.time()-t0,1))
asyncio.run(main())
print('OK')

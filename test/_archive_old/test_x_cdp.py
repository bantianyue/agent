import os, json, asyncio, urllib.request, time
os.environ['no_proxy']='localhost,127.0.0.1'; os.environ['NO_PROXY']='localhost,127.0.0.1'
BASE=r'D:\06_Hermes\articles\test'
import websockets

def get_tabs():
    return json.loads(urllib.request.urlopen('http://localhost:9222/json',timeout=5).read())

def find_x_tab():
    tabs=get_tabs()
    # pick a page tab whose title looks logged-in (not just the URL path)
    for t in tabs:
        if t.get('type')=='page' and 'x.com' in t.get('url','') and t.get('webSocketDebuggerUrl'):
            # prefer one whose title contains an @username (logged in)
            title=t.get('title','')
            if '@' in title:
                return t
    # fallback any x page tab
    for t in tabs:
        if t.get('type')=='page' and 'x.com' in t.get('url','') and t.get('webSocketDebuggerUrl'):
            return t
    return None

async def send_recv(tw, msg_id, method, params=None):
    await tw.send(json.dumps({"id":msg_id,"method":method,"params":params or {}}))
    while True:
        rep=json.loads(await tw.recv())
        if rep.get('id')==msg_id:
            return rep

async def run(name, url):
    t0=time.time()
    tab=find_x_tab()
    if not tab:
        print(name,'NO LOGGED-IN X TAB'); return
    tws=tab['webSocketDebuggerUrl']
    print(name,'reuse tab:',tab['title'][:30], round(time.time()-t0,1))
    async with websockets.connect(tws, max_size=50*1024*1024) as tw:
        await send_recv(tw,1,"Page.enable")
        await send_recv(tw,2,"Page.navigate",{"url":url})
        await asyncio.sleep(5)
        for _ in range(10):
            await send_recv(tw,3,"Runtime.evaluate",{"expression":"window.scrollBy(0,1200)","awaitPromise":False})
            await asyncio.sleep(0.5)
        await asyncio.sleep(1)
        title=await send_recv(tw,10,"Runtime.evaluate",{"expression":"document.title","returnByValue":True})
        title=title['result']['result']['value']
        text=await send_recv(tw,11,"Runtime.evaluate",{"expression":"document.body.innerText","returnByValue":True})
        text=text['result']['result']['value']
        exp='''(()=>{const els=[...document.querySelectorAll('img')].filter(e=>e.src.includes('pbs.twimg.com')&&!e.src.includes('profile_images')&&e.naturalWidth>0);return els.map(e=>({s:e.src,w:e.naturalWidth,h:e.naturalHeight}));})()'''
        imgs=await send_recv(tw,12,"Runtime.evaluate",{"expression":exp,"returnByValue":True})
        imgs=imgs['result']['result']['value']
        d=os.path.join(BASE,name); os.makedirs(d,exist_ok=True)
        open(os.path.join(d,'text.txt'),'w',encoding='utf-8').write(text)
        urls=[o['s'] for o in imgs]
        heroes=[o['s'] for o in imgs if o['w'] and o['h'] and o['w']/o['h']>=2.0]
        open(os.path.join(d,'imgs.txt'),'w',encoding='utf-8').write('\n'.join(urls))
        open(os.path.join(d,'hero.txt'),'w',encoding='utf-8').write('\n'.join(heroes))
        print(name,'TITLE:',title[:40],'TEXT_LEN',len(text),'PBS_IMGS',len(urls),'HERO',len(heroes),round(time.time()-t0,1),'s')

async def main():
    await run('x_sergio','https://x.com/SergioPaniego/status/2074863503312044499')
    await run('x_christine','https://x.com/christinexzhu/status/2074847461588267466')
asyncio.run(main())
print('DONE')

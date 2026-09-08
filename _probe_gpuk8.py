# -*- coding: utf-8 -*-
import json,time,sys
from playwright.sync_api import sync_playwright
URL=sys.argv[1]; NAME=sys.argv[2]
hits=[]
def on_resp(resp):
    try:
        u=resp.url
        if 'graphql' not in u and 'api' not in u and 'article' not in u.lower(): return
        ct=resp.headers.get('content-type','') or ''
        if 'json' not in ct and 'text' not in ct: return
        txt=resp.text()
        if not txt: return
        if ('pbs.twimg.com/media' in txt) or ('media_entities' in txt) or ('HRq' in txt) or ('mediaEntities' in txt):
            hits.append({'url':u[:200],'len':len(txt),'txt':txt})
    except Exception as e:
        pass
res={}
with sync_playwright() as p:
    b=p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx=b.contexts[0] if b.contexts else b.new_context()
    pg=ctx.new_page()
    pg.on('response', on_resp)
    got=False
    for attempt in range(6):
        try:
            pg.goto(URL, wait_until="commit", timeout=100000)
            time.sleep(20)
            got=True; break
        except Exception as e:
            print('attempt',attempt,'err',str(e)[:100]); time.sleep(6+attempt*6)
    if got:
        # scroll to trigger lazy article part loads
        try:
            for _ in range(30):
                try: pg.mouse.wheel(0,2000)
                except: break
                time.sleep(0.4)
            time.sleep(8)
        except Exception: pass
    res['hits']=hits
    try: pg.close()
    except: pass
json.dump(res,open(rf"D:/06_Hermes/articles/_probe8_{NAME}.json",'w',encoding='utf8'),ensure_ascii=False)
print('hits',len(hits))
for h in hits:
    print('URL',h['url'])
    print('LEN',h['len'])
    # print regions around pbs URLs
    import re
    for m in re.finditer(r'pbs\.twimg\.com/media/([A-Za-z0-9_-]+)', h['txt']):
        pass
    meds=sorted(set(re.findall(r'HRq[A-Za-z0-9_-]+', h['txt'])))
    print('  mediaIds found:',meds[:40])
    i=h['txt'].find('media_entities')
    if i<0: i=h['txt'].find('mediaEntities')
    if i>=0: print('  media_entities ctx:',h['txt'][max(0,i-200):i+300][:500])

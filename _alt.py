# -*- coding: utf-8 -*-
import json,time,re,sys
from playwright.sync_api import sync_playwright
URL=sys.argv[1]
with sync_playwright() as p:
    b=p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx=b.contexts[0] if b.contexts else b.new_context()
    pg=ctx.new_page()
    res=[]
    try:
        pg.goto(URL, wait_until="commit", timeout=60000)
        time.sleep(15)
        res=pg.evaluate("""()=>{
          const r=[];
          for(const el of document.querySelectorAll('img[src]')){
            const u=el.currentSrc||el.src||''; if(!u) continue;
            if(/profile_images|_normal|emoji/i.test(u)) continue;
            const w=el.naturalWidth||el.width||0, h=el.naturalHeight||el.height||0;
            if(w<500) continue;
            r.push({id:(u.split('?')[0].split('/').pop()||u), alt:(el.alt||'').trim(), w,w, hh:h});
          }
          return r;
        }""")
    except Exception as e:
        res=[{'err':str(e)[:150]}]
    finally:
        try: pg.close()
        except: pass
seen=[]; had=set()
for o in res:
    if 'err' in o: print('ERR',o['err']); continue
    if o['id'] in had: continue
    had.add(o['id']); seen.append(o)
for i,o in enumerate(seen):
    print(f"[{i}] {o['id'][:22]:24} {o.get('w')} alt={o.get('alt','')[:90]}")

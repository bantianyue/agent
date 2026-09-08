# -*- coding: utf-8 -*-
import json
from playwright.sync_api import sync_playwright
URL="https://x.com/TheVixhal/status/2097008871231672595"
out={}
with sync_playwright() as p:
    b=p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx=b.contexts[0] if b.contexts else b.new_context()
    pg=ctx.new_page()
    try:
        pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
        pg.wait_for_timeout(9000)
        # detect login wall / content
        title=pg.title()[:80]
        # scroll to bottom to trigger lazy loads
        height=pg.evaluate("document.body?document.body.scrollHeight:0")
        for _ in range(40):
            pg.evaluate("window.scrollBy(0, 900)")
            pg.wait_for_timeout(600)
            nv=pg.evaluate("window.scrollY")
            mh=pg.evaluate("document.body?document.body.scrollHeight:0")
            if nv>= (mh-1600):
                pg.wait_for_timeout(1500); break
        pg.wait_for_timeout(3000)
        # collect images
        info=pg.evaluate("""()=>{
          const out=[];
          const set=new Set();
          const q=document.querySelectorAll('img[src], img[srcset]');
          for(const el of q){
            let u=(el.currentSrc||el.src||''); 
            if(!u) continue;
            if(/profile_images|emoji|_normal|/i.test(u)) continue;
            const w=el.naturalWidth||el.width||0, h=el.naturalHeight||el.height||0;
            const key=u.split('?')[0];
            if(set.has(key)) continue; set.add(key);
            out.push({u:u, w:w, h:h});
          }
          return out;
        }""")
        out['title']=title
        out['images']=info
        out['article']=len(pg.query_selector_all('article'))
    except Exception as e:
        out['err']=str(e)[:600]
    finally:
        try: pg.close()
        except: pass
print(json.dumps(out,ensure_ascii=False,indent=1)[:4000])

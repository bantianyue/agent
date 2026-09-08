# -*- coding: utf-8 -*-
import json,time,sys,re
from playwright.sync_api import sync_playwright
URL=sys.argv[1]; NAME=sys.argv[2]
res={}
with sync_playwright() as p:
    b=p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx=b.contexts[0] if b.contexts else b.new_context()
    pg=ctx.new_page()
    try:
        pg.goto(URL, wait_until="commit", timeout=90000)
        time.sleep(16)   # stay at TOP (hero region)
        info=pg.evaluate("""()=>{
          const big=[];
          // 1) large <img> anywhere (hero covers are large, non-avatar)
          for(const el of document.querySelectorAll('img[src],img[srcset]')){
            const u=el.currentSrc||el.src||''; if(!u) continue;
            if(/profile_images|_normal|emoji/i.test(u)) continue;
            const w=el.naturalWidth||el.width||0;
            if(w>=500) big.push({kind:'img',u:u,w:w,h:el.naturalHeight||el.height||0});
          }
          // 2) css background images mentioning pbs/twimg large
          const set=new Set();
          for(const el of document.body.querySelectorAll('*')){
            const bg=getComputedStyle(el).backgroundImage;
            if(!bg || bg==='none'||!bg.includes('url('))continue;
            const m=bg.match(/url\\(["']?([^"')]+)["']?\\)/); if(!m)continue;
            let u=m[1].replace(/&amp;/g,'&'); if(/profile_images|emoji|_normal/i.test(u))continue;
            if(u.match(/^\/\//))continue;
            const r=el.getBoundingClientRect();
            if(r.width>=400) set.add(u);
          }
          return {imgs:big.slice(0,30), bgcovers:[...set].slice(0,15)};
        }""")
        res['info']=info
        # grab top screenshot (viewport)
        pg.screenshot(path=f"D:/06_Hermes/articles/_hero_{NAME}.png", full_page=False)
        res['title']=pg.title()[:80]
    except Exception as e:
        res['err']=str(e)[:250]
    finally:
        try: pg.close()
        except: pass
print(json.dumps(res,ensure_ascii=False)[:3000])

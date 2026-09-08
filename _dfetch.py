# -*- coding: utf-8 -*-
import json,sys,time
from playwright.sync_api import sync_playwright
URL=sys.argv[1]; NAME=sys.argv[2] if len(sys.argv)>2 else 'out'
out={}
with sync_playwright() as p:
    b=p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx=b.contexts[0] if b.contexts else b.new_context()
    pg=ctx.new_page()
    try:
        pg.goto(URL, wait_until="commit", timeout=60000)
        time.sleep(14)   # allow SPA article hydrate & lazy load
        # login marker WITHOUT crashing on networkidle
        try:
            auth=pg.evaluate("async()=>{try{const r=await fetch('https://x.com/i/api/1.1/account/settings.json',{credentials:'include'});return r.status}catch(e){return 'x'}}")
        except Exception as e:
            auth='eval-'+str(e)[:40]
        # gather imgs
        imgs=pg.evaluate("""()=>{
          const res=[]; const seen=new Set();
          for(const el of document.querySelectorAll('img[src],img[srcset]')){
            let u=el.currentSrc||el.src||''; if(!u) continue;
            if(/profile_images|emoji|/i.test(u)) continue;
            const w=el.naturalWidth||el.width||0, h=el.naturalHeight||el.height||0;
            const k=u.split('?')[0]; if(seen.has(k))continue; seen.add(k);
            res.push({u:u,w:w,h:h});
          }
          return res;
        }""")
        out['auth']=auth
        out['title']=pg.title()[:70]
        imgs=[x for x in imgs if x['w']>=120 and (x['h']>=60)]
        out['images']=imgs
    except Exception as e:
        out['err']=str(e)[:300]
    finally:
        try: pg.close()
        except: pass
fn=f"D:/06_Hermes/articles/_cap_{NAME}.json"
json.dump(out,open(fn,'w',encoding='utf8'),ensure_ascii=False,indent=1)
print(json.dumps(out,ensure_ascii=False)[:2500])

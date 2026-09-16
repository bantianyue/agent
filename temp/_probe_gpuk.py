# -*- coding: utf-8 -*-
import json,time,sys
from playwright.sync_api import sync_playwright
URL=sys.argv[1]; NAME=sys.argv[2]
res={}
with sync_playwright() as p:
    b=p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx=b.contexts[0] if b.contexts else b.new_context()
    pg=ctx.new_page()
    try:
        pg.goto(URL, wait_until="domcontentloaded", timeout=150000)
        time.sleep(8)
        # scroll to trigger lazy loading
        for _ in range(80):
            try: pg.mouse.wheel(0,1500)
            except: break
            time.sleep(0.35)
        time.sleep(5)
        info=pg.evaluate("""()=>{
          const out=[]; let last='';
          const walker=document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT|NodeFilter.SHOW_ELEMENT);
          let cur=walker.currentNode, steps=0;
          while(cur && steps<400000){
            steps++;
            if(cur.nodeType===Node.TEXT_NODE){
              const t=(cur.textContent||'').trim();
              if(t.length>=3) last=(last+' '+t).trim().slice(0,110);
            } else if(cur.tagName==='IMG'){
              const u=cur.currentSrc||cur.src||'';
              if(u && !/profile_images|_normal|emoji/i.test(u)){
                const w=cur.naturalWidth||cur.width||0;
                if(w>=300) out.push({u:u, w:w, ctx:last.slice(0,110)});
              }
            }
            let n=null;
            try{ n=cur.firstChild||cur.nextSibling; let c=cur;
              while(!n){ if(!c.parentNode)break; n=c.parentNode.nextSibling; c=c.parentNode; } }catch(e){}
            cur=n; if(!cur) break;
          }
          return {n:out.length, items:out, title:document.title, h1:(document.querySelector('h1')||{}).innerText||'', bodyLen:(document.body?document.body.innerText.length:0)};
        }""")
        res=info
    except Exception as e:
        res['err']=str(e)[:400]
    finally:
        try: pg.close()
        except: pass
json.dump(res,open(rf"D:/06_Hermes/articles/_probe_{NAME}.json",'w',encoding='utf8'),ensure_ascii=False,indent=1)
for i,o in enumerate((res.get('items') or [])[:60]):
    print(f"[{i}] {str(o.get('u'))[:120]}  ctx={o.get('ctx','')[:70]}")
print('ERR',res.get('err'),'| items',res.get('n'),'| title',str(res.get('title'))[:60])

# -*- coding: utf-8 -*-
import json,time,sys,re
from playwright.sync_api import sync_playwright
URL=sys.argv[1]; NAME=sys.argv[2]
out=[]
with sync_playwright() as p:
    b=p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx=b.contexts[0] if b.contexts else b.new_context()
    pg=ctx.new_page()
    try:
        pg.goto(URL, wait_until="commit", timeout=95000)
        time.sleep(14)
        # walk main order: text blocks and images
        data=pg.evaluate("""()=>{
          const out=[]; let last='';
          // gather text & paragraphs in DOM order (rough)
          const walker=document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT|NodeFilter.SHOW_ELEMENT);
          let cur=walker.currentNode;
          while(cur){ 
            if(cur.nodeType===Node.TEXT_NODE){
              const t=(cur.textContent||'').trim(); if(t.length>=2) last=(last+' '+t).trim().slice(0,90);
            } else if(cur.tagName==='IMG'){
              const u=cur.currentSrc||cur.src||''; 
              if(u && !/profile_images|_normal|emoji/i.test(u)){
                const w=cur.naturalWidth||cur.width||0;
                if(w>=500){
                  const alt=(cur.alt||'').trim();
                  out.push({u:u.split('?')[0].split('/').pop()||u, alt:alt, ctx:last.slice(0,90)});
                  last='';
                }
              }
            }
            let n=null; try{ n=cur.firstChild||cur.nextSibling; let c=cur;
              while(!n){ if(!c.parentNode)break; n=c.parentNode.nextSibling; c=c.parentNode; } }catch(e){}
            cur=n; if(!cur) break;
          }
          return out;
        }""")
        out=data
    except Exception as e:
        out=[{"err":str(e)[:200]}]
    finally:
        try: pg.close()
        except: pass
json.dump(out,open(f"D:/06_Hermes/articles/_ctx_{NAME}.json",'w',encoding='utf8'),ensure_ascii=False)
for i,o in enumerate(out):
    print(f"[{i}] {str(o.get('u'))[-14:]}  ctx={o.get('ctx','')[:70]}")
    if o.get('alt'): print("      alt:", o['alt'][:120])

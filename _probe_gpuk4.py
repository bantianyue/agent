# -*- coding: utf-8 -*-
import json,time,sys
from playwright.sync_api import sync_playwright
URL=sys.argv[1]; NAME=sys.argv[2]
res={}
def try_scan(pg):
    return pg.evaluate("""()=>{
      // find the deep container holding the article body text
      const needles=['kernel','shared memory','cuBLAS','thread ID'];
      function inNeedle(t){t=t||''; return needles.some(n=>t.includes(n));}
      let best=null;
      for(const el of document.querySelectorAll('div,article,section')){
        const t=(el.innerText||'');
        if(t.length<300) continue;
        if(inNeedle(t) && el.querySelector('img')){
          if(!best || t.length<best.tlen){ best={el:el,tlen:t.length}; }
        }
      }
      if(!best){
        // fallback: any element containing needle text
        for(const el of document.querySelectorAll('div,article')){
          const t=(el.innerText||'');
          if(inNeedle(t)){ best={el:el,tlen:t.length}; break; }
        }
      }
      if(!best) return {err:'no container',bodyLen:document.body?document.body.innerText.length:0};
      const root=best.el;
      const out=[]; let last='';
      const walk=document.createTreeWalker(root, NodeFilter.SHOW_TEXT|NodeFilter.SHOW_ELEMENT);
      let cur=walk.currentNode, steps=0;
      while(cur && steps<300000){
        steps++;
        if(cur.nodeType===Node.TEXT_NODE){
          const tt=(cur.textContent||'').trim();
          if(tt.length>=2) last=(last+' '+tt).trim().slice(0,140);
        } else if(cur.tagName==='IMG'){
          const u=(cur.currentSrc||cur.src||'').split('?')[0];
          if(u && !/profile_images|emoji|_normal/i.test(u)){
            out.push({u:u,w:cur.naturalWidth||cur.width||0,h:cur.naturalHeight||cur.height||0,ctx:last});
            last='';
          }
        }
        let n=null;
        try{ n=cur.firstChild||cur.nextSibling; let c=cur;
          while(!n){ if(!c.parentNode)break; n=c.parentNode.nextSibling; c=c.parentNode; } }catch(e){}
        cur=n; if(!cur) break;
      }
      return {n:out.length,items:out,rootTlen:root.innerText.length,rootTag:root.tagName,bodyLen:document.body?document.body.innerText.length:0, h1:(document.querySelector('h1')||{}).innerText||''};
    }""")
with sync_playwright() as p:
    b=p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx=b.contexts[0] if b.contexts else b.new_context()
    pg=ctx.new_page()
    last=None
    for attempt in range(3):
        try:
            pg.goto(URL, wait_until="domcontentloaded", timeout=120000)
            time.sleep(12+attempt*8)
            pg.mouse.wheel(0,800)
            time.sleep(4)
            info=try_scan(pg)
            if info.get('n') and not info.get('err'):
                res=info; break
            last=info
            time.sleep(6)
        except Exception as e:
            last={'exc':str(e)[:200]}
            time.sleep(5)
    res=res or last or {}
    try: pg.close()
    except: pass
json.dump(res,open(rf"D:/06_Hermes/articles/_probe4_{NAME}.json",'w',encoding='utf8'),ensure_ascii=False,indent=1)
for i,o in enumerate(res.get('items') or []):
    print(f"[{i}] {o.get('u','')[-40:]} w={o.get('w')} ctx={o.get('ctx','')[:80]}")
print('n',res.get('n'),'err',res.get('err'),'rootTlen',res.get('rootTlen'),'bodyLen',res.get('bodyLen'),'h1',str(res.get('h1'))[:50])

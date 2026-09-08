# -*- coding: utf-8 -*-
import json,time,sys
from playwright.sync_api import sync_playwright
URL=sys.argv[1]; NAME=sys.argv[2]
media=[]; seen=set()
def on_resp(resp):
    try:
        u=resp.url
        if 'pbs.twimg.com/media/' not in u: return
        base=u.split('?')[0]
        if base in seen: return
        seen.add(base)
        if 'image' in (resp.headers.get('content-type') or ''): media.append(base)
    except Exception: pass
res={}
with sync_playwright() as p:
    b=p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx=b.contexts[0] if b.contexts else b.new_context()
    pg=ctx.new_page()
    pg.on('response', on_resp)
    try:
        pg.goto(URL, wait_until="domcontentloaded", timeout=150000)
        time.sleep(10)
        # helper: scroll the tallest scrollable element containing article text
        def scroll_once(times=1):
            for _ in range(times):
                try:
                    pg.evaluate("""()=>{
                      const sc=document.scrollingElement;
                      const cands=[...document.querySelectorAll('main div,main section,article,div[data-testid]')]
                        .filter(e=>e.scrollHeight>e.clientHeight+200 && (e.innerText||'').includes('kernel'))
                        .sort((a,b)=>(b.scrollHeight-b.clientHeight)-(a.scrollHeight-a.clientHeight));
                      if(cands[0]){ cands[0].scrollTop=cands[0].scrollHeight; }
                      else if(sc){ sc.scrollTop=sc.scrollHeight; }
                    }""")
                except Exception: pass
                time.sleep(0.5)
        for cyc in range(3):
            for _ in range(30):
                try: pg.mouse.wheel(0,1800)
                except: break
                time.sleep(0.4)
            scroll_once(5)
            time.sleep(3)
            # go back up for next cycle
            try: pg.evaluate("()=>{window.scrollTo(0,0); const c=[...document.querySelectorAll('main div')].filter(e=>e.scrollHeight>e.clientHeight+200)[0]; if(c)c.scrollTop=0;}")
            except: pass
            time.sleep(2)
        scroll_once(8)
        time.sleep(6)
        # final ordered scan inside article container
        info=pg.evaluate("""()=>{
          const needles=['kernel','cuBLAS','shared memory','thread ID'];
          let best=null;
          for(const el of document.querySelectorAll('div,article,section')){
            const t=(el.innerText||'');
            if(t.length<300 || !needles.some(n=>t.includes(n))) continue;
            if(!best || t.length<best.tlen){best={el:el,tlen:t.length};}
          }
          if(!best) return {err:'no container'};
          const out=[]; let last='';
          const w=document.createTreeWalker(best.el,NodeFilter.SHOW_TEXT|NodeFilter.SHOW_ELEMENT);
          let cur=w.currentNode,steps=0;
          while(cur&&steps<300000){
            steps++;
            if(cur.nodeType===Node.TEXT_NODE){const tt=(cur.textContent||'').trim(); if(tt.length>=2) last=(last+' '+tt).trim().slice(0,160);}
            else if(cur.tagName==='IMG'){
              const u=(cur.currentSrc||cur.src||'').split('?')[0];
              if(u && !/profile_images|emoji|_normal|extensions|assets\/icons/i.test(u)){out.push({u:u,w:cur.naturalWidth||cur.width||0,ctx:last}); last='';}
            }
            let n=null;
            try{n=cur.firstChild||cur.nextSibling; let c=cur; while(!n){if(!c.parentNode)break; n=c.parentNode.nextSibling; c=c.parentNode;}}catch(e){}
            cur=n; if(!cur) break;
          }
          return {n:out.length,items:out,tlen:best.el.innerText.length};
        }""")
        res={'media':sorted(media),'info':info,'title':pg.title()[:60]}
    except Exception as e:
        res={'err':str(e)[:400]}
    finally:
        try: pg.close()
        except: pass
json.dump(res,open(rf"D:/06_Hermes/articles/_probe5_{NAME}.json",'w',encoding='utf8'),ensure_ascii=False,indent=1)
print('err',res.get('err'),'| title',res.get('title'))
print('NETWORK media urls:')
for m in res.get('media') or []: print('  ',m[-50:])
info=res.get('info') or {}
print('DOM items n=',info.get('n'),'tlen',info.get('tlen'))
for i,o in enumerate(info.get('items') or []):
    print(f"  [{i}] {o.get('u','')[-46:]} w={o.get('w')} ctx={o.get('ctx','')[:90]}")

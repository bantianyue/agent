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
    got=None
    for attempt in range(5):
        try:
            pg.goto(URL, wait_until="commit", timeout=100000)
            time.sleep(15)
            got=True
            break
        except Exception as e:
            print('attempt',attempt,'goto err',str(e)[:120]); time.sleep(8+attempt*5)
    if got:
        try:
            # union-collect while scrolling article containers
            def domset():
                return pg.evaluate("""()=>{
                  const s=new Set();
                  for(const el of document.querySelectorAll('img[src],img[srcset]')){
                    const u=((el.currentSrc||el.src)||'').split('?')[0];
                    if(u.includes('pbs.twimg.com/media')) s.add(u);
                  }
                  return [...s];
                }""")
            base_set=set(domset())
            for cyc in range(4):
                # scroll inner containers then window
                pg.evaluate("""()=>{
                  const cands=[...document.querySelectorAll('div,main,section,article')]
                    .filter(e=>e.scrollHeight>e.clientHeight+300 && (e.innerText||'').length>500)
                    .sort((a,b)=>(b.scrollHeight-b.clientHeight)-(a.scrollHeight-a.clientHeight));
                  for(const c of cands.slice(0,3)){ c.scrollTop=c.scrollHeight; }
                }""")
                time.sleep(1.2)
                for _ in range(40):
                    try: pg.mouse.wheel(0,2200)
                    except: break
                    time.sleep(0.3)
                base_set|=set(domset())
                pg.evaluate("window.scrollTo(0,0)")
                time.sleep(1.5)
            # final ordered scan inside the biggest text container
            info=pg.evaluate("""()=>{
              let best=null;
              for(const el of document.querySelectorAll('div,article,section')){
                const t=(el.innerText||'');
                if(t.length<400 || !t.includes('kernel')) continue;
                if(!best || t.length<best.tlen){best={el:el,tlen:t.length};}
              }
              if(!best) return {err:'no container'};
              const out=[]; let last='';
              const w=document.createTreeWalker(best.el,NodeFilter.SHOW_TEXT|NodeFilter.SHOW_ELEMENT);
              let cur=w.currentNode,steps=0;
              while(cur&&steps<400000){
                steps++;
                if(cur.nodeType===Node.TEXT_NODE){const tt=(cur.textContent||'').trim();
                  if(tt.length>=2 && !tt.startsWith('<') && !tt.includes('{')) last=(last+' '+tt).trim().slice(0,200);}
                else if(cur.tagName==='IMG'){
                  const u=(cur.currentSrc||cur.src||'').split('?')[0];
                  if(u && u.includes('pbs.twimg.com/media')){out.push({u:u,w:cur.naturalWidth||cur.width||0,ctx:last}); last='';}
                }
                let n=null;
                try{n=cur.firstChild||cur.nextSibling; let c=cur; while(!n){if(!c.parentNode)break; n=c.parentNode.nextSibling; c=c.parentNode;}}catch(e){}
                cur=n; if(!cur) break;
              }
              return {n:out.length,items:out,tlen:best.el.innerText.length};
            }""")
            res={'media':sorted(media),'domset':sorted(base_set),'info':info,'title':pg.title()[:60]}
        except Exception as e:
            res={'err':str(e)[:400]}
    else:
        res={'err':'goto never succeeded'}
    try: pg.close()
    except: pass
json.dump(res,open(rf"D:/06_Hermes/articles/_probe6_{NAME}.json",'w',encoding='utf8'),ensure_ascii=False,indent=1)
print('err',res.get('err'),'| title',res.get('title'))
print('NET:',len(res.get('media') or []),'DOMset:',len(res.get('domset') or []))
for u in res.get('media') or []: print('  net',u[-50:])
for u in res.get('domset') or []: print('  dom',u[-50:])
info=res.get('info') or {}
print('ordered items n=',info.get('n'),'tlen',info.get('tlen'))
for i,o in enumerate(info.get('items') or []):
    print(f"  [{i}] {o.get('u','')[-44:]} w={o.get('w')} ctx={o.get('ctx','')[:80]}")

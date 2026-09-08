# -*- coding: utf-8 -*-
import json,time,sys
from playwright.sync_api import sync_playwright
URL=sys.argv[1]; NAME=sys.argv[2]
res={}
def find_scan(pg):
    return pg.evaluate("""()=>{
      // deepest-ish container whose text covers a good chunk of article
      let best=null;
      const all=document.querySelectorAll('div,article,section,main');
      for(const el of all){
        const t=(el.innerText||'');
        if(t.length<500 || !/kernel|cuBLAS|shared memory/i.test(t)) continue;
        if(!best || t.length>best.tlen){best={el:el,tlen:t.length};}
      }
      if(!best) return null;
      const out=[]; let last='';
      const w=document.createTreeWalker(best.el,NodeFilter.SHOW_TEXT|NodeFilter.SHOW_ELEMENT);
      let cur=w.currentNode,steps=0;
      while(cur&&steps<400000){
        steps++;
        if(cur.nodeType===Node.TEXT_NODE){
          const tt=(cur.textContent||'').trim();
          if(tt.length>=2 && !tt.includes('{') && !tt.startsWith('<')) last=(last+' '+tt).trim().slice(0,240);
        } else if(cur.tagName==='IMG'){
          const u=(cur.currentSrc||cur.src||'').split('?')[0];
          if(u && u.includes('pbs.twimg.com/media')) out.push({u:u,w:cur.naturalWidth||cur.width||0,ctx:last.slice(0,240)});
        }
        let n=null;
        try{n=cur.firstChild||cur.nextSibling; let c=cur; while(!n){if(!c.parentNode)break; n=c.parentNode.nextSibling; c=c.parentNode;}}catch(e){}
        cur=n; if(!cur) break;
      }
      return {items:out,tlen:best.el.innerText.length};
    }""")
with sync_playwright() as p:
    b=p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx=b.contexts[0] if b.contexts else b.new_context()
    pg=ctx.new_page()
    got=False
    for attempt in range(6):
        try:
            pg.goto(URL, wait_until="commit", timeout=100000)
            time.sleep(16)
            got=True; break
        except Exception as e:
            print('attempt',attempt,'err',str(e)[:100]); time.sleep(6+attempt*6)
    rec={}   # u -> {w, ctx, firstseen}
    order=[]
    tlen=0
    if got:
        try:
            for cyc in range(2):
                # scroll inner container to top
                pg.evaluate("""()=>{window.scrollTo(0,0);
                  const cs=[...document.querySelectorAll('div,main,article')].filter(e=>e.scrollHeight>e.clientHeight+300).sort((a,b)=>(b.scrollHeight-b.clientHeight)-(a.scrollHeight-a.clientHeight));
                  if(cs[0]) cs[0].scrollTop=0;}""")
                time.sleep(2)
                for step in range(50):
                    try: pg.evaluate("""()=>{
                      const cs=[...document.querySelectorAll('div,main,article')].filter(e=>e.scrollHeight>e.clientHeight+300 && (e.innerText||'').includes('kernel')).sort((a,b)=>(b.scrollHeight-b.clientHeight)-(a.scrollHeight-a.clientHeight));
                      if(cs[0]){ if(cs[0].scrollTop+cs[0].clientHeight>=cs[0].scrollHeight-10) cs[0].scrollTop=0; else cs[0].scrollTop+=cs[0].clientHeight*0.9; }
                      else window.scrollBy(0, window.innerHeight*0.9);
                    }""")
                    except: pass
                    time.sleep(0.7)
                    sc=find_scan(pg)
                    if not sc: continue
                    tlen=max(tlen,sc['tlen'])
                    for it in sc['items']:
                        if it['u'] not in rec:
                            rec[it['u']]={'w':it['w'],'ctx':it['ctx']}; order.append(it['u'])
                time.sleep(1)
        except Exception as e:
            res['err']=str(e)[:400]
    else:
        res['err']='no load'
    res['tlen']=tlen
    res['order']=[{'u':u,'w':rec[u]['w'],'ctx':rec[u]['ctx']} for u in order]
    try: pg.close()
    except: pass
json.dump(res,open(rf"D:/06_Hermes/articles/_probe7_{NAME}.json",'w',encoding='utf8'),ensure_ascii=False,indent=1)
print('err',res.get('err'),'tlen',tlen,'count',len(order))
for i,o in enumerate(res['order']):
    print(f"[{i}] {o['u'][-44:]} w={o['w']} ctx={o['ctx'][:110]}")

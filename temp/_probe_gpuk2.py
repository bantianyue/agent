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
        time.sleep(6)
        for _ in range(100):
            try: pg.mouse.wheel(0,1500)
            except: break
            time.sleep(0.25)
        time.sleep(5)
        data=pg.evaluate("""()=>{
          const allEls=[...document.querySelectorAll('h1,h2,h3,h4,p,pre,img')];
          const seq=[];
          for(const el of allEls){
            if(el.tagName==='IMG'){
              const u=(el.currentSrc||el.src||'').split('?')[0];
              if(!u || /profile_images|_normal|emoji|twimg.com\/sticker/i.test(u)) continue;
              seq.push({kind:'img',u:u,w:el.naturalWidth||el.width||0,h:el.naturalHeight||el.height||0});
            } else if(el.tagName==='PRE'){
              const t=el.innerText.trim();
              if(t) seq.push({kind:'pre',t:t.slice(0,300)});
            } else {
              const t=(el.innerText||'').trim();
              if(t && !/^\\s*$/.test(t) && seq.length && seq[seq.length-1].kind!=='txt') seq.push({kind:'txt',t:t.slice(0,160)});
              else if(t && !/^\\s*$/.test(t)){ if(seq.length&&seq[seq.length-1].kind==='txt') seq[seq.length-1].t+=' | '+t.slice(0,160); else seq.push({kind:'txt',t:t.slice(0,160)}); }
            }
          }
          let lastTxt='';
          const imgs=[];
          for(const it of seq){
            if(it.kind==='txt'){ lastTxt=it.t.slice(0,140); }
            else if(it.kind==='img'){ imgs.push({u:it.u,w:it.w,h:it.h,ctx:lastTxt}); }
          }
          return {totalImgs:allEls.filter(e=>e.tagName==='IMG').length, seq:seq.slice(0,200), imgs:imgs, title:document.title, bodyLen:(document.body?document.body.innerText.length:0)};
        }""")
        res=data
    except Exception as e:
        res['err']=str(e)[:400]
    finally:
        try: pg.close()
        except: pass
json.dump(res,open(rf"D:/06_Hermes/articles/_probe2_{NAME}.json",'w',encoding='utf8'),ensure_ascii=False,indent=1)
for i,o in enumerate(res.get('imgs') or []):
    print(f"[{i}] {o.get('u')[-40:]} w={o.get('w')} ctx={o.get('ctx','')[:60]}")
print('ERR',res.get('err'),'| imgs',len(res.get('imgs') or []),'| bodyLen',res.get('bodyLen'))

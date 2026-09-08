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
        ct=resp.headers.get('content-type','')
        if 'image' in ct: media.append({'url':u,'ct':ct})
    except Exception: pass
res={}
with sync_playwright() as p:
    b=p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx=b.contexts[0] if b.contexts else b.new_context()
    pg=ctx.new_page()
    pg.on('response', on_resp)
    try:
        pg.goto(URL, wait_until="domcontentloaded", timeout=150000)
        time.sleep(6)
        pg.mouse.click(10,300)
        time.sleep(3)
        for i in range(120):
            st=pg.evaluate("()=>{const sc=document.scrollingElement; const el=[document.body,...document.querySelectorAll('*')].filter(e=>e.scrollHeight>e.clientHeight+200).sort((a,b)=>(b.scrollHeight-b.clientHeight)-(a.scrollHeight-a.clientHeight))[0]; return {wy:sc?sc.scrollTop:0, wsh:sc?sc.scrollHeight:0, el:(el?el.scrollHeight-el.clientHeight:0)} }")
            cap=st['el'] or st['wsh']
            y=pg.evaluate("()=>{const sc=document.scrollingElement; const el=[...document.querySelectorAll('div,main,section')].filter(e=>e.scrollHeight>e.clientHeight+300).sort((a,b)=>(b.scrollHeight-b.clientHeight)-(a.scrollHeight-a.clientHeight))[0]; if(el){el.scrollTop=el.scrollHeight;return 'el'} sc.scrollTop=sc.scrollHeight; return 'win'}")
            time.sleep(0.3)
        time.sleep(6)
        info=pg.evaluate("""()=>{
          const imgs=[];
          for(const el of document.querySelectorAll('img[src]')){
            const u=(el.currentSrc||el.src||'').split('?')[0];
            if(!u.includes('pbs.twimg.com/media')) continue;
            imgs.push({u:u, w:el.naturalWidth||el.width||0, h:el.naturalHeight||el.height||0, alt:(el.alt||'').slice(0,60)});
          }
          const art=[...document.querySelectorAll('article div[lang]')].map(e=>e.innerText.slice(0,200));
          return {nImgs:imgs.length, imgs:imgs, bodyLen:document.body?document.body.innerText.length:0, artSamples:art.slice(0,5)};
        }""")
        pg.screenshot(path=rf"D:/06_Hermes/articles/_shot_{NAME}.png")
        res={'media':media,'info':info,'title':pg.title()[:80]}
    except Exception as e:
        res['err']=str(e)[:500]
    finally:
        try: pg.close()
        except: pass
json.dump(res,open(rf"D:/06_Hermes/articles/_probe3_{NAME}.json",'w',encoding='utf8'),ensure_ascii=False,indent=1)
print('title',res.get('title'))
print('err',res.get('err'))
print('net media:',len(res.get('media') or []))
for m in res.get('media') or []: print('  ',m['url'][:130])
info=res.get('info') or {}
print('dom media imgs:',info.get('nImgs'),'bodyLen',info.get('bodyLen'))
for i in info.get('imgs') or []: print('  ',i['u'][-46:],i['w'],i['h'],i['alt'][:30])
print('art samples:')
for s in (info.get('artSamples') or []): print('   *',s[:100].replace(chr(10),' '))

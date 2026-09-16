# -*- coding: utf-8 -*-
import json,time,sys,re
from playwright.sync_api import sync_playwright
URL=sys.argv[1]; NAME=sys.argv[2]; OUT=r"D:/06_Hermes/articles"
pics={}
media_urls=[]
def on_resp(resp):
    try:
        u=resp.url
        if not u.startswith('http'): return
        low=u.lower()
        if not (('pbs.twimg.com/media' in low) or ('.png' in low) or ('.jpg' in low or '.jpeg' in low) or ('.webp' in low) or ('/media/' in low)): return
        if 'profile_images' in low or 'emoji' in low.replace('‌',''): return
        ct=resp.headers.get('content-type','')
        if 'image' not in ct and '.mp4' not in low and 'video' not in ct: return
        media_urls.append(u)
    except Exception:
        pass
with sync_playwright() as p:
    b=p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx=b.contexts[0] if b.contexts else b.new_context()
    pg=ctx.new_page()
    pg.on('response', on_resp)
    try:
        pg.goto(URL, wait_until="commit", timeout=120000)
        time.sleep(18)
        # scroll through whole page
        for _ in range(60):
            try: pg.mouse.wheel(0,1200)
            except: break
            time.sleep(0.5)
        time.sleep(6)
        pg.screenshot(path=OUT+f"/_shot_{NAME}.png", full_page=False)
        title=pg.title()[:80]
    except Exception as e:
        title='ERR '+str(e)[:120]
    finally:
        try: pg.close()
        except: pass
seen=[]
_for=set()
for u in media_urls:
    base=re.sub(r'\?.*','',u)
    if base in _for: continue
    _for.add(base); seen.append((base, len(u)))
print("TITLE", title)
print("media image resp urls:", len(seen))
for base,_ in seen[:50]:
    print("  ", base[:150])

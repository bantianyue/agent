# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import time
def attempt(i):
    with sync_playwright() as p:
        b=p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        ctx=b.contexts[0] if b.contexts else b.new_context()
        pg=ctx.new_page()
        try:
            pg.goto("https://x.com/home", wait_until="networkidle", timeout=85000)
            pg.wait_for_timeout(5000)
            title=pg.title()[:60]
            st=None
            try:
                st=pg.evaluate("async()=>{const r=await fetch('https://x.com/i/api/1.1/account/settings.json',{credentials:'include'});return r.status;}")
            except Exception as e:
                st='eval-err-'+str(e)[:50]
            print("attempt",i,"title=",title,"settings_status=",st,"articles=",len(pg.query_selector_all("article")))
            return True
        except Exception as e:
            print("attempt",i,"ERR",str(e)[:200])
            return False
        finally:
            try: pg.close()
            except: pass
for i in range(2):
    if attempt(i):
        break
    time.sleep(3)

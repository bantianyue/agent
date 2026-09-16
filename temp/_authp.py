# -*- coding: utf-8 -*-
import time
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx=b.contexts[0] if b.contexts else b.new_context()
    pg=ctx.new_page()
    try:
        pg.goto("https://x.com/home", wait_until="commit", timeout=40000)
        time.sleep(9)
        print("TITLE:", pg.title()[:80])
        arts=pg.query_selector_all("article")
        print("articles:", len(arts))
        txt=pg.inner_text("body")[:400]
        print("signin-hit:", ("Sign in" in txt) or ("登录" in txt) or ("sign in" in txt.lower()))
        print("CTX:", txt[:200].replace("\n"," / "))
    except Exception as e:
        print("ERR", str(e)[:200])
    finally:
        try: pg.close()
        except: pass

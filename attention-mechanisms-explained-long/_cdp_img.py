# -*- coding: utf-8 -*-
import json
from playwright.sync_api import sync_playwright
url="https://x.com/akshay_pachaar/status/2096215921568498042"
out={}
with sync_playwright() as p:
    b=p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx=b.contexts[0] if b.contexts else b.new_context()
    pg=ctx.new_page()
    try:
        pg.goto(url, wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(9000)  # 懒加载与文章展开
        # 滚动到底触发懒加载插图
        try:
            for _ in range(6):
                pg.mouse.wheel(0, 2500); pg.wait_for_timeout(900)
        except Exception as e: out['scroll_err']=str(e)[:100]
        arts=pg.query_selector_all("article")
        out['article_cnt']=len(arts)
        imgs=[]
        # 从 body 收集图片但排除头像/emoji
        nodes=pg.eval_on_selector_all("img","els=>els.map(e=>e.currentSrc||e.src||'')")
        from collections import OrderedDict
        seen=OrderedDict()
        for s in nodes:
            if not s: continue
            if 'profile_images' in s or 'emoji' in s.lower(): continue
            # 归一 name=大尺寸
            seen[s]=1
        out['imgs']=list(seen.keys())
        # og/hero
        out['og']=pg.eval_on_selector_all("meta[property='og:image']","els=>els.map(e=>e.content)")
        out['page_title']=pg.title()
    except Exception as e:
        out['err']=str(e)[:500]
    finally:
        try: pg.close()
        except: pass
print(json.dumps(out,ensure_ascii=False,indent=1)[:3500])

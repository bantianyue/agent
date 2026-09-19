import os
from playwright.sync_api import sync_playwright
URL="https://mlc.ai/modern-gpu-programming-for-mlsys/demo/pipeline_arch.html"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True, proxy={"server":"http://127.0.0.1:7890"})
    pg=b.new_page(viewport={"width":1000,"height":1200}, device_scale_factor=1)
    pg.goto(URL, wait_until="load", timeout=60000)
    pg.wait_for_timeout(2500)
    info=pg.evaluate("""() => {
      const sel=['h1','.sub','.pipeline','#archWrap','.detail-panel','.sm-box','#arrowSvg','body'];
      const out={};
      for (const s of sel){ const e=document.querySelector(s); if(e){const r=e.getBoundingClientRect(); out[s]={x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};} }
      out.scroll={w:document.documentElement.scrollWidth,h:document.documentElement.scrollHeight};
      return out;
    }""")
    for k,v in info.items(): print(k,v)
    b.close()
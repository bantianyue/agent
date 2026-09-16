# -*- coding: utf-8 -*-
"""One-off probe: dump the rendered X Article container HTML for offline ordering analysis."""
import sys, time
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

URL = "https://x.com/i/article/2097417044840869888"

JS = r"""
() => {
  const root = document.querySelector('[data-testid="twitterArticleReadView"]')
             || document.querySelector('article') || document.body;
  return root.outerHTML;
}
"""

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = b.contexts[0]
    pg = ctx.new_page()
    try:
        pg.goto(URL, wait_until="domcontentloaded", timeout=60000)
        time.sleep(9)
        for i in range(12):
            pg.mouse.wheel(0, 1400)
            time.sleep(1.0)
        time.sleep(3)
        html = pg.evaluate(JS)
        open(r"D:/06_Hermes/articles/_vlgif_article.html", "w", encoding="utf-8").write(html)
        print("bytes:", len(html))
        # also grab the raw HTML entities path for each media anchor
        anchors = pg.evaluate(r"""() => {
          const root = document.querySelector('[data-testid="twitterArticleReadView"]')
                     || document.querySelector('article') || document.body;
          const res = [];
          root.querySelectorAll('img,video').forEach(el => {
            if (el.tagName === 'IMG') {
              const s = el.currentSrc || el.src || '';
              if (s.includes('profile_images') || s.includes('emoji')) return;
              res.push({t:'img', src:s, alt:el.alt||''});
            } else {
              res.push({t:'video', src: el.currentSrc||el.src||'', poster: el.poster||''});
            }
          });
          return res;
        }""")
        for i, a in enumerate(anchors):
            print(i, a)
    finally:
        pg.close()

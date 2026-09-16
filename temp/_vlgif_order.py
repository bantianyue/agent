# -*- coding: utf-8 -*-
"""One-off probe: ordered walk of the X Article body -> text blocks + media in reading order."""
import sys, json, time
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

URL = "https://x.com/i/article/2097417044840869888"

JS = r"""
() => {
  const root = document.querySelector('[data-testid="twitterArticleReadView"]')
             || document.querySelector('article') || document.body;
  const seq = [];
  const walk = (el) => {
    for (const c of el.children) {
      const tag = c.tagName.toLowerCase();
      if (tag === 'img') {
        const s = c.currentSrc || c.src || '';
        if (s.includes('profile_images') || s.includes('emoji')) continue;
        seq.push({t: 'img', src: s, alt: c.alt || ''});
      } else if (tag === 'video') {
        seq.push({t: 'video', src: c.currentSrc || c.src || '', poster: c.poster || ''});
      } else if (['p','h1','h2','h3','h4','li','blockquote'].includes(tag)) {
        const txt = (c.innerText || '').trim();
        if (!txt) continue;
        const inner = c.querySelectorAll('img,video').length;
        seq.push({t: tag, text: txt.slice(0, 150), media_inside: inner});
        if (inner) walk(c);
      } else {
        walk(c);
      }
    }
  };
  walk(root);
  return {title: document.title, seq};
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
        data = pg.evaluate(JS)
        print("TITLE:", data["title"])
        for i, s in enumerate(data["seq"]):
            if s["t"] in ("img", "video"):
                print(f"[{i}] <<{s['t'].upper()}>> {s.get('src')} alt={s.get('alt')}")
            else:
                print(f"[{i}] {s['t']}: {s['text']}")
        open(r"D:/06_Hermes/articles/_vlgif_order.json", "w", encoding="utf-8").write(
            json.dumps(data, ensure_ascii=False, indent=1))
    finally:
        pg.close()

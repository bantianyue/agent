# -*- coding: utf-8 -*-
"""One-off probe: enumerate media (img/video/gif) in the live X Article DOM via CDP."""
import sys, json, time
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

URL = "https://x.com/i/article/2097417044840869888"

JS = r"""
() => {
  const out = {imgs: [], videos: [], medias: [], titled: document.title};
  const push = (arr, o) => arr.push(o);
  document.querySelectorAll('img').forEach(im => {
    const s = im.currentSrc || im.src || '';
    if (!s) return;
    if (s.includes('profile_images') || s.includes('emoji') || s.includes('abs.twimg.com/emoji')) return;
    push(out.imgs, {src: s, w: im.naturalWidth, h: im.naturalHeight,
      cw: im.clientWidth, ch: im.clientHeight,
      alt: (im.alt||'').slice(0,40), cls: (im.className||'').toString().slice(0,60)});
  });
  document.querySelectorAll('video').forEach(v => {
    push(out.videos, {src: v.currentSrc || v.src || '', poster: v.poster || '',
      w: v.videoWidth, h: v.videoHeight, dur: v.duration || 0,
      cw: v.clientWidth, ch: v.clientHeight,
      cls: (v.className||'').toString().slice(0,60)});
    v.querySelectorAll('source').forEach(s => push(out.videos, {source: s.src, type: s.type}));
  });
  // X media containers (images + gifs) carry data-testid="tweetPhoto" / videoPlayer
  document.querySelectorAll('[data-testid]').forEach(el => {
    const t = el.getAttribute('data-testid');
    if (['tweetPhoto','videoPlayer','videoComponent','previewInterstitial'].includes(t)) {
      const im = el.querySelector('img'); const v = el.querySelector('video');
      push(out.medias, {testid: t,
        img: im ? (im.currentSrc||im.src) : null,
        video: v ? (v.currentSrc||v.src) : null,
        poster: v ? v.poster : null});
    }
  });
  return out;
}
"""

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = b.contexts[0]
    pg = ctx.new_page()
    try:
        pg.goto(URL, wait_until="domcontentloaded", timeout=60000)
        time.sleep(9)
        for i in range(10):
            pg.mouse.wheel(0, 1400)
            time.sleep(1.2)
        time.sleep(3)
        data = pg.evaluate(JS)
        print("TITLE:", data["titled"])
        print("== IMGS ==")
        for i, im in enumerate(data["imgs"]):
            print(i, im)
        print("== VIDEOS ==")
        for i, v in enumerate(data["videos"]):
            print(i, v)
        print("== MEDIA TESTIDS ==")
        for i, m in enumerate(data["medias"]):
            print(i, m)
        open(r"D:/06_Hermes/articles/_vlgif_probe.json", "w", encoding="utf-8").write(
            json.dumps(data, ensure_ascii=False, indent=1))
    finally:
        pg.close()

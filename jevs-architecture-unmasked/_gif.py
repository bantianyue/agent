# -*- coding: utf-8 -*-
import os, time, math
from playwright.sync_api import sync_playwright

URL = "https://archerhume.com/posts/jevs-architecture-unmasked/?v=3"
log = []
def P(*a): log.append(" ".join(str(x) for x in a))

os.makedirs("frames", exist_ok=True)
for f in os.listdir("frames"):
    os.remove(os.path.join("frames", f))

with sync_playwright() as pw:
    browser = pw.chromium.launch(proxy={"server": "http://127.0.0.1:7890"}, args=["--no-sandbox"])
    ctx = browser.new_context(viewport={"width": 1280, "height": 1100}, device_scale_factor=2)
    page = ctx.new_page()
    page.goto(URL, wait_until="networkidle", timeout=120000)
    time.sleep(2)
    el = page.query_selector("jev-architecture-study")
    scene = page.query_selector("jev-architecture-study svg.scene")
    el.scroll_into_view_if_needed()
    time.sleep(1)
    scene.scroll_into_view_if_needed()
    time.sleep(0.5)
    # deterministic scrub
    ok = page.evaluate("""() => {
        const el = document.querySelector('jev-architecture-study');
        el.pause();
        el.time = 17100; el.render();
        return {time: el.time, C: el.C, w: el.width};
    }""")
    P("probe:", ok)
    time.sleep(0.5)
    scene.screenshot(path="cap/fig01_final.png")
    STEP = 80  # ms
    TOTAL = 17200
    n = int(round(TOTAL / STEP)) + 1
    t0 = time.time()
    for i in range(n):
        t = min(i * STEP, TOTAL - 1)
        page.evaluate("""(t) => { const el = document.querySelector('jev-architecture-study'); el.time = t; el.render(); }""", t)
        scene.screenshot(path="frames/f%04d.png" % i)
    dur = time.time() - t0
    P("frames:", n, "elapsed %.1fs" % dur, "avg %.0fms/frame" % (dur * 1000 / n))
    browser.close()
open("_gif.txt", "w", encoding="utf-8").write("\n".join(log))
print("done")

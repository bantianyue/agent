# -*- coding: utf-8 -*-
import os, sys, json, time
from playwright.sync_api import sync_playwright

URL = "https://archerhume.com/posts/jevs-architecture-unmasked/?v=3"
log = []
def P(*a):
    s = " ".join(str(x) for x in a)
    log.append(s)

with sync_playwright() as pw:
    browser = pw.chromium.launch(proxy={"server": "http://127.0.0.1:7890"}, args=["--no-sandbox"])
    ctx = browser.new_context(viewport={"width": 1280, "height": 1000}, device_scale_factor=3)
    page = ctx.new_page()
    page.goto(URL, wait_until="networkidle", timeout=120000)
    time.sleep(3)
    # scroll to trigger lazy
    for i in range(12):
        page.mouse.wheel(0, 900)
        time.sleep(0.4)
    time.sleep(2)
    page.evaluate("window.scrollTo(0,0)")
    time.sleep(1)
    figs = page.query_selector_all("figure")
    P("figures:", len(figs))
    os.makedirs("cap", exist_ok=True)
    for i, f in enumerate(figs, 1):
        try:
            f.scroll_into_view_if_needed()
            time.sleep(0.8)
            bbox = f.bounding_box()
            P(i, "bbox", bbox)
            f.screenshot(path="cap/fig%02d.png" % i)
            P(i, "saved")
        except Exception as e:
            P(i, "ERR", repr(e))
    # figure 1 animation frames
    try:
        f1 = figs[0]
        f1.scroll_into_view_if_needed()
        time.sleep(0.5)
        btns = f1.query_selector_all("button")
        P("fig1 buttons:", len(btns))
        for b in btns:
            P("  btn:", (b.get_attribute("aria-label") or b.inner_text() or "")[:60])
    except Exception as e:
        P("btn err", repr(e))
    page.screenshot(path="cap/_full.png", full_page=False)
    browser.close()
open("_cap.txt", "w", encoding="utf-8").write("\n".join(log))
print("done")

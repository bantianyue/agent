# -*- coding: utf-8 -*-
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
D=Path(r"D:/06_Hermes/articles/glm53-hisparse-vllm-part1")
jobs=[("one-pool-two-requests.svg","fig01.png"),
      ("residency-states.svg","fig02.png")] if False else [
("one-pool-two-requests.svg","fig01.png"),
("three-residency-states.svg","fig02.png"),
("pareto-occupancy.svg","fig03.png")]
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_page(viewport={"width":2000,"height":900}, device_scale_factor=2)
    for src,out in jobs:
        url=(D/src).as_uri()
        pg.goto(url, wait_until="load", timeout=60000)
        pg.wait_for_timeout(1200)
        # size to width 1000 (crisp) preserving aspect: set svg width px per its viewBox ratio via css
        pg.evaluate("""()=>{const s=document.querySelector('svg');if(s){const vb=(s.viewBox&&s.viewBox.baseVal)?s.viewBox.baseVal:null; if(vb){const h=Math.round(1100*vb.height/vb.width); s.style.width='1100px'; s.style.height=h+'px';} else {s.style.width='1100px';}}}""")
        pg.wait_for_timeout(400)
        loc=pg.locator('svg').screenshot(path=str(D/out))
        print("wrote",out)
    b.close()
print("done")

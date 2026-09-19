import os
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops
URL="https://mlc.ai/modern-gpu-programming-for-mlsys/demo/pipeline_arch.html"
TMP=r"D:\06_Hermes\articles\mlc-gpu-execution-model\_dbg"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True, proxy={"server":"http://127.0.0.1:7890"})
    pg=b.new_page(viewport={"width":1000,"height":800})
    pg.goto(URL, wait_until="load", timeout=60000)
    pg.wait_for_timeout(1500)
    print("stage boxes:", pg.eval_on_selector_all(".stage-box","els=>els.map(e=>e.getAttribute('data-stage')||e.textContent.trim())"))
    pg.screenshot(path=TMP+r"\a.png", clip={"x":8,"y":78,"width":984,"height":556})
    for i in [0,1,2]:
        pg.evaluate("(i)=>{document.querySelectorAll('.stage-box')[i].click()}", i)
        pg.wait_for_timeout(500)
        print(i, "panel:", pg.inner_text("#dpBody")[:60].replace("\n"," "))
        pg.screenshot(path=TMP+("\\b%d.png"%i), clip={"x":8,"y":78,"width":984,"height":556})
        d=ImageChops.difference(Image.open(TMP+r"\a.png").convert("RGB"),Image.open(TMP+("\\b%d.png"%i)).convert("RGB"))
        print("   diff bbox:", d.getbbox())
    b.close()
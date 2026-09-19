import os,io
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops
URL="https://mlc.ai/modern-gpu-programming-for-mlsys/demo/pipeline_arch.html"
TMP=r"D:\06_Hermes\articles\mlc-gpu-execution-model\_dbg"
os.makedirs(TMP,exist_ok=True)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True, proxy={"server":"http://127.0.0.1:7890"})
    pg=b.new_page(viewport={"width":1000,"height":800}, device_scale_factor=1)
    errs=[]
    pg.on("console", lambda m: errs.append(m.type+":"+m.text[:120]))
    pg.on("pageerror", lambda e: errs.append("pageerror:"+str(e)[:200]))
    pg.goto(URL, wait_until="load", timeout=60000)
    pg.wait_for_timeout(2000)
    print("title:",pg.title())
    print("before panel:",pg.inner_text("#dpBody")[:80])
    pg.screenshot(path=os.path.join(TMP,"a.png"), clip={"x":8,"y":78,"width":984,"height":556})
    pg.click(".stage-box >> nth=0")
    pg.wait_for_timeout(600)
    print("after panel:",pg.inner_text("#dpBody")[:120])
    pg.screenshot(path=os.path.join(TMP,"b.png"), clip={"x":8,"y":78,"width":984,"height":556})
    d=ImageChops.difference(Image.open(os.path.join(TMP,"a.png")).convert("RGB"),Image.open(os.path.join(TMP,"b.png")).convert("RGB"))
    print("diff bbox:",d.getbbox())
    print("console:",errs[:6])
    b.close()
import os
from playwright.sync_api import sync_playwright
from PIL import Image
URL="https://mlc.ai/modern-gpu-programming-for-mlsys/demo/pipeline_arch.html"
OUT=r"D:\06_Hermes\articles\mlc-gpu-execution-model\fig04.gif"
TMP=r"D:\06_Hermes\articles\mlc-gpu-execution-model\_frames3"
os.makedirs(TMP,exist_ok=True)
for f in os.listdir(TMP): os.remove(os.path.join(TMP,f))
CLIP={"x":8,"y":78,"width":984,"height":556}
k=0
with sync_playwright() as p:
    b=p.chromium.launch(headless=True, proxy={"server":"http://127.0.0.1:7890"})
    pg=b.new_page(viewport={"width":1000,"height":800}, device_scale_factor=1)
    pg.goto(URL, wait_until="load", timeout=60000)
    pg.wait_for_timeout(2000)
    n=pg.eval_on_selector_all(".stage-box","els=>els.length")
    print("stage boxes:",n)
    def shot(times=1,gap=60):
        global k
        for _ in range(times):
            pg.screenshot(path=os.path.join(TMP,"f%03d.png"%k), clip=CLIP); k+=1
            pg.wait_for_timeout(gap)
    shot(6,80)                      # overview
    for i in range(n):
        pg.eval_on_selector_all(".stage-box", "(els,i)=>{els[i].click()}", i) if False else None
        pg.click(".stage-box >> nth=%d" % i)
        pg.wait_for_timeout(420)
        shot(6,80)
    pg.click(".stage-box >> nth=0")  # toggle off -> back to overview
    pg.wait_for_timeout(420)
    shot(6,80)
    b.close()
frames=[Image.open(os.path.join(TMP,f)).convert("RGB") for f in sorted(os.listdir(TMP))]
w,h=frames[0].size
nw=760; nh=int(h*nw/w)
frames=[im.resize((nw,nh), Image.LANCZOS) for im in frames]
pal=frames[0].quantize(colors=128)
q=[im.quantize(colors=128, palette=pal, dither=Image.FLOYDSTEINBERG) for im in frames]
q[0].save(OUT, save_all=True, append_images=q[1:], duration=80, loop=0, optimize=True)
import hashlib
hs={hashlib.md5(open(os.path.join(TMP,f),'rb').read()).hexdigest() for f in os.listdir(TMP)}
print("gif",OUT,os.path.getsize(OUT),(nw,nh),"frames",len(q),"distinct",len(hs))
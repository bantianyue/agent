import os
from playwright.sync_api import sync_playwright
from PIL import Image
URL="https://mlc.ai/modern-gpu-programming-for-mlsys/demo/pipeline_arch.html"
OUT=r"D:\06_Hermes\articles\mlc-gpu-execution-model\fig04.gif"
TMP=r"D:\06_Hermes\articles\mlc-gpu-execution-model\_frames2"
os.makedirs(TMP,exist_ok=True)
for f in os.listdir(TMP): os.remove(os.path.join(TMP,f))
CLIP={"x":8,"y":78,"width":984,"height":556}
with sync_playwright() as p:
    b=p.chromium.launch(headless=True, proxy={"server":"http://127.0.0.1:7890"})
    pg=b.new_page(viewport={"width":1000,"height":800}, device_scale_factor=1)
    pg.goto(URL, wait_until="load", timeout=60000)
    pg.wait_for_timeout(2500)
    for i in range(48):
        pg.screenshot(path=os.path.join(TMP,"f%03d.png"%i), clip=CLIP)
        pg.wait_for_timeout(85)
    b.close()
frames=[Image.open(os.path.join(TMP,f)).convert("RGB") for f in sorted(os.listdir(TMP))]
w,h=frames[0].size
nw=760; nh=int(h*nw/w)
frames=[im.resize((nw,nh), Image.LANCZOS) for im in frames]
pal=frames[0].quantize(colors=128)
q=[im.quantize(colors=128, palette=pal, dither=Image.FLOYDSTEINBERG) for im in frames]
q[0].save(OUT, save_all=True, append_images=q[1:], duration=85, loop=0, optimize=True)
print("gif",OUT,os.path.getsize(OUT),(nw,nh),len(q))
# sanity: distinct frames count (animation check)
import hashlib
hs={hashlib.md5(open(os.path.join(TMP,f),'rb').read()).hexdigest() for f in os.listdir(TMP)}
print("distinct frames:",len(hs))
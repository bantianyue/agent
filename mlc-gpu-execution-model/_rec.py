import io,os,sys,time
from playwright.sync_api import sync_playwright
from PIL import Image

URL="https://mlc.ai/modern-gpu-programming-for-mlsys/demo/pipeline_arch.html"
OUT=r"D:\06_Hermes\articles\mlc-gpu-execution-model\fig04.gif"
TMP=r"D:\06_Hermes\articles\mlc-gpu-execution-model\_frames"
os.makedirs(TMP,exist_ok=True)
for f in os.listdir(TMP): os.remove(os.path.join(TMP,f))

with sync_playwright() as p:
    b=p.chromium.launch(headless=True, proxy={"server":"http://127.0.0.1:7890"})
    pg=b.new_page(viewport={"width":900,"height":1100}, device_scale_factor=1)
    pg.goto(URL, wait_until="load", timeout=60000)
    pg.wait_for_timeout(2500)
    # find the main visual container
    box=pg.evaluate("""() => {
      const c = document.querySelector('.stage, .scene, #stage, svg, .wrap') || document.body;
      const r = c.getBoundingClientRect();
      return {x:Math.max(0,r.x), y:Math.max(0,r.y), w:r.width, h:r.height};
    }""")
    print("box",box)
    n=48
    for i in range(n):
        pg.screenshot(path=os.path.join(TMP,"f%03d.png"%i), clip={"x":box["x"],"y":box["y"],"width":box["w"],"height":box["h"]})
        pg.wait_for_timeout(90)
    b.close()

frames=[]
for f in sorted(os.listdir(TMP)):
    im=Image.open(os.path.join(TMP,f)).convert("RGB")
    frames.append(im)
w,h=frames[0].size
nw=760; nh=int(h*nw/w)
frames=[im.resize((nw,nh), Image.LANCZOS) for im in frames]
pal=frames[0].quantize(colors=128, method=Image.MEDIANCUT)
q=[im.quantize(colors=128, palette=pal, dither=Image.FLOYDSTEINBERG) for im in frames]
q[0].save(OUT, save_all=True, append_images=q[1:], duration=90, loop=0, optimize=True)
print("gif",OUT,os.path.getsize(OUT),(nw,nh),len(q))
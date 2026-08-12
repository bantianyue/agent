import os, pathlib, numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

base = r"D:\06_Hermes\articles\lmsys-unified-radix-cache"
svg_files = ["image1","image2","image3","image6"]
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width":1500,"height":900})
    for f in svg_files:
        src = os.path.join(base, f+".svg")
        out = os.path.join(base, f+"_raw.png")
        try:
            page.goto(pathlib.Path(src).as_uri())
            page.wait_for_timeout(800)
            el = page.query_selector("svg")
            box = el.bounding_box() if el else None
            if box:
                page.screenshot(clip={"x":box["x"],"y":box["y"],"width":box["width"],"height":box["height"]}, path=out)
            else:
                page.screenshot(path=out, full_page=True)
            print(f"OK {f} bbox={box}")
        except Exception as e:
            print(f"FAIL {f}: {str(e)[:60]}")
    browser.close()

# crop 白边
for f in svg_files:
    p=os.path.join(base,f+"_raw.png")
    if not os.path.exists(p): continue
    im=Image.open(p).convert('RGB')
    a=np.array(im.convert('L'))
    nw=(a<245)
    rows=nw.any(axis=1); cols=nw.any(axis=0)
    if rows.any():
        r0,r1=rows.argmax(),len(rows)-rows[::-1].argmax()-1
        c0,c1=cols.argmax(),len(cols)-cols[::-1].argmax()-1
        pad=6
        im=im.crop((max(0,c0-pad),max(0,r0-pad),min(im.size[0],c1+pad),min(im.size[1],r1+pad)))
    # 统一命名 figNN（按论文/博客图顺序: fig01=image1, fig02=image2, fig03=image3, fig06=image6）
    order={"image1":"fig01","image2":"fig02","image3":"fig03","image6":"fig05"}
    im.save(os.path.join(base, order[f]+".png"))
    print(f"crop {order[f]}.png {im.size}")
print("done")

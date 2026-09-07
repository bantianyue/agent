import os, numpy as np, re
from PIL import Image
from playwright.sync_api import sync_playwright

ART = r"D:/06_Hermes/articles/ultrascale-p3-ring-pp-expert"
svgs = ["cp_attnmask.svg", "cp_zigzagmask.svg", "5d_full.svg"]
VIEWBOX = re.compile(r'<svg[^>]*viewBox="([\d\.\- ]+)"', re.I)

def autocrop_nptrim(im, pad=6, thresh=248):
    im = im.convert("RGB")
    a = np.array(im.convert("L"))
    nw = a < thresh
    rows = nw.any(axis=1); cols = nw.any(axis=0)
    if not rows.any():
        return im
    r0, r1 = rows.argmax(), len(rows) - rows[::-1].argmax() - 1
    c0, c1 = cols.argmax(), len(cols) - cols[::-1].argmax() - 1
    return im.crop((max(0, c0-pad), max(0, r0-pad), min(im.size[0], c1+pad), min(im.size[1], r1+pad)))

with sync_playwright() as p:
    browser = p.chromium.launch()
    for svg in svgs:
        path = os.path.join(ART, svg)
        text = open(path, encoding="utf-8").read()
        W = 1600
        html = ('<!DOCTYPE html><html><head><meta charset="utf-8">'
                '<style>html,body{margin:0;padding:0;background:#fff}'
                f'svg{{width:{W}px;height:auto;display:block}}</style>'
                '</head><body>%s</body></html>' % text)
        page = browser.new_page(viewport={"width": W + 40, "height": 2600})
        page.set_content(html, wait_until="load")
        page.wait_for_timeout(700)
        page.locator("svg").screenshot(path=os.path.join(ART, svg.replace(".svg", "_raw.png")))
        page.close()
    browser.close()

for svg in svgs:
    raw = os.path.join(ART, svg.replace(".svg", "_raw.png"))
    if not os.path.exists(raw):
        print("missing", raw); continue
    im2 = autocrop_nptrim(Image.open(raw))
    sc = 1600 / im2.size[0]
    if sc > 1:
        im2 = im2.resize((int(im2.size[0]*sc), int(im2.size[1]*sc)), Image.LANCZOS)
    out = os.path.join(ART, svg.replace(".svg", ".png"))
    im2.save(out)
    a = np.array(im2.convert("L"))
    print(f"{svg} => {im2.size} nonwhite%={round(100.0*(a<250).mean(),2)}")
    os.remove(raw)
print("DONE")

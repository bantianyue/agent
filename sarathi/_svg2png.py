# -*- coding: utf-8 -*-
import os, re, json, glob
from playwright.sync_api import sync_playwright
from PIL import Image

ART = r"D:\06_Hermes\articles\sarathi"
svgs = sorted(glob.glob(os.path.join(ART, "src*.svg")))
TARGET_W = 2400
MAX_OUT_W = 1400

log = []
with sync_playwright() as p:
    br = p.chromium.launch()
    pg = br.new_page(viewport={"width": 2600, "height": 1600})
    for s in svgs:
        name = os.path.basename(s)
        outp = os.path.join(ART, name[:-4] + ".png")
        txt = open(s, encoding="utf-8", errors="ignore").read()
        # strip xml decl
        txt = re.sub(r"<\?xml[^>]*\?>", "", txt)
        wrapper = "<html><body style='margin:0;padding:0;background:#fff'><div id='host'>" + txt + "</div></body></html>"
        tmp = os.path.join(ART, "_tmpwrap.html")
        open(tmp, "w", encoding="utf-8").write(wrapper)
        try:
            pg.goto("file:///" + tmp.replace("\\", "/"))
            pg.wait_for_timeout(400)
            els = pg.query_selector_all("#host svg")
            if not els:
                log.append("NOSVG " + name)
                continue
            el = els[0]
            pg.evaluate(
                """([el, W]) => {
                    el.removeAttribute('height');
                    el.setAttribute('width', String(W));
                    el.style.width = W + 'px';
                    el.style.height = 'auto';
                    el.style.display = 'block';
                    if (!el.getAttribute('viewBox')) {
                        const b = el.getBBox();
                        el.setAttribute('viewBox', `${b.x} ${b.y} ${b.width} ${b.height}`);
                    }
                    el.setAttribute('preserveAspectRatio', 'xMidYMid meet');
                }""", [el, TARGET_W])
            pg.wait_for_timeout(300)
            el.screenshot(path=outp)
            im = Image.open(outp)
            w, h = im.size
            if w > MAX_OUT_W:
                nh = int(h * MAX_OUT_W / w)
                im = im.convert("RGB").resize((MAX_OUT_W, nh), Image.LANCZOS)
                im.save(outp, "PNG", optimize=True)
            size = os.path.getsize(outp)
            log.append("OK %s -> %s %sx%s %d KB" % (name, os.path.basename(outp), w, h, size // 1024))
        except Exception as e:
            log.append("ERR %s %s" % (name, e))
    br.close()

open(os.path.join(ART, "_svg_out.txt"), "w", encoding="utf-8").write("\n".join(log))
print("done")

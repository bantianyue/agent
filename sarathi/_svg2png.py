# -*- coding: utf-8 -*-
import os, re, glob, traceback
from playwright.sync_api import sync_playwright
from PIL import Image

ART = r"D:\06_Hermes\articles\sarathi"
LOG = os.path.join(ART, "_svg_out.txt")
if os.path.exists(LOG):
    os.remove(LOG)

def rec(s):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(s + "\n")

svgs = sorted(glob.glob(os.path.join(ART, "src*.svg")))
TARGET_W = 2400
MAX_OUT_W = 1400

try:
    pw = sync_playwright().start()
    br = pw.chromium.launch()
    pg = br.new_page(viewport={"width": 2600, "height": 1600})
    rec("browser ok")
    for s in svgs:
        name = os.path.basename(s)
        try:
            outp = os.path.join(ART, name[:-4] + ".png")
            txt = open(s, encoding="utf-8", errors="ignore").read()
            txt = re.sub(r"<\?xml[^>]*\?>", "", txt)
            txt = re.sub(r"<!DOCTYPE[^>]*>", "", txt)
            wrapper = ("<html><body style='margin:0;padding:0;background:#fff'>"
                       "<div id='host'>" + txt + "</div></body></html>")
            tmp = os.path.join(ART, "_tmpwrap.html")
            open(tmp, "w", encoding="utf-8").write(wrapper)
            pg.goto("file:///" + tmp.replace("\\", "/"))
            pg.wait_for_timeout(400)
            els = pg.query_selector_all("#host svg")
            if not els:
                rec("NOSVG " + name)
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
                        el.setAttribute('viewBox', b.x + ' ' + b.y + ' ' + b.width + ' ' + b.height);
                    }
                    el.setAttribute('preserveAspectRatio', 'xMidYMid meet');
                }""", [el, TARGET_W])
            pg.wait_for_timeout(300)
            el.screenshot(path=outp)
            im = Image.open(outp)
            w, h = im.size
            im2 = im.convert("RGB")
            if w > MAX_OUT_W:
                nh = int(h * MAX_OUT_W / w)
                im2 = im2.resize((MAX_OUT_W, nh), Image.LANCZOS)
            im2.save(outp, "PNG", optimize=True)
            rec("OK %s %dx%d %dKB" % (name, w, h, os.path.getsize(outp) // 1024))
        except Exception:
            rec("ERR %s\n%s" % (name, traceback.format_exc()))
    rec("ALLDONE")
except Exception:
    rec("FATAL\n" + traceback.format_exc())

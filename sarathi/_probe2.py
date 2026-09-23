# -*- coding: utf-8 -*-
import os, traceback
LOG = r"D:\06_Hermes\articles\sarathi\_probe2_out.txt"

def rec(s):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(s + "\n")

if os.path.exists(LOG):
    os.remove(LOG)
rec("start")
try:
    from playwright.sync_api import sync_playwright
    rec("import ok")
    with sync_playwright() as p:
        rec("ctx ok")
        br = p.chromium.launch()
        rec("launch ok")
        pg = br.new_page()
        pg.set_content("<svg width='100' height='50'><rect width='100' height='50' fill='red'/></svg>")
        rec("content ok")
        pg.screenshot(path=r"D:\06_Hermes\articles\sarathi\_test.png")
        rec("shot ok")
        br.close()
    rec("done")
except Exception:
    rec("EXC\n" + traceback.format_exc())

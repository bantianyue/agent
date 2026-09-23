# -*- coding: utf-8 -*-
import os, sys, traceback
LOG = r"D:\06_Hermes\articles\sarathi\_probe2_out.txt"
buf = []
def rec(*a):
    buf.append(" ".join(str(x) for x in a))
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
except Exception:
    rec("EXC\n" + traceback.format_exc())
open(LOG, "w", encoding="utf-8").write("\n".join(buf))

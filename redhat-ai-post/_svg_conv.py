import sys, os, pathlib
from playwright.sync_api import sync_playwright

base = r"D:\06_Hermes\articles\redhat-ai-post"
files = ["hero","fig01","fig02"]
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width":1500,"height":900})
    for f in files:
        src = os.path.join(base, f+".svg")
        out = os.path.join(base, f+"_c.png")
        try:
            page.goto(pathlib.Path(src).as_uri())
            page.wait_for_timeout(800)
            el = page.query_selector("svg")
            if el:
                box = el.bounding_box()
                if box:
                    page.screenshot(clip={ "x": box["x"], "y": box["y"], "width": box["width"], "height": box["height"]}, path=out)
                else:
                    page.screenshot(path=out, full_page=True)
            else:
                page.screenshot(path=out, full_page=True)
            print(f"OK {f}")
        except Exception as e:
            print(f"FAIL {f}: {str(e)[:60]}")
    browser.close()
print("done")
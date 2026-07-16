import sys, json, time
from playwright.sync_api import sync_playwright

ART = "D:/06_Hermes/articles/introducing-inkling"
URL = "https://thinkingmachines.ai/news/introducing-inkling/"

def main():
    with sync_playwright() as p:
        # connect to running Chrome on 9222
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        ctx = browser.contexts[0]
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2500)
        # scroll through to trigger lazy render
        for y in range(0, 12):
            page.mouse.wheel(0, 900)
            page.wait_for_timeout(400)
        page.wait_for_timeout(1500)
        # count figures
        n = page.eval_on_selector_all("figure", "els => els.length")
        print("FIGURES:", n)
        captions = page.eval_on_selector_all("figure", """els => els.map(f => {
            const fc = f.querySelector('figcaption');
            return fc ? fc.innerText : '';
        })""")
        for i,c in enumerate(captions):
            print(f"--- Fig {i} ---")
            print(c[:120])
        # screenshot each figure
        for i in range(n):
            try:
                sel = f"figure >> nth={i}"
                el = page.query_selector_all("figure")[i]
                # try to click any "Result" tab to show the demo
                path = f"{ART}/fig{i:02d}.png"
                el.screenshot(path=path)
                print(f"saved fig{i:02d}.png")
            except Exception as e:
                print(f"fig{i:02d} FAIL: {e}")
        browser.close()

if __name__ == "__main__":
    main()

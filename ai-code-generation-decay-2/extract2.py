from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    
    target_page = None
    for ctx in browser.contexts:
        for pg in ctx.pages:
            if "0xCodez" in pg.url:
                target_page = pg
                break
        if target_page:
            break
    
    if target_page:
        # Get remaining text
        full_text = target_page.evaluate("document.body.innerText")
        # Get the tail end
        print(full_text[15000:])
        
        # Also get article content specifically
        print("\n\n=== ALL DIV DATA-TESTID ===")
        all_divs = target_page.evaluate("""
            () => Array.from(document.querySelectorAll('div[data-testid]')).map(el => ({
                testid: el.getAttribute('data-testid'),
                text: el.innerText.substring(0, 100)
            }))
        """)
        for d in all_divs:
            print(json.dumps(d, ensure_ascii=False))
    
    browser.close()

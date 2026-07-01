from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    
    target_page = None
    for ctx in browser.contexts:
        for pg in ctx.pages:
            if "2063403172383649792" in pg.url or "polydao" in pg.url:
                target_page = pg
                print(f"Found: {pg.url[:120]}")
                break
        if target_page:
            break
    
    if target_page is None:
        print("Checking all pages...")
        for ctx in browser.contexts:
            for pg in ctx.pages:
                print(f"  {pg.url[:120]}")
    
    if target_page:
        target_page.wait_for_timeout(5000)
        
        full_text = target_page.evaluate("document.body.innerText")
        print("=== FULL TEXT ===")
        print(full_text[:25000])
        
        # Get images
        imgs = target_page.evaluate("""
            () => Array.from(document.querySelectorAll('img[src*="pbs.twimg.com"]')).map(img => ({
                src: img.src,
                alt: img.alt,
                w: img.naturalWidth,
                h: img.naturalHeight
            }))
        """)
        print("\n=== IMAGES ===")
        for img in imgs:
            print(json.dumps(img))
        
        print(f"\nTitle: {target_page.title()}")
        print(f"URL: {target_page.url}")
    
    browser.close()

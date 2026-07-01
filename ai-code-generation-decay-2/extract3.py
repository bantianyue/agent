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
        # Get rich text view full content
        rich_text = target_page.evaluate("""
            () => {
                const el = document.querySelector('[data-testid="twitterArticleRichTextView"]');
                if (el) return el.innerText;
                return null;
            }
        """)
        print("=== RICH TEXT VIEW ===")
        print(rich_text[:20000] if rich_text else "Not found")
        
        # Also get the full body text
        full_text = target_page.evaluate("document.body.innerText")
        print("\n=== FULL TEXT (last 5000) ===")
        print(full_text[-5000:])
    
    browser.close()

from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    
    # Find the article tab
    target_page = None
    for ctx in browser.contexts:
        for pg in ctx.pages:
            url = pg.url
            if "2064357550225510400" in url or "0xCodez" in url:
                target_page = pg
                print(f"Found target: {url[:120]}")
                break
        if target_page:
            break
    
    if target_page is None:
        print("No matching page found, checking all pages...")
        for ctx in browser.contexts:
            for pg in ctx.pages:
                print(f"  {pg.url[:120]}")
    
    if target_page:
        target_page.wait_for_timeout(5000)
        
        # Get full article text
        full_text = target_page.evaluate("document.body.innerText")
        print("=== FULL TEXT ===")
        print(full_text[:20000])
        
        # Try article element
        article_text = target_page.evaluate("""
            () => {
                const article = document.querySelector('article');
                if (article) return article.innerText;
                return null;
            }
        """)
        print("\n=== ARTICLE ELEMENT ===")
        print(article_text[:15000] if article_text else "No article element found")
        
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
        
        print(f"\nPage title: {target_page.title()}")
        print(f"Page URL: {target_page.url}")
    
    browser.close()

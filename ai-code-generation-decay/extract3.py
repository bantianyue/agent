from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    # Connect to existing CDP Chrome (already logged into X)
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    
    # Find the article tab
    target_page = None
    for page in browser.contexts[0].pages if browser.contexts else []:
        pass
    
    # Get all pages across all contexts
    all_pages = []
    for ctx in browser.contexts:
        all_pages.extend(ctx.pages)
    
    print(f"Total pages: {len(all_pages)}")
    for pg in all_pages:
        url = pg.url
        if "Mnilax" in url or "2064425685834207232" in url:
            target_page = pg
            print(f"Found target: {url[:120]}")
            break
    
    if target_page is None and all_pages:
        # Try the first page that has article content
        for pg in all_pages:
            if "article" in pg.url.lower() or "status" in pg.url.lower():
                target_page = pg
                print(f"Using page: {pg.url[:120]}")
                break
    
    if target_page is None:
        # Open a new tab via CDP
        print("Opening new tab...")
        import requests
        resp = requests.put("http://localhost:9222/json/new?https://x.com/i/article/2064425685834207232")
        tab_info = resp.json()
        tab_id = tab_info["id"]
        
        # Wait and find it
        import time
        time.sleep(8)
        
        # Re-connect to find the new page
        browser.close()
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        for ctx in browser.contexts:
            for pg in ctx.pages:
                if "2064425685834207232" in pg.url or "Mnilax" in pg.url:
                    target_page = pg
                    print(f"Found new page: {pg.url[:120]}")
                    break
    
    if target_page:
        target_page.wait_for_timeout(5000)
        
        # Get full article text
        full_text = target_page.evaluate("document.body.innerText")
        print("=== FULL TEXT ===")
        print(full_text[:15000])
        
        # Try to get article content specifically
        article_text = target_page.evaluate("""
            () => {
                const article = document.querySelector('article');
                if (article) return article.innerText;
                return null;
            }
        """)
        print("\n=== ARTICLE ELEMENT ===")
        print(article_text[:10000] if article_text else "No article element found")
        
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
        
        # Get page title
        print(f"\nPage title: {target_page.title()}")
        print(f"Page URL: {target_page.url}")
    else:
        print("Could not find or create target page")
    
    browser.close()

from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch(
        channel="chrome",
        headless=True,
        proxy={"server": "http://127.0.0.1:7890"}
    )
    context = browser.new_context(
        viewport={"width": 1280, "height": 720}
    )
    page = context.new_page()
    
    # Try the status URL instead
    page.goto("https://x.com/Mnilax/status/2064447011953225770", 
              wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(10000)
    
    # Take a screenshot to see what's happening
    page.screenshot(path="screenshot.png", full_page=True)
    
    # Get page title
    title = page.title()
    print(f"Page title: {title}")
    print(f"URL: {page.url}")
    
    # Check for login wall
    body_text = page.eval_on_selector("body", "el => el.innerText.substring(0, 2000)")
    print(f"Body text (first 2000): {body_text}")
    
    # Get all text
    full_text = page.eval_on_selector("body", "el => el.innerText")
    print(f"\n=== FULL BODY TEXT ===")
    print(full_text[:10000])
    
    # Get images
    imgs = page.eval_on_selector_all("img[src*=\"pbs.twimg.com\"]",
        "els => els.map(el => ({src: el.src, alt: el.alt, w: el.naturalWidth, h: el.naturalHeight}))")
    
    print(f"\n=== IMAGES ===")
    for img in imgs:
        print(json.dumps(img))
    
    browser.close()

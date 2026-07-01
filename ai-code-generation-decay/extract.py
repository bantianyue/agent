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
    
    page.goto("https://x.com/i/article/2064425685834207232", 
              wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(10000)
    
    # Get article text
    article_texts = page.eval_on_selector_all("article",
        "els => els.map(el => el.innerText)")
    
    # Get tweet text
    tweet_texts = page.eval_on_selector_all("[data-testid=\"tweetText\"]",
        "els => els.map(el => el.textContent)")
    
    # Get Article rich text
    rich_text = page.eval_on_selector_all("[data-testid=\"twitterArticleRichTextView\"]",
        "els => els.map(el => el.textContent)")
    
    # Get all div data-testid for debugging
    all_divs = page.eval_on_selector_all("div[data-testid]",
        "els => els.map(el => ({testid: el.getAttribute('data-testid'), text: el.innerText.substring(0, 200)}))")
    
    # Get images
    imgs = page.eval_on_selector_all("img[src*=\"pbs.twimg.com\"]",
        "els => els.map(el => ({src: el.src, alt: el.alt, w: el.naturalWidth, h: el.naturalHeight}))")
    
    print("=== ARTICLE TEXTS ===")
    for i, t in enumerate(article_texts):
        print(f"--- Article {i} ---")
        print(t[:8000])
        print()
    
    print("=== TWEET TEXTS ===")
    for i, t in enumerate(tweet_texts):
        print(f"--- Tweet {i} ---")
        print(t[:3000])
        print()
    
    print("=== RICH TEXT ===")
    for i, t in enumerate(rich_text):
        print(f"--- Rich Text {i} ---")
        print(t[:8000])
        print()
    
    print("=== ALL DIVS ===")
    for d in all_divs:
        print(json.dumps(d, ensure_ascii=False))
    
    print("=== IMAGES ===")
    for img in imgs:
        print(json.dumps(img))
    
    browser.close()

import asyncio, os, json
from playwright.async_api import async_playwright

ARTICLE_URL = "https://x.com/mem0ai/status/2071990201531118063"
ARTICLE_DIR = r"D:\06_Hermes\articles\chatgpt-memory-works"
PROXY = "http://127.0.0.1:7890"

async def main():
    async with async_playwright() as p:
        # 用独立 profile 目录启动，避免冲突
        test_profile = os.path.join(ARTICLE_DIR, "_chrome_test_profile")
        os.makedirs(test_profile, exist_ok=True)
        
        context = await p.chromium.launch_persistent_context(
            test_profile,
            channel="chrome",
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
            ],
            proxy={"server": PROXY},
            viewport={"width": 1280, "height": 4000},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        print("Navigating to X article...")
        await page.goto(ARTICLE_URL, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(10)
        
        # 看是否被要求登录
        page_text = await page.evaluate("() => document.body.innerText.substring(0, 200)")
        print(f"Page preview: {page_text[:200]}")
        
        if 'Log in' in page_text or 'Sign up' in page_text:
            print("X requires login. Checking for article elements anyway...")
        
        # 提取所有图片
        imgs = await page.evaluate("""
            () => {
                const imgs = Array.from(document.querySelectorAll('img'));
                return imgs.map(i => ({
                    src: i.src,
                    alt: i.alt || '',
                    w: i.naturalWidth,
                    h: i.naturalHeight,
                    complete: i.complete,
                }));
            }
        """)
        
        print(f"\n=== Found {len(imgs)} images ===")
        for idx, img in enumerate(imgs):
            print(f"  [{idx}] complete={img['complete']} | {img['w']}x{img['h']} | {img['alt'][:50]} | {img['src'][:120]}")
        
        # 找 pbs.twimg.com/media
        twimg_media = [i for i in imgs if 'pbs.twimg.com/media' in i['src']]
        print(f"\n=== pbs.twimg.com/media: {len(twimg_media)} ===")
        for idx, img in enumerate(twimg_media):
            print(f"  [{idx}] {img['w']}x{img['h']} | {img['src']}")
        
        # 截图保存
        await page.screenshot(path=os.path.join(ARTICLE_DIR, "page_render.png"), full_page=True)
        print("\nFull page screenshot saved.")
        
        # 如果需要登录，尝试注入 cookies
        if 'Log in' in page_text:
            print("\nNeed login. Trying to use cookies from browser...")
            # 尝试从已安装的浏览器提取 X cookies
            try:
                cookies = await context.cookies()
                print(f"Current cookies: {len(cookies)}")
                for c in cookies:
                    if 'x.com' in c.get('domain','') or 'twitter' in c.get('domain',''):
                        print(f"  {c['name']}: {c['value'][:20]}...")
            except:
                pass
        
        await context.close()

asyncio.run(main())

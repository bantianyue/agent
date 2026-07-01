import asyncio, os, json, re
from playwright.async_api import async_playwright

ARTICLE_URL = "https://x.com/mem0ai/status/2071990201531118063"
ARTICLE_DIR = r"D:\06_Hermes\articles\chatgpt-memory-works"
PROXY = "http://127.0.0.1:7890"

# 用用户已登录的 Chrome profile（X 已登录）
CHROME_PROFILE = r"C:\Users\twfehh7\AppData\Local\Google\Chrome\User Data"

async def main():
    async with async_playwright() as p:
        # 用 persistent context 加载用户 profile
        context = await p.chromium.launch_persistent_context(
            CHROME_PROFILE,
            channel="chrome",
            headless=False,
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
        await page.goto(ARTICLE_URL, wait_until="domcontentloaded", timeout=45000)
        await asyncio.sleep(8)
        
        # 截全页长图
        print("Screenshotting full page...")
        await page.screenshot(path=os.path.join(ARTICLE_DIR, "full_page.png"), full_page=True)
        print("Full page screenshot saved.")
        
        # 提取所有可见图片
        imgs = await page.evaluate("""
            () => {
                const imgs = Array.from(document.querySelectorAll('img'));
                return imgs.filter(i => i.naturalWidth > 0).map(i => ({
                    src: i.src,
                    alt: i.alt || '',
                    w: i.naturalWidth,
                    h: i.naturalHeight,
                }));
            }
        """)
        
        print(f"\n=== Found {len(imgs)} images ===")
        for idx, img in enumerate(imgs):
            print(f"  [{idx}] {img['w']}x{img['h']} | {img['alt'][:60]} | {img['src'][:120]}")
        
        # 过滤出正文图片（非头像、非图标、宽>100px）
        body_imgs = [i for i in imgs if i['w'] > 100 and i['h'] > 100 and 'emoji' not in i['src'] and 'profile_images' not in i['src']]
        print(f"\n=== Body images: {len(body_imgs)} ===")
        for idx, img in enumerate(body_imgs):
            print(f"  [{idx}] {img['w']}x{img['h']} | {img['alt'][:50]} | {img['src'][:120]}")
        
        # 如果是 pbs.twimg.com 的图片，用 name=orig 下载
        twimg = [i for i in body_imgs if 'pbs.twimg.com/media' in i['src']]
        print(f"\n=== pbs.twimg.com media: {len(twimg)} ===")
        for idx, img in enumerate(twimg):
            print(f"  [{idx}] {img['src']}")
            # 下载
            dl_url = img['src'] + '?name=orig' if '?' not in img['src'] else re.sub(r'name=[^&]+', 'name=orig', img['src'])
            fname = f"img{idx+1}.jpg"
            fpath = os.path.join(ARTICLE_DIR, fname)
            print(f"     Downloading -> {fname}")
            await page.evaluate("""
                async (args) => {
                    const [url, path] = args;
                    const resp = await fetch(url);
                    const blob = await resp.blob();
                    const reader = new FileReader();
                    return new Promise((resolve) => {
                        reader.onload = () => {
                            const base64 = reader.result.split(',')[1];
                            const el = document.createElement('a');
                            el.href = 'data:application/octet-stream;base64,' + base64;
                            el.download = path.split('/').pop();
                            document.body.appendChild(el);
                            el.click();
                            document.body.removeChild(el);
                            resolve('ok');
                        };
                        reader.readAsDataURL(blob);
                    });
                }
            """, [dl_url, fpath])
            print(f"     Done.")
        
        # 如果没有 twimg 图片，截图正文区域
        if not twimg:
            print("\nNo twimg media found. Screenshotting article area...")
            # 找 article 或 main 元素
            article_box = await page.query_selector('article')
            if article_box:
                await article_box.screenshot(path=os.path.join(ARTICLE_DIR, "article_content.png"))
                print("Article content screenshot saved.")
            else:
                # 截图页面正文区域
                await page.screenshot(path=os.path.join(ARTICLE_DIR, "page_content.png"), full_page=False)
                print("Page content screenshot saved.")
        
        # 提取正文文本
        text = await page.evaluate("""
            () => {
                const article = document.querySelector('article');
                return article ? article.innerText : document.body.innerText;
            }
        """)
        print(f"\n=== Article text (first 3000 chars) ===")
        print(text[:3000])
        
        await context.close()

asyncio.run(main())

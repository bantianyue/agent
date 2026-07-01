import asyncio, json, os
from playwright.async_api import async_playwright

ARTICLE_URL = "https://x.com/i/article/2071987942659383296"
ARTICLE_DIR = r"D:\06_Hermes\articles\chatgpt-memory-works"
PROXY = "http://127.0.0.1:7890"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            channel="chrome",
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            proxy={"server": PROXY}
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 8000},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        print("Navigating to article...")
        await page.goto(ARTICLE_URL, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(5)

        # 提取所有图片 URL
        imgs = await page.evaluate("""
            () => {
                const imgs = Array.from(document.querySelectorAll('img'));
                return imgs.filter(i => i.naturalWidth > 0).map(i => ({
                    src: i.src,
                    alt: i.alt || '',
                    w: i.naturalWidth,
                    h: i.naturalHeight,
                    cls: i.className
                }));
            }
        """)

        print(f"\n=== Found {len(imgs)} images ===")
        for idx, img in enumerate(imgs):
            print(f"  [{idx}] {img['w']}x{img['h']} | {img['alt'][:60]} | {img['src'][:120]}")

        # 特别找 pbs.twimg.com media 图片（正文内嵌图）
        twimg = [i for i in imgs if 'pbs.twimg.com/media' in i['src'] and 'profile' not in i['src']]
        print(f"\n=== Twitter media images (excl. avatars): {len(twimg)} ===")
        for idx, img in enumerate(twimg):
            print(f"  [{idx}] {img['w']}x{img['h']} | {img['src']}")

        # 找其他外部图片
        external = [i for i in imgs if 'pbs.twimg.com' not in i['src'] and i['w'] > 100]
        print(f"\n=== External images (width > 100px): {len(external)} ===")
        for idx, img in enumerate(external):
            print(f"  [{idx}] {img['w']}x{img['h']} | {img['alt'][:50]} | {img['src'][:120]}")

        # 提取正文
        text = await page.evaluate("""
            () => {
                const article = document.querySelector('article');
                return article ? article.innerText : document.body.innerText;
            }
        """)
        print(f"\n=== Page text (first 2000 chars) ===")
        print(text[:2000])

        # 如果有正文图片，下载它们
        media_urls = [i['src'] for i in twimg]
        if media_urls:
            print(f"\n=== Downloading {len(media_urls)} media images... ===")
            for idx, url in enumerate(media_urls):
                ext = url.split('?')[0].split('.')[-1] if '.' in url.split('?')[0] else 'jpg'
                # 用 name=orig 下载原图
                dl_url = url + '?name=orig' if '?' not in url else url.replace('name=small', 'name=orig').replace('name=thumb', 'name=orig')
                fname = f"img{idx+1}.{ext}"
                fpath = os.path.join(ARTICLE_DIR, fname)
                print(f"  Downloading {dl_url[:100]}... -> {fname}")
                # 用 page.evaluate 下载
                await page.evaluate("""
                    async (args) => {
                        const [url, path] = args;
                        const response = await fetch(url);
                        const buffer = await response.arrayBuffer();
                        const fs = require('fs');
                        fs.writeFileSync(path, Buffer.from(buffer));
                    }
                """, [dl_url, fpath])

        await browser.close()

asyncio.run(main())

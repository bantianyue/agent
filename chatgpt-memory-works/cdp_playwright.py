import asyncio, os, json, re
from playwright.async_api import async_playwright

ARTICLE_URL = "https://x.com/mem0ai/status/2071990201531118063"
ARTICLE_DIR = r"D:\06_Hermes\articles\chatgpt-memory-works"

async def main():
    async with async_playwright() as p:
        # 用 connect_over_cdp 连已启动的 Chrome
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        
        print("Connected to Chrome via CDP")
        
        # 获取所有页面
        contexts = browser.contexts
        pages = []
        for ctx in contexts:
            pages.extend(ctx.pages)
        
        print(f"Found {len(pages)} pages")
        
        # 找 X 页面
        target_page = None
        for page in pages:
            url = page.url
            if 'x.com' in url or 'twitter' in url:
                target_page = page
                print(f"Found X page: {url[:100]}")
                break
        
        if not target_page:
            print("No X page found, creating new tab...")
            target_page = await browser.new_page()
            await target_page.goto(ARTICLE_URL, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(5)
        else:
            # 如果已经在 X 页面上，刷新或确认
            if target_page.url != ARTICLE_URL:
                print(f"Navigating to article...")
                await target_page.goto(ARTICLE_URL, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(5)
        
        # 提取所有图片
        imgs = await target_page.evaluate("""
            () => {
                const imgs = Array.from(document.querySelectorAll('img'));
                return imgs.filter(i => i.complete && i.naturalWidth > 50)
                    .map(i => ({
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
        
        # 过滤正文图：排除头像、emoji、图标
        body_imgs = [i for i in imgs 
                     if i['w'] >= 150 and i['h'] >= 100
                     and 'profile_images' not in i['src']
                     and 'emoji' not in i['src']
                     and 'badge' not in i['src']]
        
        print(f"\n=== Body images ({len(body_imgs)}) ===")
        for idx, img in enumerate(body_imgs):
            print(f"  [{idx}] {img['w']}x{img['h']} | {img['alt'][:50]} | {img['src'][:120]}")
        
        # 下载图片
        os.makedirs(ARTICLE_DIR, exist_ok=True)
        for idx, img in enumerate(body_imgs):
            src = img['src']
            
            # 确定扩展名
            if 'format=jpg' in src: ext = 'jpg'
            elif 'format=png' in src: ext = 'png'
            elif 'format=gif' in src: ext = 'gif'
            elif '.jpg' in src or '.jpeg' in src: ext = 'jpg'
            elif '.png' in src: ext = 'png'
            else: ext = 'jpg'
            
            fname = f"img{idx+1}.{ext}"
            fpath = os.path.join(ARTICLE_DIR, fname)
            
            # 用 page.evaluate 通过浏览器下载
            dl_url = src
            if 'pbs.twimg.com/media' in src:
                dl_url = re.sub(r'name=[^&]+', 'name=orig', src) if 'name=' in src else src + '?name=orig'
            
            print(f"\n  Downloading [{idx}] {fname}")
            print(f"    URL: {dl_url[:100]}...")
            
            result = await target_page.evaluate("""
                async (args) => {
                    const [url, path] = args;
                    try {
                        const resp = await fetch(url);
                        const blob = await resp.blob();
                        const reader = new FileReader();
                        return await new Promise((resolve) => {
                            reader.onload = () => resolve(reader.result);
                            reader.readAsDataURL(blob);
                        });
                    } catch(e) {
                        return 'ERROR: ' + e.message;
                    }
                }
            """, [dl_url, fname])
            
            if result.startswith('ERROR'):
                print(f"    Failed: {result}")
            else:
                import base64
                header, encoded = result.split(',', 1)
                with open(fpath, 'wb') as f:
                    f.write(base64.b64decode(encoded))
                size = os.path.getsize(fpath) // 1024
                print(f"    Saved: {fname} ({size}KB)")
        
        # 截取文章内容
        screenshot_path = os.path.join(ARTICLE_DIR, "article_screenshot.png")
        await target_page.screenshot(path=screenshot_path, full_page=False)
        print(f"\nScreenshot saved: article_screenshot.png")
        
        # 提取正文文字
        text = await target_page.evaluate("""
            () => {
                const article = document.querySelector('article');
                return article ? article.innerText : document.body.innerText;
            }
        """)
        # 保存到文件
        text_path = os.path.join(ARTICLE_DIR, "article_text.txt")
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"\nArticle text saved: {len(text)} chars")
        
        await browser.close()

asyncio.run(main())

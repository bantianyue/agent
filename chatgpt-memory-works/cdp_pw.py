import asyncio, os, json, base64, re
from playwright.async_api import async_playwright

ARTICLE_URL = "https://x.com/mem0ai/status/2071990201531118063"
ARTICLE_DIR = r"D:\06_Hermes\articles\chatgpt-memory-works"

async def main():
    async with async_playwright() as p:
        # connect_over_cdp 连本地 9222
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        print("Connected via Playwright CDP!")
        
        # 获取所有页面
        contexts = browser.contexts
        all_pages = []
        for ctx in contexts:
            all_pages.extend(ctx.pages)
        print(f"Total pages: {len(all_pages)}")
        
        # 找 X 页面或创建新页面
        target = None
        for page in all_pages:
            url = page.url
            print(f"  Page: {url[:80]}")
            if "x.com" in url and "sw.js" not in url and "omnibox" not in url:
                target = page
        
        if not target:
            print("Creating new page...")
            target = await browser.new_page()
        
        # 导航到文章
        print(f"Navigating to article...")
        await target.goto(ARTICLE_URL, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(6)
        
        # 提取所有图片
        imgs = await target.evaluate("""
            () => {
                const imgs = Array.from(document.querySelectorAll('img'));
                return imgs.filter(i => i.complete && i.naturalWidth > 50)
                    .map(i => ({
                        src: i.src,
                        w: i.naturalWidth,
                        h: i.naturalHeight,
                        alt: (i.alt || '').substring(0, 80),
                        loaded: i.complete
                    }));
            }
        """)
        
        print(f"\n=== Found {len(imgs)} images ===")
        for idx, img in enumerate(imgs):
            print(f"  [{idx}] {img['w']}x{img['h']} | {img['alt'][:40]} | {img['src'][:120]}")
        
        # 过滤正文图
        body_imgs = [i for i in imgs 
                     if i['w'] >= 100 and i['h'] >= 80
                     and 'profile_images' not in i['src']
                     and 'emoji' not in i['src']
                     and 'favicon' not in i['src']
                     and 'omnibox' not in i['src']]
        
        print(f"\n=== Body images ({len(body_imgs)}) ===")
        for idx, img in enumerate(body_imgs):
            print(f"  [{idx}] {img['w']}x{img['h']} | {img['alt'][:40]} | {img['src'][:120]}")
        
        # 下载图片
        os.makedirs(ARTICLE_DIR, exist_ok=True)
        for idx, img in enumerate(body_imgs):
            src = img['src']
            
            m = re.search(r'\.(jpg|jpeg|png|gif|webp)(\?|$)', src)
            ext = m.group(1) if m else 'jpg'
            if ext == 'jpeg': ext = 'jpg'
            
            fname = f"img{idx+1}.{ext}"
            fpath = os.path.join(ARTICLE_DIR, fname)
            
            dl_url = src
            if 'pbs.twimg.com/media' in src:
                dl_url = re.sub(r'name=[^&]+', 'name=orig', src) if 'name=' in src else src + '?name=orig'
            
            print(f"\n  Download [{idx}] {fname}")
            
            result = await target.evaluate("""
                async (url) => {
                    try {
                        const r = await fetch(url);
                        const b = await r.blob();
                        const reader = new FileReader();
                        return await new Promise(r => { reader.onload = () => r(reader.result); reader.readAsDataURL(b); });
                    } catch(e) {
                        return 'ERROR:' + e.message;
                    }
                }
            """, dl_url)
            
            if result.startswith('ERROR'):
                # 用原 URL 试
                result2 = await target.evaluate("""
                    async (url) => {
                        try {
                            const r = await fetch(url);
                            const b = await r.blob();
                            const reader = new FileReader();
                            return await new Promise(r => { reader.onload = () => r(reader.result); reader.readAsDataURL(b); });
                        } catch(e) {
                            return 'ERROR2:' + e.message;
                        }
                    }
                """, src)
                if result2.startswith('ERROR2'):
                    print(f"    FAILED: {result2}")
                else:
                    _, encoded = result2.split(',', 1)
                    with open(fpath, 'wb') as f:
                        f.write(base64.b64decode(encoded))
                    size = os.path.getsize(fpath) // 1024
                    print(f"    Saved: {fname} ({size}KB)")
            else:
                _, encoded = result.split(',', 1)
                with open(fpath, 'wb') as f:
                    f.write(base64.b64decode(encoded))
                size = os.path.getsize(fpath) // 1024
                print(f"    Saved: {fname} ({size}KB)")
        
        # 截图
        await target.screenshot(path=os.path.join(ARTICLE_DIR, "page_screenshot.png"), full_page=True)
        print(f"\nScreenshot saved.")
        
        await browser.close()

asyncio.run(main())

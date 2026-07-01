import asyncio, json, os, base64, re
from websockets import connect

CDP_HTTP = "http://127.0.0.1:9222"
ARTICLE_URL = "https://x.com/mem0ai/status/2071990201531118063"
ARTICLE_DIR = r"D:\06_Hermes\articles\chatgpt-memory-works"

async def main():
    # Step 1: 获取 browser WS URL
    import urllib.request
    with urllib.request.urlopen(f"{CDP_HTTP}/json/version", timeout=5) as resp:
        version_data = json.loads(resp.read())
    browser_ws_url = version_data["webSocketDebuggerUrl"]
    print(f"Browser WS: {browser_ws_url[:80]}")
    
    # Step 2: 找已有 X 页面或创建新页面
    async with connect(browser_ws_url) as ws:
        # 获取所有目标
        await ws.send(json.dumps({"id": 1, "method": "Target.getTargets", "params": {}}))
        resp = json.loads(await ws.recv())
        targets = resp.get("result", {}).get("targetInfos", [])
        print(f"Found {len(targets)} targets")
        
        target_id = None
        for t in targets:
            url = t.get("url", "")
            if "x.com" in url and "composer" not in url and "omnibox" not in url and "sw.js" not in url:
                target_id = t["targetId"]
                print(f"Using existing X page: {url[:80]}")
                break
        
        if not target_id:
            print("Creating new tab for article...")
            await ws.send(json.dumps({
                "id": 2, "method": "Target.createTarget",
                "params": {"url": ARTICLE_URL}
            }))
            resp = json.loads(await ws.recv())
            target_id = resp["result"]["targetId"]
            print(f"Created target: {target_id}")
    
    # Step 3: 导航到文章链接
    page_ws_url = f"ws://127.0.0.1:9222/devtools/page/{target_id}"
    print(f"Page WS: {page_ws_url[:80]}")
    
    async with connect(page_ws_url) as ws:
        # 启用 Page
        await ws.send(json.dumps({"id": 1, "method": "Page.enable"}))
        await asyncio.sleep(0.5)
        
        # 导航
        await ws.send(json.dumps({
            "id": 2, "method": "Page.navigate",
            "params": {"url": ARTICLE_URL}
        }))
        # 等待导航完成
        while True:
            resp = json.loads(await ws.recv())
            if resp.get("method") == "Page.frameStoppedLoading":
                break
        
        print("Page loaded!")
        await asyncio.sleep(5)
        
        # 启用 Runtime
        await ws.send(json.dumps({"id": 3, "method": "Runtime.enable"}))
        await asyncio.sleep(0.5)
        
        # 提取所有图片
        await ws.send(json.dumps({
            "id": 10, "method": "Runtime.evaluate",
            "params": {
                "expression": """
                    (function() {
                        const imgs = Array.from(document.querySelectorAll('img'));
                        return JSON.stringify(
                            imgs.filter(i => i.complete && i.naturalWidth > 50)
                                .map(i => ({
                                    src: i.src,
                                    w: i.naturalWidth,
                                    h: i.naturalHeight,
                                    alt: (i.alt || '').substring(0, 80)
                                }))
                        );
                    })()
                """,
                "returnByValue": True
            }
        }))
        resp = json.loads(await ws.recv())
        imgs = json.loads(resp["result"]["result"]["value"])
        
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
        
        print(f"\n=== Body images: {len(body_imgs)} ===")
        for idx, img in enumerate(body_imgs):
            print(f"  [{idx}] {img['w']}x{img['h']} | {img['alt'][:40]} | {img['src'][:120]}")
        
        # 下载
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
            
            await ws.send(json.dumps({
                "id": 100 + idx, "method": "Runtime.evaluate",
                "params": {
                    "expression": f"""
                        (async () => {{
                            try {{
                                const r = await fetch('{dl_url}');
                                const b = await r.blob();
                                const reader = new FileReader();
                                return await new Promise(r => {{ reader.onload = () => r(reader.result); reader.readAsDataURL(b); }});
                            }} catch(e) {{
                                try {{
                                    const r2 = await fetch('{src}');
                                    const b2 = await r2.blob();
                                    const reader2 = new FileReader();
                                    return await new Promise(r => {{ reader2.onload = () => r(reader2.result); reader2.readAsDataURL(b2); }});
                                }} catch(e2) {{ return 'ERROR:' + e2.message; }}
                            }}
                        }})()
                    """,
                    "awaitPromise": True
                }
            }))
            resp = json.loads(await ws.recv())
            data_url = resp["result"]["result"]["value"]
            
            if data_url.startswith('ERROR'):
                print(f"    FAIL: {data_url}")
            else:
                _, encoded = data_url.split(',', 1)
                with open(fpath, 'wb') as f:
                    f.write(base64.b64decode(encoded))
                size = os.path.getsize(fpath) // 1024
                print(f"    Saved: {fname} ({size}KB)")
        
        # 截图
        await ws.send(json.dumps({
            "id": 200, "method": "Page.captureScreenshot",
            "params": {"format": "png"}
        }))
        resp = json.loads(await ws.recv())
        with open(os.path.join(ARTICLE_DIR, "page_screenshot.png"), 'wb') as f:
            f.write(base64.b64decode(resp["result"]["data"]))
        print(f"\nScreenshot saved.")

asyncio.run(main())

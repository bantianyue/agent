import asyncio, json, os, base64, re
from websockets import connect

CDP_URL = "ws://127.0.0.1:9222"
ARTICLE_URL = "https://x.com/mem0ai/status/2071990201531118063"
ARTICLE_DIR = r"D:\06_Hermes\articles\chatgpt-memory-works"

async def main():
    # Step 1: 获取 CDP 页面列表，找可用页面
    async with connect(f"{CDP_URL}/devtools/browser/743E3E51CC1D6B726DC075B757E34D02") as ws:
        # 获取已有目标
        await ws.send(json.dumps({"id": 1, "method": "Target.getTargets"}))
        resp = json.loads(await ws.recv())
        targets = resp.get("result", {}).get("targetInfos", [])
        
        x_target = None
        for t in targets:
            url = t.get("url", "")
            if "x.com" in url and "composer" not in url and "omnibox" not in url and "sw.js" not in url:
                x_target = t
                print(f"Found existing X page: {url[:100]}")
                break
        
        if not x_target:
            # 创建新标签页
            print("Creating new tab for article...")
            await ws.send(json.dumps({
                "id": 2, "method": "Target.createTarget",
                "params": {"url": ARTICLE_URL}
            }))
            resp = json.loads(await ws.recv())
            target_id = resp["result"]["targetId"]
        else:
            target_id = x_target["targetId"]
            # 导航到文章
            async with connect(f"{CDP_URL}/devtools/page/{target_id}") as ps:
                await ps.send(json.dumps({"id": 1, "method": "Page.enable"}))
                await ps.recv()
                await ps.send(json.dumps({
                    "id": 2, "method": "Page.navigate",
                    "params": {"url": ARTICLE_URL}
                }))
                await ps.recv()
    
    # Step 2: 等页面加载
    await asyncio.sleep(8)
    
    # Step 3: 连接目标页面提取图片
    async with connect(f"{CDP_URL}/devtools/page/{target_id}") as ws:
        # 启用必要域
        for domain in ["Page", "DOM", "Runtime", "Network"]:
            await ws.send(json.dumps({"id": 0, "method": f"{domain}.enable"}))
            try:
                await asyncio.wait_for(ws.recv(), timeout=3)
            except:
                pass
        
        # 提取所有图片
        await ws.send(json.dumps({
            "id": 10, "method": "Runtime.evaluate",
            "params": {
                "expression": """
                    JSON.stringify(
                        Array.from(document.querySelectorAll('img'))
                            .filter(i => i.complete && i.naturalWidth > 50)
                            .map(i => ({src: i.src, w: i.naturalWidth, h: i.naturalHeight, alt: (i.alt || '').substring(0, 80)}))
                    )
                """,
                "returnByValue": True
            }
        }))
        resp = json.loads(await ws.recv())
        imgs = json.loads(resp["result"]["result"]["value"])
        
        print(f"\n=== Found {len(imgs)} images ===")
        for idx, img in enumerate(imgs):
            print(f"  [{idx}] {img['w']}x{img['h']} | {img['alt'][:40]} | {img['src'][:120]}")
        
        # 过滤正文图：排除头像/图标/emoji
        body_imgs = [i for i in imgs 
                     if i['w'] >= 150 and i['h'] >= 100
                     and 'profile_images' not in i['src']
                     and 'emoji' not in i['src']
                     and 'badge' not in i['src']
                     and 'favicon' not in i['src']]
        
        print(f"\n=== Body images to download: {len(body_imgs)} ===")
        for idx, img in enumerate(body_imgs):
            print(f"  [{idx}] {img['w']}x{img['h']} | {img['alt'][:40]} | {img['src'][:120]}")
        
        # 下载图片
        os.makedirs(ARTICLE_DIR, exist_ok=True)
        for idx, img in enumerate(body_imgs):
            src = img['src']
            
            # 确定扩展名
            m = re.search(r'\.(jpg|jpeg|png|gif|webp)(\?|$)', src)
            ext = m.group(1) if m else 'jpg'
            if ext == 'jpeg': ext = 'jpg'
            
            fname = f"img{idx+1}.{ext}"
            fpath = os.path.join(ARTICLE_DIR, fname)
            
            # 组装下载 URL（用 orig 质量）
            dl_url = src
            if 'pbs.twimg.com/media' in src:
                dl_url = re.sub(r'name=[^&]+', 'name=orig', src) if 'name=' in src else src + '?name=orig'
            
            print(f"\n  Downloading [{idx}] -> {fname}")
            print(f"    URL: {dl_url[:100]}")
            
            # 用 fetch 下载
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
                print(f"    FAILED: {data_url}")
            else:
                header, encoded = data_url.split(',', 1)
                with open(fpath, 'wb') as f:
                    f.write(base64.b64decode(encoded))
                size = os.path.getsize(fpath) // 1024
                print(f"    Saved: {fname} ({size}KB)")
        
        # 截图页面
        await ws.send(json.dumps({
            "id": 200, "method": "Page.captureScreenshot",
            "params": {"format": "png", "fullPage": True}
        }))
        resp = json.loads(await ws.recv())
        screenshot_data = resp["result"]["data"]
        with open(os.path.join(ARTICLE_DIR, "page_full.png"), 'wb') as f:
            f.write(base64.b64decode(screenshot_data))
        print(f"\nFull page screenshot saved.")

asyncio.run(main())

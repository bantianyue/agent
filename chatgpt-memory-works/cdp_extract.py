import asyncio, json, os, base64
from websockets import connect

ARTICLE_URL = "https://x.com/mem0ai/status/2071990201531118063"
ARTICLE_DIR = r"D:\06_Herpes\articles\chatgpt-memory-works"
CDP_URL = "ws://127.0.0.1:9222"

async def main():
    # 先获取目标页面
    async with connect(f"{CDP_URL}/json") as ws:
        await ws.send(json.dumps({"id": 1, "method": "Target.getTargets"}))
        resp = json.loads(await ws.recv())
        targets = resp.get("result", {}).get("targetInfos", [])
        # 找 X 页面
        article_target = None
        for t in targets:
            if "x.com" in t.get("url", "") or "twitter" in t.get("url", ""):
                article_target = t
                break
        if article_target:
            print(f"Found X page: {article_target['url'][:80]}")
            target_id = article_target["targetId"]
        else:
            print("No X page found. Creating new page...")
            # 创建新页面
            await ws.send(json.dumps({
                "id": 2, "method": "Target.createTarget",
                "params": {"url": "about:blank"}
            }))
            resp = json.loads(await ws.recv())
            target_id = resp["result"]["targetId"]
            
            # 导航到文章
            ws_page = f"{CDP_URL}/devtools/page/{target_id}"
            async with connect(ws_page) as ps:
                await ps.send(json.dumps({
                    "id": 1, "method": "Page.enable"
                }))
                await ps.recv()
                await ps.send(json.dumps({
                    "id": 2, "method": "Page.navigate",
                    "params": {"url": ARTICLE_URL}
                }))
                await ps.recv()
                await asyncio.sleep(5)
    
    # 连接目标页面
    ws_url = f"{CDP_URL}/devtools/page/{target_id}"
    print(f"Connecting to page: {ws_url}")
    
    async with connect(ws_url) as ws:
        # 启用必要域
        for domain in ["Page", "DOM", "Runtime", "Network"]:
            await ws.send(json.dumps({"id": 0, "method": f"{domain}.enable"}))
            await ws.recv()
        
        # 提取所有图片
        await ws.send(json.dumps({
            "id": 1, "method": "Runtime.evaluate",
            "params": {
                "expression": """
                    JSON.stringify(
                        Array.from(document.querySelectorAll('img'))
                            .filter(i => i.complete && i.naturalWidth > 50 && !i.src.includes('profile_images') && !i.src.includes('emoji'))
                            .map(i => ({src: i.src, w: i.naturalWidth, h: i.naturalHeight, alt: i.alt || ''}))
                    )
                """,
                "returnByValue": True
            }
        }))
        resp = json.loads(await ws.recv())
        imgs = json.loads(resp["result"]["result"]["value"])
        
        print(f"\n=== Found {len(imgs)} images ===")
        for idx, img in enumerate(imgs):
            print(f"  [{idx}] {img['w']}x{img['h']} | {img['alt'][:50]} | {img['src'][:120]}")
        
        # 过滤出正文图（非头像）
        body_imgs = [i for i in imgs if 'pbs.twimg.com/media' in i['src']]
        if not body_imgs:
            # 可能图片是 data URL 或其它 CDN
            body_imgs = [i for i in imgs if i['w'] >= 200 and i['h'] >= 200]
        
        print(f"\n=== Body images to download: {len(body_imgs)} ===")
        
        for idx, img in enumerate(body_imgs):
            src = img['src']
            ext = 'jpg'
            if 'format=jpg' in src or '.jpg' in src: ext = 'jpg'
            elif 'format=png' in src or '.png' in src: ext = 'png'
            elif 'format=gif' in src or '.gif' in src: ext = 'gif'
            
            fname = f"img{idx+1}.{ext}"
            fpath = os.path.join(ARTICLE_DIR, fname)
            
            # 用 name=orig 下载
            dl_url = src
            if 'pbs.twimg.com' in src and '?' in src:
                dl_url = src.split('?')[0] + '?name=orig'
            elif 'pbs.twimg.com' in src:
                dl_url = src + '?name=orig'
            
            print(f"  Downloading [{idx}] {fname} from {dl_url[:100]}")
            
            # 通过 CDP fetch 下载
            await ws.send(json.dumps({
                "id": 100 + idx, "method": "Runtime.evaluate",
                "params": {
                    "expression": f"""
                        (async () => {{
                            try {{
                                const resp = await fetch('{dl_url}');
                                const blob = await resp.blob();
                                const reader = new FileReader();
                                return await new Promise((resolve) => {{
                                    reader.onload = () => resolve(reader.result);
                                    reader.readAsDataURL(blob);
                                }});
                            }} catch(e) {{
                                const resp2 = await fetch('{src}');
                                const blob2 = await resp2.blob();
                                const reader2 = new FileReader();
                                return await new Promise((resolve) => {{
                                    reader2.onload = () => resolve(reader2.result);
                                    reader2.readAsDataURL(blob2);
                                }});
                            }}
                        }})()
                    """,
                    "awaitPromise": True
                }
            }))
            resp = json.loads(await ws.recv())
            data_url = resp["result"]["result"]["value"]
            
            # 保存文件
            header, encoded = data_url.split(',', 1)
            with open(fpath, 'wb') as f:
                f.write(base64.b64decode(encoded))
            
            size_kb = os.path.getsize(fpath) // 1024
            print(f"     Saved: {fname} ({size_kb}KB)")
        
        # 提取正文
        await ws.send(json.dumps({
            "id": 200, "method": "Runtime.evaluate",
            "params": {
                "expression": """
                    (() => {
                        const article = document.querySelector('article');
                        return article ? article.innerText.substring(0, 5000) : document.body.innerText.substring(0, 5000);
                    })()
                """,
                "returnByValue": True
            }
        }))
        resp = json.loads(await ws.recv())
        text = resp["result"]["result"]["value"]
        print(f"\n=== Article text (first 2000) ===")
        print(text[:2000])

asyncio.run(main())

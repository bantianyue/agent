#!/usr/bin/env python3
"""
cdp-extract.py — 通用 CDP Chrome 网页提取脚本。

从已登录的 CDP Chrome 打开目标 URL，提取：
  - 结构化块序列 blocks.jsonl（PRIMARY）：按 DOM 文档顺序，text 块与 figure 块
    （img + 图注 caption + after_para + hero）在【同一次 DOM 遍历】里绑定
  - 兼容产物：full_text.txt（纯文本）、image_list.txt（扁平 URL 列表）
  - SVG 元素数量提示

关键铁律：图与图注必须在同一次 DOM 遍历绑定成一对记录，
禁止“先抓图数组、再单独编 caption 数组、最后 zip”——这正是 +1 偏移的温床。

用法:
    python cdp-extract.py <url> [<article_dir>]

依赖: websockets (pip install websockets)
      Chrome 必须在 9222 端口开启 CDP

策略:
  - 从 http://localhost:9222/json 获取已打开的 tab
  - 优先复用已有 tab（不新建），用 Target.createTarget 开新 tab
  - 等页面渲染完成后再提取
  - 多维度查图：<img> + background-image + picture source
"""

import json, os, sys, asyncio, urllib.request, urllib.parse, urllib.error
import websockets


async def cdp_eval(ws, expression: str, timeout: int = 15):
    """Evaluate JavaScript in the page via CDP."""
    msg_id = int(asyncio.get_running_loop().time() * 1000) % 100000
    cmd = {
        'id': msg_id,
        'method': 'Runtime.evaluate',
        'params': {'expression': expression, 'returnByValue': True, 'awaitPromise': True, 'timeout': timeout * 1000}
    }
    await ws.send(json.dumps(cmd))
    while True:
        resp = json.loads(await ws.recv())
        if resp.get("id") == msg_id:
            return resp


def get_debug_ws():
    """Get the first usable tab's websocket URL from CDP.
    Prefer tabs that are already on x.com (they have login cookies).
    """
    req = urllib.request.Request("http://localhost:9222/json")
    with urllib.request.urlopen(req, timeout=10) as r:
        tabs = json.loads(r.read().decode())
    if not tabs:
        print("❌ CDP: 没有打开的标签页")
        print("   请确认 Chrome 已以 --remote-debugging-port=9222 启动")
        sys.exit(1)
    # Prefer an existing x.com tab (already logged in)
    for tab in tabs:
        url = tab.get('url', '')
        title = tab.get('title', '')
        if 'x.com' in url and 'x.com/' not in title and len(title) > 15:
            print(f"   复用 X.com 已登录标签页: {title[:50]}")
            return tab['webSocketDebuggerUrl']
    # Fallback: pick a random tab and navigate it
    print(f"   使用标签页: {tabs[0].get('url', '?')[:60]}")
    return tabs[0]['webSocketDebuggerUrl']


async def wait_for_render(ws, timeout: int = 15):
    """Poll until the page has a non-empty title."""
    for _ in range(timeout):
        resp = await cdp_eval(ws, "document.title && document.title.length > 5 ? document.title : ''")
        try:
            title = resp['result']['result']['value']
            if title:
                print(f"   页面已渲染: {title[:60]}")
                return True
        except KeyError:
            pass
        await asyncio.sleep(1)
    print("    ⚠️ 页面渲染超时，继续提取...")
    # Try one more time with longer wait
    await asyncio.sleep(5)
    return False


async def extract(url: str, article_dir: str = None):
    """
    Main extraction flow:
      1. Get CDP WS from browser
      2. Open URL in new tab (Target.createTarget — non-blocking)
      3. Wait up to 15s for render + scroll to trigger lazy load
      4. Extract structured blocks (text + figure[img+caption+after_para+hero])
         —— 图与图注在同一次 DOM 遍历绑定，禁止分两次抓后再 zip
      5. Save blocks.jsonl (PRIMARY) + 兼容产物 + 按序重命名下载脚本
    """
    # 1. Get CDP connection
    print(f"🔗 连接 CDP Chrome...")
    browser_ws = get_debug_ws()
    print(f"   浏览器 WS: {browser_ws[:70]}...")

    async with websockets.connect(browser_ws, max_size=10 * 1024 * 1024) as ws:
        # 2. Open new tab with target URL (keeps same browser context = cookies)
        msg_id = int(asyncio.get_running_loop().time() * 1000) % 100000
        await ws.send(json.dumps({
            'id': msg_id,
            'method': 'Target.createTarget',
            'params': {'url': url, 'newWindow': False}
        }))
        resp = await asyncio.wait_for(ws.recv(), timeout=10)
        result = json.loads(resp)
        tab_id = result.get('result', {}).get('targetId', '')
        if not tab_id:
            print("❌ 无法创建新标签页")
            sys.exit(1)
        print(f"✅ 已打开标签页: {tab_id}")
        tab_ws_url = f"ws://localhost:9222/devtools/page/{tab_id}"

    # Connect to the new tab
    async with websockets.connect(tab_ws_url, max_size=10 * 1024 * 1024) as ws:
        await asyncio.sleep(3)
        await wait_for_render(ws, timeout=15)

        # 2.5 Scroll to trigger lazy-loaded images
        await cdp_eval(ws, "window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(3)
        await cdp_eval(ws, "window.scrollTo(0, document.body.scrollHeight/2)")
        await asyncio.sleep(2)
        await cdp_eval(ws, "window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)
        await cdp_eval(ws, "window.scrollTo(0, 0)")
        await asyncio.sleep(2)

        # 3. Extract structured blocks in ONE DOM traversal.
        #    text 块与 figure 块（img + 其图注 + after_para + hero）一起产出，
        #    图注取 <figcaption> 或紧邻前后文本节点；绝不先抓图再编注后 zip。
        block_script = r'''
(() => {
  const root = document.querySelector('article') || document.querySelector('[role=article]') || document.querySelector('main') || document.body;
  function captionFor(img) {
    const src = img.src || '';
    const fig = img.closest('figure');
    if (fig) {
      const fc = fig.querySelector('figcaption');
      if (fc) { const t = (fc.innerText||'').trim(); if (t) return t; }
    }
    // 紧邻前一个兄弟元素文本（短，视为图注）
    let p = img.previousElementSibling;
    while (p) { const t = (p.innerText||'').trim(); if (t && t.length <= 300) return t; p = p.previousElementSibling; }
    // 紧邻后一个兄弟元素文本（短）
    let n = img.nextElementSibling;
    while (n) { const t = (n.innerText||'').trim(); if (t && t.length <= 300) return t; n = n.nextElementSibling; }
    // X 特例：图注取该推文文本节点（可能较长）
    if (src.includes('pbs.twimg.com')) {
      const tw = img.closest('[data-testid="tweetText"]') || img.parentElement;
      if (tw) { const t = (tw.innerText||'').trim(); if (t) return t; }
    }
    return '';
  }
  const blocks = [];
  let paraIndex = -1;
  const nodes = Array.from(root.querySelectorAll('p,h1,h2,h3,h4,h5,h6,li,blockquote,pre,img,figure'));
  for (const el of nodes) {
    if (el.tagName === 'IMG') {
      if (el.closest('figure')) continue; // figure 分支已处理
      const src = el.src;
      if (!src || src.startsWith('data:') || src.includes('emoji') || src.includes('logo') || src.includes('profile_images')) continue;
      const w = el.naturalWidth || 0, h = el.naturalHeight || 0;
      const ratio = (w && h) ? w / h : 0;
      blocks.push({type:'figure', img:src, caption:captionFor(el), after_para:paraIndex, hero: ratio >= 2.0});
    } else if (el.tagName === 'FIGURE') {
      const im = el.querySelector('img');
      if (!im) continue;
      const src = im.src;
      if (!src || src.startsWith('data:') || src.includes('emoji') || src.includes('logo') || src.includes('profile_images')) continue;
      const w = im.naturalWidth || 0, h = im.naturalHeight || 0;
      const ratio = (w && h) ? w / h : 0;
      blocks.push({type:'figure', img:src, caption:captionFor(im), after_para:paraIndex, hero: ratio >= 2.0});
    } else {
      const t = (el.innerText||'').trim();
      if (t) { blocks.push({type:'text', content:t}); paraIndex++; }
    }
  }
  return JSON.stringify(blocks);
})()
'''
        resp_blocks = await cdp_eval(ws, block_script)
        try:
            blocks = json.loads(resp_blocks['result']['result']['value'])
        except (KeyError, json.JSONDecodeError):
            blocks = []

        text_blocks = [b for b in blocks if b.get('type') == 'text']
        fig_blocks = [b for b in blocks if b.get('type') == 'figure']
        captions_nonempty = sum(1 for b in fig_blocks if (b.get('caption') or '').strip())
        text = "\n\n".join(b['content'] for b in text_blocks)
        imgs = [{'src': b['img']} for b in fig_blocks]

        print(f"\n📝 文本块: {len(text_blocks)} | 图块: {len(fig_blocks)} | 非空图注: {captions_nonempty}")
        if len(fig_blocks) > 0 and len(fig_blocks) != captions_nonempty:
            print(f"   ⚠️ 图块数({len(fig_blocks)}) != 非空图注数({captions_nonempty})，可能图注绑定缺失，请检查 blocks.jsonl")
        for b in fig_blocks:
            print(f"   [图] {b['img'][:80]} | 注: {(b.get('caption','') or '')[:40]}")

        print(f"\n✅ 提取完成")

    # 6. Save results
    if article_dir:
        os.makedirs(article_dir, exist_ok=True)

        # PRIMARY: 结构化块序列
        blocks_path = os.path.join(article_dir, "blocks.jsonl")
        with open(blocks_path, 'w', encoding='utf-8') as f:
            for b in blocks:
                f.write(json.dumps(b, ensure_ascii=False) + "\n")
        print(f"🧱 结构化块已保存: {blocks_path} ({len(blocks)} 块)")

        # Backcompat: 纯文本
        text_path = os.path.join(article_dir, "full_text.txt")
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"📄 正文(兼容)已保存: {text_path}")

        # Backcompat: 扁平图片列表
        img_list_path = os.path.join(article_dir, "image_list.txt")
        with open(img_list_path, 'w', encoding='utf-8') as f:
            f.write(f"Total images: {len(imgs)}\n\n")
            for i, img in enumerate(imgs):
                f.write(f"[img{i+1}] {img['src']}\n")
        print(f"📷 图片列表(兼容)已保存: {img_list_path}")

        # 按文档顺序重命名的下载脚本（hero->cover.png，其余->figNN.png）
        dl_path = os.path.join(article_dir, "_download_images.py")
        dl = []
        dl.append('#!/usr/env python3')
        dl.append('"""Download images in document order; hero->cover.png, others->figNN.png."""')
        dl.append('import urllib.request, os, json')
        dl.append('')
        dl.append('here = os.path.dirname(os.path.abspath(__file__))')
        dl.append('blocks = []')
        dl.append('with open(os.path.join(here, "blocks.jsonl"), encoding="utf-8") as f:')
        dl.append('    for line in f:')
        dl.append('        line = line.strip()')
        dl.append('        if line:')
        dl.append('            try: blocks.append(json.loads(line))')
        dl.append('            except Exception: pass')
        dl.append('figs = [b for b in blocks if b.get("type") == "figure"]')
        dl.append('n = 0')
        dl.append('for b in figs:')
        dl.append('    src = b["img"]')
        dl.append('    if b.get("hero"):')
        dl.append('        fname = "cover.png"')
        dl.append('    else:')
        dl.append('        n += 1')
        dl.append('        fname = f"fig{n:02d}.png"')
        dl.append('    try:')
        dl.append('        req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})')
        dl.append('        with urllib.request.urlopen(req, timeout=30) as r:')
        dl.append('            data = r.read()')
        dl.append('            ct = r.headers.get("Content-Type", "")')
        dl.append('            if "svg" in ct: fname = fname.rsplit(".", 1)[0] + ".svg"')
        dl.append('            elif ("jpg" in ct or "jpeg" in ct) and not fname.endswith(".svg"): fname = fname.rsplit(".", 1)[0] + ".jpg"')
        dl.append('            with open(os.path.join(here, fname), "wb") as ff:')
        dl.append('                ff.write(data)')
        dl.append('            print(f"  OK {fname} ({len(data)//1024}KB)")')
        dl.append('    except Exception as e:')
        dl.append('        print(f"  FAIL {fname}: {e}")')
        with open(dl_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(dl) + "\n")
        print(f"📥 下载脚本已生成(按序重命名): {dl_path}")

    return blocks


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    url = sys.argv[1]
    article_dir = sys.argv[2] if len(sys.argv) > 2 else None
    asyncio.run(extract(url, article_dir))

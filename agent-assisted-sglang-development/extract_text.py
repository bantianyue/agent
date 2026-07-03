import json, asyncio, websockets

TAB_ID = open("/tmp/sglang_tab.txt").read().strip()

async def main():
    ws_url = f'ws://localhost:9222/devtools/page/{TAB_ID}'
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        await asyncio.sleep(1)
        script = '''document.querySelector('article')?.innerText || document.querySelector('[role="article"]')?.innerText || document.body.innerText'''
        cmd = {'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': script, 'returnByValue': True}}
        await ws.send(json.dumps(cmd))
        resp = json.loads(await ws.recv())
        text = resp['result']['result']['value']
        with open("full_text.txt", "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Written: {len(text)} chars")

asyncio.run(main())

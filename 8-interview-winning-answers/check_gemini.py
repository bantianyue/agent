import asyncio, json, websockets

async def main():
    ws_url = 'ws://localhost:9222/devtools/page/A4E36D16A56D515C9E65F79DB438032E'
    async with websockets.connect(ws_url, max_size=20*1024*1024) as ws:
        await asyncio.sleep(1)
        await ws.send(json.dumps({
            'id': 1, 'method': 'Runtime.evaluate',
            'params': {'expression': 'document.title', 'returnByValue': True}
        }))
        resp = json.loads(await ws.recv())
        title = resp.get('result', {}).get('result', {}).get('value', 'no title')
        print(f'Title: {title}')
        
        await ws.send(json.dumps({
            'id': 2, 'method': 'Runtime.evaluate',
            'params': {'expression': 'document.querySelector("[contenteditable=true]") !== null ? "has input" : "no input"', 'returnByValue': True}
        }))
        resp = json.loads(await ws.recv())
        print(f'Input: {resp.get("result", {}).get("result", {}).get("value", "?")}')

asyncio.run(main())

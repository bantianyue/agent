import json, requests, sys, websocket

tabs = requests.get("http://localhost:9222/json").json()
tab = None
for t in tabs:
    if 'NVIDIA' in t.get('title','') and 'Co-Design' in t.get('title',''):
        tab = t['id']
        break

if not tab:
    print("Tab not found")
    sys.exit(1)

ws_url = "ws://localhost:9222/devtools/page/" + tab
ws = websocket.create_connection(ws_url, timeout=10)

msg_id = 1
cmd = {
    "id": msg_id,
    "method": "Runtime.evaluate",
    "params": {
        "expression": "JSON.stringify(Array.from(document.querySelectorAll('img')).filter(i => i.naturalWidth>0).map(i => ({src: i.src, w: i.naturalWidth, h: i.naturalHeight, alt: i.alt})))",
        "returnByValue": True
    }
}
ws.send(json.dumps(cmd))
resp = ws.recv()
result = json.loads(resp)
if 'result' in result and 'result' in result['result']:
    imgs = json.loads(result['result']['result']['value'])
    for i, img in enumerate(imgs):
        print(f"img[{i}]: src={img['src'][:120]}, {img['w']}x{img['h']}, alt={img['alt'][:60]}")
    print(f"\nTotal images: {len(imgs)}")
else:
    print("Error:", json.dumps(result, indent=2)[:500])
ws.close()

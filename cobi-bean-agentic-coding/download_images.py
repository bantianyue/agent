import urllib.request
import os

proxy_handler = urllib.request.ProxyHandler({'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'})
opener = urllib.request.build_opener(proxy_handler)

images = {
    "hero.jpg": "https://pbs.twimg.com/media/HKet_y2WwAAVaul?format=jpg&name=orig",
    "memory-loop.png": "https://pbs.twimg.com/media/HKfNHc8WgAAFgrI?format=png&name=orig",
    "mem0-cover.jpg": "https://pbs.twimg.com/media/HJ0QXlyaoAA36lE?format=jpg&name=orig",
    "mem0-diagram.png": "https://pbs.twimg.com/media/HKfNlUmXYAAoorQ?format=png&name=orig",
    "honcho-diagram1.png": "https://pbs.twimg.com/media/HKfNt88XgAAAB8l?format=png&name=orig",
    "honcho-diagram2.png": "https://pbs.twimg.com/media/HKfN3p4WQAErP_G?format=png&name=orig",
    "checklist.png": "https://pbs.twimg.com/media/HKfOCRhWEAAvt6t?format=png&name=orig",
    "video_thumb.jpg": "https://pbs.twimg.com/amplify_video_thumb/2033555915648200704/img/_O7lSACvRKof7YML.jpg?name=orig",
}

for name, url in images.items():
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with opener.open(req, timeout=30) as resp:
            with open(name, 'wb') as f:
                f.write(resp.read())
        print(f"OK: {name} ({os.path.getsize(name)} bytes)")
    except Exception as e:
        print(f"FAIL: {name} - {e}")

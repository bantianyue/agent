import urllib.request, os

proxy_handler = urllib.request.ProxyHandler({'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'})
opener = urllib.request.build_opener(proxy_handler)

images = [
    ("https://pbs.twimg.com/media/HKhY9ykbAAAQzT2?format=jpg&name=orig", "screenshot.jpg"),
    ("https://pbs.twimg.com/amplify_video_thumb/2057352720206671872/img/r4TcoO7Bo5xJHZgu?format=jpg&name=orig", "video-thumb.jpg"),
]

out_dir = "D:\\06_Hermes\\articles\\steipete-agent-loop"
for url, filename in images:
    path = os.path.join(out_dir, filename)
    if os.path.exists(path):
        print(f"SKIP (exists): {filename}")
        continue
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with opener.open(req, timeout=30) as resp:
            with open(path, 'wb') as f:
                f.write(resp.read())
        print(f"OK: {filename} ({os.path.getsize(path)} bytes)")
    except Exception as e:
        print(f"FAIL: {filename}: {e}")

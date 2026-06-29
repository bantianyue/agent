import urllib.request, os

url = "https://pbs.twimg.com/media/HLXBX4hWIAAoOWn?format=jpg&name=orig"
path = "D:/06_Hermes/articles/how-to-never-hit-glm-5-2-limits/source_cover.jpg"

try:
    # Try direct first
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
        with open(path, "wb") as f:
            f.write(data)
        print(f"OK: {len(data)} bytes")
except Exception as e:
    print(f"Direct failed: {e}")
    # Try with proxy
    try:
        proxy_handler = urllib.request.ProxyHandler({
            'http': 'http://127.0.0.1:7890',
            'https': 'http://127.0.0.1:7890'
        })
        opener = urllib.request.build_opener(proxy_handler)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with opener.open(req, timeout=30) as resp:
            data = resp.read()
            with open(path, "wb") as f:
                f.write(data)
            print(f"OK (via proxy): {len(data)} bytes")
    except Exception as e2:
        print(f"Proxy also failed: {e2}")

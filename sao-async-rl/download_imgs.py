import urllib.request, os
proxies = {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}
handler = urllib.request.ProxyHandler(proxies)
opener = urllib.request.build_opener(handler)
for i in range(1, 12):
    url = f"https://arxiv.org/html/2607.07508v1/x{i}.png"
    dst = f"img{i}.png"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with opener.open(req, timeout=60) as r:
            data = r.read()
        with open(dst, 'wb') as f:
            f.write(data)
        print(f"OK {dst} ({len(data)//1024}KB)")
    except Exception as e:
        print(f"FAIL {dst}: {e}")
print("done")

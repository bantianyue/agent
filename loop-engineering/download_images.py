import urllib.request, os

proxy_handler = urllib.request.ProxyHandler({'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'})
opener = urllib.request.build_opener(proxy_handler)

images = [
    ("https://pbs.twimg.com/media/HKdmlNSWoAER-UY?format=jpg&name=orig", "hero.jpg"),
    ("https://pbs.twimg.com/media/HKdpRZHWwAAkOcJ?format=jpg&name=orig", "img1.jpg"),
    ("https://pbs.twimg.com/media/HKdo2WCWQAAIkh4?format=jpg&name=orig", "img2.jpg"),
    ("https://pbs.twimg.com/media/HKdpGTGW4AAE2aL?format=jpg&name=orig", "img3.jpg"),
    ("https://pbs.twimg.com/media/HKdpeDNWwAAejdO?format=jpg&name=orig", "img4.jpg"),
    ("https://pbs.twimg.com/media/HKdp8_aWAAAHTTA?format=jpg&name=orig", "img5.jpg"),
    ("https://pbs.twimg.com/media/HKdpYQEWwAACdml?format=jpg&name=orig", "img6.jpg"),
    ("https://pbs.twimg.com/media/HKdpvIhXoAAEtvf?format=jpg&name=orig", "img7.jpg"),
    ("https://pbs.twimg.com/media/HKdpqlBWIAAfQYQ?format=jpg&name=orig", "img8.jpg"),
]

out_dir = "D:\\06_Hermes\\articles\\loop-engineering"
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

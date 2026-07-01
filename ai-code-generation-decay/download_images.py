import urllib.request
import os

images = [
    "HKZdjSlXwAAymKr",
    "HKZfV3eWwAAw8-Y",
    "HKZfy7wWcAAg6Cx",
    "HKZh9djXsAAiztR",
    "HKZiCtFWkAAa1ge",
    "HKZgf-DWgAAZ0La",
    "HKZgrfCWsAAbgeS",
]

proxy_handler = urllib.request.ProxyHandler({
    'http': 'http://127.0.0.1:7890',
    'https': 'http://127.0.0.1:7890'
})
opener = urllib.request.build_opener(proxy_handler)

for i, img_id in enumerate(images):
    url = f"https://pbs.twimg.com/media/{img_id}?format=jpg&name=orig"
    filename = f"img{i+1}.jpg"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with opener.open(req, timeout=30) as resp:
            with open(filename, 'wb') as f:
                f.write(resp.read())
        size = os.path.getsize(filename)
        print(f"OK {filename} ({size} bytes)")
    except Exception as e:
        print(f"FAIL {filename}: {e}")

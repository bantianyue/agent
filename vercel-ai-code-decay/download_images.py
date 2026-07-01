import urllib.request
import os

os.chdir("D:\\06_Hermes\\articles\\vercel-ai-code-decay")

urls = [
    ("hero.png", "https://pbs.twimg.com/media/HKT0M8zXwAAoLtQ?format=png&name=orig"),
    ("img1.jpg", "https://pbs.twimg.com/media/HKVr7S_WYAAAc3-?format=jpg&name=orig"),
    ("img2.jpg", "https://pbs.twimg.com/media/HKVsDHDWkAAWaLj?format=jpg&name=orig"),
    ("img3.jpg", "https://pbs.twimg.com/media/HKVsK0qXMAARU9K?format=jpg&name=orig"),
    ("img4.jpg", "https://pbs.twimg.com/media/HKVsQrLXMAAMYjW?format=jpg&name=orig"),
    ("img5.jpg", "https://pbs.twimg.com/media/HKVsYLNW0AAIauL?format=jpg&name=orig"),
    ("img6.jpg", "https://pbs.twimg.com/media/HKVsdc8WIAAB0bC?format=jpg&name=orig"),
    ("img7.jpg", "https://pbs.twimg.com/media/HKVskaoWoAA7aiH?format=jpg&name=orig"),
    ("img8.jpg", "https://pbs.twimg.com/media/HKVsqfFWkAAsZ-u?format=jpg&name=orig"),
]

proxy_handler = urllib.request.ProxyHandler({'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'})
opener = urllib.request.build_opener(proxy_handler)

for name, url in urls:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with opener.open(req, timeout=20) as resp:
            with open(name, 'wb') as f:
                f.write(resp.read())
        print(f"OK: {name}")
    except Exception as e:
        print(f"FAIL: {name} - {e}")

import urllib.request
import os

images = [
    ("HKQpmKIWIAAUozg", "jpg"),   # Article cover
    ("HKK61itXgAAlzrw", "jpg"),   # Lost in the Middle
    ("HKK74qlWgAAmBll", "jpg"),   # Cost chart
    ("HKK7dWUXEAABSVf", "jpg"),   # Memory vs window
    ("HKK8mXDXYAEPHI2", "jpg"),   # Four properties
    ("HKK2sXvXgAEwz6T", "jpg"),   # Memory layer
    ("HKK3P-KXMAALpAQ", "jpg"),   # Division of labor
    ("HKK8Lu_W0AA6QJY", "jpg"),   # Conclusion
    ("HKK4gfGWgAAEYnb", "jpg"),   # Final message
]

proxy_handler = urllib.request.ProxyHandler({
    'http': 'http://127.0.0.1:7890',
    'https': 'http://127.0.0.1:7890'
})
opener = urllib.request.build_opener(proxy_handler)

for i, (img_id, fmt) in enumerate(images):
    url = f"https://pbs.twimg.com/media/{img_id}?format={fmt}&name=orig"
    filename = f"img{i+1}.{fmt}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with opener.open(req, timeout=30) as resp:
            with open(filename, 'wb') as f:
                f.write(resp.read())
        size = os.path.getsize(filename)
        print(f"OK {filename} ({size} bytes)")
    except Exception as e:
        print(f"FAIL {filename}: {e}")

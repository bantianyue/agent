import urllib.request
import os

# All non-avatar images from the article
images = [
    ("HKYhsj-XsAAd3fr", "jpg"),   # Article cover
    ("HKYTPjUX0AAJooq", "png"),   # inline
    ("HKYT-XBXEAI0yYt", "png"),   # inline
    ("HKYVILFW0AAmsCm", "png"),   # inline
    ("HKYYGruWIAAWmLC", "png"),   # inline
    ("HKYY3V-WkAAiB-j", "jpg"),   # inline
    ("HKYZaJqXQAAIF96", "jpg"),   # video thumb
    ("HKYZ6H9XEAA54ks", "jpg"),   # inline
    ("HKYaufLXEAAgTCz", "png"),   # inline
    ("HKYbR9NXcAAfivV", "png"),   # inline
    ("HKYcBV9WwAApV5v", "jpg"),   # inline
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

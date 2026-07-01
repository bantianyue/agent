import urllib.request, urllib.error, os

urls = [
    ("https://pbs.twimg.com/media/HLTAYkEWUAEhdhg?format=jpg&name=orig", "img0.jpg"),
    ("https://pbs.twimg.com/media/HLS_HkDXgAALmAf?format=jpg&name=orig", "img1.jpg"),
    ("https://pbs.twimg.com/media/HLS_Q_SWMAAm_Ig?format=jpg&name=orig", "img2.jpg"),
    ("https://pbs.twimg.com/media/HLS_Ys0WcAATIEV?format=jpg&name=orig", "img3.jpg"),
    ("https://pbs.twimg.com/media/HLS_gz9WQAAdH9M?format=jpg&name=orig", "img4.jpg"),
    ("https://pbs.twimg.com/media/HLS_nzbWAAA5TNw?format=jpg&name=orig", "img5.jpg"),
    ("https://pbs.twimg.com/media/HLS_vgkXsAAbLJT?format=png&name=orig", "img6.png"),
    ("https://pbs.twimg.com/media/HLTAJo2XEAAPvKI?format=jpg&name=orig", "img7.jpg"),
]

proxy_handler = urllib.request.ProxyHandler({
    'http': 'http://127.0.0.1:7890',
    'https': 'http://127.0.0.1:7890'
})
opener = urllib.request.build_opener(proxy_handler)

for url, filename in urls:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with opener.open(req, timeout=30) as resp:
            data = resp.read()
            with open(filename, 'wb') as f:
                f.write(data)
            print(f"✅ {filename} ({len(data)} bytes)")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # Try name=large as fallback
            fallback_url = url.replace('name=orig', 'name=large')
            try:
                req = urllib.request.Request(fallback_url, headers={'User-Agent': 'Mozilla/5.0'})
                with opener.open(req, timeout=30) as resp:
                    data = resp.read()
                    with open(filename, 'wb') as f:
                        f.write(data)
                    print(f"✅ {filename} (fallback large, {len(data)} bytes)")
            except Exception as e2:
                print(f"❌ {filename}: fallback also failed: {e2}")
        else:
            print(f"❌ {filename}: {e}")
    except Exception as e:
        print(f"❌ {filename}: {e}")

print("\n--- Downloaded files ---")
for f in os.listdir('.'):
    if f.startswith('img'):
        print(f"  {f} ({os.path.getsize(f)} bytes)")

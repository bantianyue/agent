#!/usr/bin/env python3
"""Download all images from CDP extraction."""
import urllib.request, os

urls = [
    ('img1.jpg', "https://pbs.twimg.com/media/HMkKR19acAAmOXm?format=jpg&name=900x900"),
    ('img2.jpg', "https://pbs.twimg.com/media/HMi_wNUaMAAbYX1?format=jpg&name=900x900"),
    ('img3.jpg', "https://pbs.twimg.com/media/HMi_82ha0AEGtPE?format=jpg&name=900x900"),
    ('img4.jpg', "https://pbs.twimg.com/media/HMjIMxzaEAAU9uq?format=png&name=small"),
    ('img5.jpg', "https://pbs.twimg.com/media/HMjJUcPaYAAmMl3?format=jpg&name=900x900"),
    ('img6.jpg', "https://pbs.twimg.com/media/HMj9wk0bIAAOJ7y?format=png&name=900x900"),
    ('img7.jpg', "https://pbs.twimg.com/media/HMjKCgXbcAADW1u?format=jpg&name=900x900"),
    ('img8.jpg', "https://pbs.twimg.com/media/HMjLxjubMAAgNk9?format=jpg&name=900x900"),
    ('img9.jpg', "https://pbs.twimg.com/media/HMjOc4IaAAAmURx?format=jpg&name=900x900"),
    ('img10.jpg', "https://pbs.twimg.com/media/HMjPEtzboAAxzkW?format=jpg&name=900x900"),
    ('img11.jpg', "https://pbs.twimg.com/media/HMjPtAvaYAA4GKS?format=jpg&name=900x900"),
    ('img12.jpg', "https://pbs.twimg.com/media/HMjP4XcbQAAZDbV?format=jpg&name=900x900"),
    ('img13.jpg', "https://pbs.twimg.com/media/HMjQrktakAA7ybf?format=jpg&name=900x900"),
]

for fname, url in urls:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
            # Detect actual format from content-type
            ct = r.headers.get("Content-Type", "")
            if "png" in ct: fname = fname.replace(".jpg", ".png")
            with open(fname, "wb") as f:
                f.write(data)
            print(f"  OK {fname} ({len(data)//1024}KB)")
    except Exception as e:
        print(f"  FAIL {fname}: {e}")

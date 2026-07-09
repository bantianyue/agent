#!/usr/bin/env python3
"""Download all images from CDP extraction."""
import urllib.request, os

urls = [
    ('img1.jpg', "https://pbs.twimg.com/media/HMwiDtabQAEei08?format=jpg&name=900x900"),
    ('img2.jpg', "https://pbs.twimg.com/media/HMwZ6NSa8AAUqIg?format=jpg&name=900x900"),
    ('img3.jpg', "https://pbs.twimg.com/media/HMxKEkxaQAAGURG?format=jpg&name=900x900"),
    ('img4.jpg', "https://pbs.twimg.com/media/HMwapNIawAAsQ8_?format=jpg&name=900x900"),
    ('img5.jpg', "https://pbs.twimg.com/media/HMwavm6aIAE4YqT?format=jpg&name=900x900"),
    ('img6.jpg', "https://pbs.twimg.com/media/HMwdBzxaAAAaCMs?format=jpg&name=900x900"),
    ('img7.jpg', "https://pbs.twimg.com/media/HMwa0ata4AAUU8I?format=jpg&name=900x900"),
    ('img8.jpg', "https://pbs.twimg.com/media/HMwa7tIbkAEwdpA?format=jpg&name=900x900"),
    ('img9.jpg', "https://pbs.twimg.com/media/HMwa-2xbIAApULR?format=jpg&name=900x900"),
    ('img10.jpg', "https://pbs.twimg.com/media/HMwbJiubUAEA_3x?format=jpg&name=900x900"),
    ('img11.jpg', "https://pbs.twimg.com/amplify_video_thumb/2075178981889064960/img/YImPGs_triFvIhYq?format=jpg&name=900x900"),
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

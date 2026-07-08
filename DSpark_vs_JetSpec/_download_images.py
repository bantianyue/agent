#!/usr/bin/env python3
"""Download all images from CDP extraction."""
import urllib.request, os

urls = [
    ('img1.jpg', "https://pbs.twimg.com/media/HMLRF1jbgAAYu6U?format=jpg&name=900x900"),
    ('img2.jpg', "https://pbs.twimg.com/media/HMLUeJKawAAwoFK?format=jpg&name=900x900"),
    ('img3.jpg', "https://pbs.twimg.com/tweet_video_thumb/HMLU6d7asAAWF7I?format=jpg&name=900x900"),
    ('img4.jpg', "https://pbs.twimg.com/media/HMLVQPEbYAAIOh0?format=jpg&name=900x900"),
    ('img5.jpg', "https://pbs.twimg.com/media/HMLVhNkbIAAkbe8?format=jpg&name=900x900"),
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

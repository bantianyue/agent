#!/usr/bin/env python3
"""Download all images from CDP extraction."""
import urllib.request, os

urls = [
    ('img1.jpg', "https://pbs.twimg.com/amplify_video_thumb/2074889729070473216/img/iNxp3Zt5JQnHuc3-?format=jpg&name=900x900"),
    ('img2.jpg', "https://pbs.twimg.com/amplify_video_thumb/2074907624580304896/img/bUIjW1eXYX1kTgKw?format=jpg&name=900x900"),
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

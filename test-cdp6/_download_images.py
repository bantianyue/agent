#!/usr/bin/env python3
"""Download all images from CDP extraction."""
import urllib.request, os

urls = [
    ('img1.jpg', "https://pbs.twimg.com/profile_images/2018710459139100672/S9HU7Smb_bigger.jpg"),
    ('img2.jpg', "https://pbs.twimg.com/media/HLVYU3ia0AAjkUs?format=jpg&name=900x900"),
    ('img3.jpg', "https://pbs.twimg.com/media/HMb_XoHbMAAn698?format=jpg&name=900x900"),
    ('img4.jpg', "https://pbs.twimg.com/media/HLA1Rr2bAAAImwc?format=png&name=small"),
    ('img5.jpg', "https://pbs.twimg.com/media/HMcAEBnagAAxQ1O?format=jpg&name=small"),
    ('img6.jpg', "https://pbs.twimg.com/media/HMcA4FFa4AA9l7a?format=jpg&name=900x900"),
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

#!/usr/bin/env python3
"""Download all images from CDP extraction."""
import urllib.request, os

urls = [
    ('img1.jpg', "https://pbs.twimg.com/media/HMpt4JibIAAxBfH?format=jpg&name=900x900"),
    ('img2.jpg', "https://pbs.twimg.com/media/HMpxcRZa8AARxlj?format=jpg&name=900x900"),
    ('img3.jpg', "https://pbs.twimg.com/media/HMp0eckbYAAipJT?format=jpg&name=900x900"),
    ('img4.jpg', "https://pbs.twimg.com/media/HMp1Adwb0AAlMBH?format=jpg&name=900x900"),
    ('img5.jpg', "https://pbs.twimg.com/media/HMp1t-MaoAAz1ia?format=jpg&name=900x900"),
    ('img6.jpg', "https://pbs.twimg.com/media/HMp3sMjbYAAOku2?format=jpg&name=900x900"),
    ('img7.jpg', "https://pbs.twimg.com/media/HMp6l1BaAAAAqE_?format=jpg&name=900x900"),
    ('img8.jpg', "https://pbs.twimg.com/media/HMp4itUbQAEgmFl?format=png&name=900x900"),
    ('img9.jpg', "https://pbs.twimg.com/media/HMqwZn_agAAS3f3?format=jpg&name=900x900"),
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

#!/usr/bin/env python3
"""Download all images from CDP extraction."""
import urllib.request, os

urls = [
    ('img1.jpg', "https://arxiv.org/static/base/1.0.1/images/icons/smileybones-small.svg"),
    ('img2.jpg', "https://arxiv.org/html/2602.18196v5/x1.png"),
    ('img3.jpg', "https://arxiv.org/html/2602.18196v5/x2.png"),
    ('img4.jpg', "https://arxiv.org/html/2602.18196v5/x3.png"),
    ('img5.jpg', "https://arxiv.org/html/2602.18196v5/x4.png"),
    ('img6.jpg', "https://arxiv.org/html/2602.18196v5/x5.png"),
    ('img7.jpg', "https://arxiv.org/html/2602.18196v5/x6.png"),
    ('img8.jpg', "https://arxiv.org/html/2602.18196v5/x7.png"),
    ('img9.jpg', "https://arxiv.org/html/2602.18196v5/x8.png"),
    ('img10.jpg', "https://arxiv.org/html/2602.18196v5/x9.png"),
    ('img11.jpg', "https://arxiv.org/static/base/1.0.1/images/funders/simons-foundation.png"),
    ('img12.jpg', "https://arxiv.org/static/base/1.0.1/images/funders/schmidt-sciences.png"),
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

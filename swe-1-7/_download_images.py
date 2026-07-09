#!/usr/bin/env python3
"""Download all images from CDP extraction."""
import urllib.request, os

urls = [
    ('img1.jpg', "https://cognition.com/images/swe-1-7/policy-entropy.svg"),
    ('img2.jpg', "https://cognition.com/images/swe-1-7/train-infer-mismatch.svg"),
    ('img3.jpg', "https://cognition.com/images/swe-1-7/response-length.svg"),
    ('img4.jpg', "https://cognition.com/images/swe-1-7/behavioral-tendencies.svg"),
    ('img5.jpg', "https://cognition.com/images/swe-1-7/edge-cases.svg"),
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

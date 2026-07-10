#!/usr/bin/env python3
"""Download content images from arXiv HTML paper (x1-x7 only, discard static boilerplate)."""
import urllib.request, os

base = "https://arxiv.org/html/2607.06906v1/"
urls = [
    ('x1.png', base + "x1.png"),
    ('x2.png', base + "x2.png"),
    ('x3.png', base + "x3.png"),
    ('x4.png', base + "x4.png"),
    ('x5.png', base + "x5.png"),
    ('x6.png', base + "x6.png"),
    ('x7.png', base + "x7.png"),
]

for fname, url in urls:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
            with open(fname, "wb") as f:
                f.write(data)
            print(f"  OK {fname} ({len(data)//1024}KB)")
    except Exception as e:
        print(f"  FAIL {fname}: {e}")

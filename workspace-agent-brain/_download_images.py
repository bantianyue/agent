#!/usr/bin/env python3
"""Download all images from CDP extraction."""
import urllib.request, os

urls = [
    ('img1.jpg', "https://transformer-circuits.pub/2026/workspace/png/img_860ca3aa914e9155.png"),
    ('img2.jpg', "https://transformer-circuits.pub/2026/workspace/png/img_2adac9e6c5d32578.png"),
    ('img3.jpg', "https://transformer-circuits.pub/2026/workspace/png/img_0a76fdb1e38b75dd.png"),
    ('img4.jpg', "https://transformer-circuits.pub/2026/workspace/png/img_b6e33e9c6f22dfce.png"),
    ('img5.jpg', "https://transformer-circuits.pub/2026/workspace/png/img_99f81e6946c904c0.png"),
    ('img6.jpg', "https://transformer-circuits.pub/2026/workspace/png/img_b2a7e6b0ffae0b7b.png"),
    ('img7.jpg', "https://transformer-circuits.pub/2026/workspace/png/img_26705cc75891f28c.png"),
    ('img8.jpg', "https://transformer-circuits.pub/2026/workspace/png/img_827d3a5cb00bcbcf.png"),
    ('img9.jpg', "https://transformer-circuits.pub/2026/workspace/png/img_1b62b10ab235e6e7.png"),
    ('img10.jpg', "https://transformer-circuits.pub/2026/workspace/png/img_2b19c68c5712bfa4.png"),
    ('img11.jpg', "https://transformer-circuits.pub/2026/workspace/png/img_c983850908bf60d9.png"),
    ('img12.jpg', "https://transformer-circuits.pub/2026/workspace/png/img_23e5b6de451752cd.png"),
    ('img13.jpg', "https://transformer-circuits.pub/2026/workspace/png/img_151fa39f2f7df490.png"),
    ('img14.jpg', "https://transformer-circuits.pub/2026/workspace/png/img_56638dae3fb9fdd2.png"),
    ('img15.jpg', "https://transformer-circuits.pub/2026/workspace/png/img_cff4d31c62b4ee13.png"),
    ('img16.jpg', "https://transformer-circuits.pub/2026/workspace/png/img_b43879900a1353cf.png"),
    ('img17.jpg', "https://transformer-circuits.pub/2026/workspace/png/img_f7089e9e67458e69.png"),
    ('img18.jpg', "https://transformer-circuits.pub/2026/workspace/png/img_b3ee9cc4785b8511.png"),
    ('img19.jpg', "https://transformer-circuits.pub/2026/workspace/data/jlens-circuit-graph/swaps.svg"),
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

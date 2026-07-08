#!/usr/bin/env python3
"""Download all images from CDP extraction."""
import urllib.request, os

urls = [
    ('img1.jpg', ""),
    ('img2.jpg', "https://publish-01.obsidian.md/access/283ed58d7165cd432e707f2f78dd0724/Machine%20Learning/Inference/assets/stableflashdistill.excalidraw.png"),
    ('img3.jpg', "https://publish-01.obsidian.md/access/283ed58d7165cd432e707f2f78dd0724/Machine%20Learning/Inference/assets/qwen.6.png"),
    ('img4.jpg', "https://publish-01.obsidian.md/access/283ed58d7165cd432e707f2f78dd0724/Machine%20Learning/Inference/assets/unstableflashdistill.png"),
    ('img5.jpg', "https://publish-01.obsidian.md/access/283ed58d7165cd432e707f2f78dd0724/Machine%20Learning/Inference/assets/acceptance.png"),
    ('img6.jpg', "https://publish-01.obsidian.md/access/283ed58d7165cd432e707f2f78dd0724/Machine%20Learning/Inference/assets/markov.png"),
    ('img7.jpg', "https://publish-01.obsidian.md/access/283ed58d7165cd432e707f2f78dd0724/Machine%20Learning/Inference/assets/speedup.png"),
    ('img8.jpg', "https://publish-01.obsidian.md/access/283ed58d7165cd432e707f2f78dd0724/Machine%20Learning/Inference/assets/pretraining.png"),
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

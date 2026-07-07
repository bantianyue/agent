#!/usr/bin/env python3
"""Download all images from CDP extraction."""
import urllib.request, os

urls = [
    ('img1.jpg', "https://cdn.agenticlearning.ai/3c4aead7e9bec501/overview.png"),
    ('img2.jpg', "https://cdn.agenticlearning.ai/a1cf748b02ee760a/method.png"),
    ('img3.jpg', "https://cdn.agenticlearning.ai/2757913f48a98516/benchmarks.png"),
    ('img4.jpg', "https://cdn.agenticlearning.ai/bd8e27b0ff19eb18/main-results.png"),
    ('img5.jpg', "https://cdn.agenticlearning.ai/63c81f8b547b375f/robustness.png"),
    ('img6.jpg', "https://cdn.agenticlearning.ai/7c483df5652cddd4/scaling-results.png"),
    ('img7.jpg', "https://cdn.agenticlearning.ai/160b9cb5cff1c96d/ablation-results.png"),
    ('img8.jpg', "https://cdn.agenticlearning.ai/6c3bc5c53c8921a5/qualitative-color-mapping.png"),
    ('img9.jpg', "https://cdn.agenticlearning.ai/ea775506610c7c8c/qualitative-cross-completion.png"),
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

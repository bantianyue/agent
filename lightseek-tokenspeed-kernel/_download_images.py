#!/usr/bin/env python3
"""Download all images from CDP extraction."""
import urllib.request, os

urls = [
    ('img1.jpg', "https://pytorch.org/wp-content/uploads/2026/06/TokenSpeed-Kernel-Portable-APIs-and-High-Performance-Kernels-for-Multi-Silicon-LLM-Inference.png"),
    ('img2.jpg', "https://pytorch.org/wp-content/uploads/2026/06/01-layered-kernel-system-1.png"),
    ('img3.jpg', "https://pytorch.org/wp-content/uploads/2026/06/02-registration-and-selection-1.png"),
    ('img4.jpg', "https://pytorch.org/wp-content/uploads/2026/06/03-numerics-benchmarking-cli-2.png"),
    ('img5.jpg', "https://pytorch.org/wp-content/uploads/2026/06/04-gpt-oss-kernel-api-boundary-2.png"),
    ('img6.jpg', "https://pytorch.org/wp-content/uploads/2026/06/05-gluon-attention-kernel-snippet-2.png"),
    ('img7.jpg', "https://pytorch.org/wp-content/uploads/2026/06/06-attention-persistent-scheduler-2.png"),
    ('img8.jpg', "https://pytorch.org/wp-content/uploads/2026/06/07-attention-prefill-benchmark-2.png"),
    ('img9.jpg', "https://pytorch.org/wp-content/uploads/2026/06/08-moe-benchmark-2.png"),
    ('img10.jpg', "https://pytorch.org/wp-content/uploads/2026/06/09-end-to-end-output-throughput-2-scaled.png"),
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

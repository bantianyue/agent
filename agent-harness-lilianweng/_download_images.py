#!/usr/bin/env python3
"""Download all images from CDP extraction."""
import urllib.request, os

urls = [
    ('img1.jpg', "https://lilianweng.github.io/posts/2026-07-04-harness/openai-agent-loop.png"),
    ('img2.jpg', "https://lilianweng.github.io/posts/2026-07-04-harness/coding-harness-loop.png"),
    ('img3.jpg', "https://lilianweng.github.io/posts/2026-07-04-harness/ace.png"),
    ('img4.jpg', "https://lilianweng.github.io/posts/2026-07-04-harness/mce.png"),
    ('img5.jpg', "https://lilianweng.github.io/posts/2026-07-04-harness/meta-harness-outer-loop.png"),
    ('img6.jpg', "https://lilianweng.github.io/posts/2026-07-04-harness/meta-harness.png"),
    ('img7.jpg', "https://lilianweng.github.io/posts/2026-07-04-harness/ai-scientist.png"),
    ('img8.jpg', "https://lilianweng.github.io/posts/2026-07-04-harness/autodata.png"),
    ('img9.jpg', "https://lilianweng.github.io/posts/2026-07-04-harness/adas.png"),
    ('img10.jpg', "https://lilianweng.github.io/posts/2026-07-04-harness/aflow.png"),
    ('img11.jpg', "https://lilianweng.github.io/posts/2026-07-04-harness/aflow-exp.png"),
    ('img12.jpg', "https://lilianweng.github.io/posts/2026-07-04-harness/STOP-algo.png"),
    ('img13.jpg', "https://lilianweng.github.io/posts/2026-07-04-harness/STOP-patterns.png"),
    ('img14.jpg', "https://lilianweng.github.io/posts/2026-07-04-harness/self-harness.png"),
    ('img15.jpg', "https://lilianweng.github.io/posts/2026-07-04-harness/alphaevolve.png"),
    ('img16.jpg', "https://lilianweng.github.io/posts/2026-07-04-harness/alphaevolve-plot.png"),
    ('img17.jpg', "https://lilianweng.github.io/posts/2026-07-04-harness/SIA.png"),
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

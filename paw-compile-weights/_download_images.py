#!/usr/bin/env python3
"""Download all images from CDP extraction."""
import urllib.request, os

urls = [
    ('img1.jpg', "https://arxiv.org/static/base/1.0.1/images/icons/smileybones-small.svg"),
    ('img2.jpg', "https://arxiv.org/html/2607.02512v1/x1.png"),
    ('img3.jpg', "https://arxiv.org/html/2607.02512v1/figures/architecture_lora.png"),
    ('img4.jpg', "https://arxiv.org/html/2607.02512v1/x2.png"),
    ('img5.jpg', "https://arxiv.org/html/2607.02512v1/figures/web_ui_1.png"),
    ('img6.jpg', "https://arxiv.org/html/2607.02512v1/figures/web_ui_2.png"),
    ('img7.jpg', "https://arxiv.org/html/2607.02512v1/figures/web_ui_3.png"),
    ('img8.jpg', "https://arxiv.org/html/2607.02512v1/x3.png"),
    ('img9.jpg', "https://arxiv.org/html/2607.02512v1/x4.png"),
    ('img10.jpg', "https://arxiv.org/html/2607.02512v1/figures/paw_program_library.png"),
    ('img11.jpg', "https://arxiv.org/html/2607.02512v1/figures/alien_taboo_frame.png"),
    ('img12.jpg', "https://arxiv.org/static/base/1.0.1/images/funders/simons-foundation.png"),
    ('img13.jpg', "https://arxiv.org/static/base/1.0.1/images/funders/schmidt-sciences.png"),
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

# -*- coding: utf-8 -*-
"""One-off: download the mmbiz_gif files from the draft and count their frames."""
import io
import os
import re
import sys
import urllib.request

from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")

DIR = r"D:/06_Hermes/articles/vllm-agentx-agentic-serving"
content = open(os.path.join(DIR, "_draft_get.html"), encoding="utf-8").read()
imgs = re.findall(r'<img[^>]*src="([^"]+)"', content)
gifs = [u for u in imgs if "mmbiz_gif" in u]
out = r"D:/06_Hermes/articles/_vlgif_work/dl"
os.makedirs(out, exist_ok=True)
for i, u in enumerate(gifs, 1):
    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
    data = urllib.request.urlopen(req, timeout=60).read()
    p = os.path.join(out, f"remote_gif{i}.gif")
    open(p, "wb").write(data)
    im = Image.open(io.BytesIO(data))
    print(f"remote #{i}: bytes={len(data)} size={im.size} frames={getattr(im, 'n_frames', 1)}")

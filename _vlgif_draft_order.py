# -*- coding: utf-8 -*-
"""One-off: print draft text/media reading order to QA figure placement."""
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

content = open(
    r"D:/06_Hermes/articles/vllm-agentx-agentic-serving/_draft_get.html",
    encoding="utf-8",
).read()

content = re.sub(r'<img[^>]*src="([^"]+)"[^>]*>', lambda m: " @@IMG@@ ", content)
content = re.sub(
    r"<figcaption[^>]*>(.*?)</figcaption>",
    lambda m: " @@CAP:" + re.sub(r"<[^>]+>", "", m.group(1))[:60] + "@@ ",
    content,
    flags=re.S,
)
content = re.sub(r"</(p|div|h1|h2|h3|section|blockquote|li)>", "\n", content)
content = re.sub(r"<[^>]+>", "", content)
lines = [l.strip() for l in content.split("\n")]
lines = [l for l in lines if l]
for i, l in enumerate(lines):
    if "@@IMG@@" in l or "@@CAP" in l:
        prev = lines[i - 1][:70] if i else ""
        print(f"[{i:3d}] {l[:130]}")
        print(f"      ^ after: {prev}")

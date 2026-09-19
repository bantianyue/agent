# -*- coding: utf-8 -*-
"""再生-4：补参考区（参考：URL + 分隔线），供 add-portal.py 注入传送门。"""
import re

BASE = r"D:/06_Hermes/articles/amd-mi450-lds-opt"
URL = "https://rocm.blogs.amd.com/software-tools-optimization/mi450-lds-optimization/README.html"

HR = (
    '<hr class="hr" style="border-style: solid;border-width: 2px 0 0;'
    'border-color: rgba(0, 0, 0, 0.1);-webkit-transform-origin: 0 0;'
    '-webkit-transform: scale(1, 0.5);transform-origin: 0 0;transform: scale(1, 0.5);'
    'height: 0.4em;margin: 1.5em 0;"  />'
)
REF = (
    '<p class="p" style="margin: 1.5em 8px;letter-spacing: 0.1em;color: #3f3f3f;">'
    '<span style="font-size:12px;color:#888888;font-family:\'Courier New\',monospace;">'
    f"参考：{URL}</span></p>"
)

h = open(f"{BASE}/article.html", encoding="utf-8").read()
h = re.sub(r"\n*<hr[^>]*/>\s*\n*<p[^>]*><span[^>]*>参考：.*?</span></p>\s*$", "", h, flags=re.S)
if h.rstrip().endswith("</section>"):
    i = h.rstrip().rfind("</section>")
    h = h[:i] + "\n\n" + HR + "\n\n" + REF + "\n</section>\n"
else:
    raise SystemExit("找不到收尾 </section>")
open(f"{BASE}/article.html", "w", encoding="utf-8").write(h)
print("tail ok，参考区:", "参考：" in h, "len", len(h))

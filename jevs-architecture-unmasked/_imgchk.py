# -*- coding: utf-8 -*-
import re
h = open("_draft.html", encoding="utf-8").read()
imgs = re.findall(r'<img[^>]*>', h)
out = ["n=%d" % len(imgs)]
for m in imgs:
    src = re.search(r'src="([^"]+)"', m)
    out.append((src.group(1) if src else "?")[:160])
open("_imgchk.txt", "w", encoding="utf-8").write("\n".join(out))

# -*- coding: utf-8 -*-
import re
s = open("_arch.js", encoding="utf-8", errors="replace").read()
out = []
# find var definitions
for m in re.finditer(r'(?:var|let|const)?\s*([A-Za-z_$][\w$]*)\s*=\s*(\[[^\]]{0,200}\]|\d+(?:\.\d+)?)\s*[,;]', s):
    name, val = m.group(1), m.group(2)
    if len(val) <= 60 or val.startswith("["):
        out.append("%s = %s   (at %d)" % (name, val[:120], m.start()))
open("_dl2.txt","w",encoding="utf-8").write("\n".join(out[:120]))

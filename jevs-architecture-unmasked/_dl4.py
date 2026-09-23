# -*- coding: utf-8 -*-
import re
h = open("_page.html", encoding="utf-8", errors="replace").read()
out = []
# custom elements = tags containing a dash, not astro-cid pattern names
tags = set(re.findall(r'<([a-z][a-z0-9]*-[a-z0-9-]*)', h))
out.append("custom-ish tags: %s" % sorted(tags))
i = h.find('class="scene"')
out.append("scene at %d" % i)
seg = h[max(0,i-2500):i+200]
for m in re.finditer(r'<([a-z][a-z0-9-]*)([^>]*)>', seg):
    tag, attrs = m.group(1), m.group(2)
    if '-' in tag or 'astro-cid-taglfwiq' not in attrs:
        out.append("<%s %s>" % (tag, attrs[:250]))
open("_dl4.txt","w",encoding="utf-8").write("\n".join(out))

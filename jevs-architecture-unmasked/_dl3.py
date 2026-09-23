# -*- coding: utf-8 -*-
import re
h = open("_page.html", encoding="utf-8", errors="replace").read()
out = []
i = h.find("data-play")
out.append("data-play at %d" % i)
seg = h[max(0,i-3000):i+1500]
# find the custom element opening before
m = re.findall(r'<([a-z][a-z0-9-]*)([^>]{0,300}?)>', seg)
for tag, attrs in m[-40:]:
    if 'astro' in attrs or tag not in ('div','span','p','a','path'):
        out.append("<%s %s>" % (tag, attrs[:220]))
open("_dl3.txt","w",encoding="utf-8").write("\n".join(out))

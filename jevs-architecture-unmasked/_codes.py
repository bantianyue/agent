# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
h = open("_page.html", encoding="utf-8", errors="replace").read()
soup = BeautifulSoup(h, "html.parser")
pres = soup.find_all("pre")
out = []
for i, p in enumerate(pres, 1):
    code = p.get_text("", strip=False)
    fn = "_code%d.txt" % i
    open(fn, "w", encoding="utf-8").write(code)
    out.append("%s: %d chars, first line: %s" % (fn, len(code), code.strip().splitlines()[0][:80] if code.strip() else "EMPTY"))
open("_codes.txt", "w", encoding="utf-8").write("\n".join(out))

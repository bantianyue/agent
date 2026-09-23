# -*- coding: utf-8 -*-
import re, os
ART = r"D:\06_Hermes\articles\sarathi"
raw = open(os.path.join(ART, "_raw.html"), encoding="utf-8").read()
out = []
for m in re.finditer(r"determined as follows", raw):
    s = max(0, m.start() - 200)
    out.append(raw[s:m.end() + 1500])
open(os.path.join(ART, "_eq.txt"), "w", encoding="utf-8").write("\n\n====\n\n".join(out))
print(len(out))

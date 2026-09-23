# -*- coding: utf-8 -*-
import re, os
p = r"D:\06_Hermes\articles\sarathi\_draft_raw.html"
h = open(p, encoding="utf-8").read()
print("len", len(h))
out = ["len=%d" % len(h), "=== TAIL ==="]
out.append(h[-1500:])
open(r"D:\06_Hermes\articles\sarathi\_draft_tail2.txt", "w", encoding="utf-8").write("\n".join(out))

# -*- coding: utf-8 -*-
import re, os
ART = r"D:\06_Hermes\articles\sarathi"
raw = open(os.path.join(ART, "_raw.html"), encoding="utf-8").read()
eqs = re.findall(r'<math[^>]*display="block"[^>]*alttext="([^"]*)"', raw)
eqs += re.findall(r'<math[^>]*alttext="([^"]*)"[^>]*display="block"', raw)
out = ["BLOCK EQ count=%d" % len(eqs)]
for e in eqs:
    out.append("  " + e)
# also tex annotations in display block tables
tbl = re.findall(r'<table[^>]*ltx_equation[^>]*>.*?<annotation encoding="application/x-tex">(.*?)</annotation>.*?</table>', raw, re.S)
out.append("EQTABLES=%d" % len(tbl))
for e in tbl:
    out.append("  " + e)
open(os.path.join(ART, "_eq2.txt"), "w", encoding="utf-8").write("\n".join(out))
print("ok")

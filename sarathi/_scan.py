# -*- coding: utf-8 -*-
import json, os, re
ART = r"D:\06_Hermes\articles\sarathi"
tr = json.load(open(os.path.join(ART, "_translations.json"), encoding="utf-8"))
tr = {int(k): v for k, v in tr.items()}
out = []
for k in sorted(tr):
    t = tr[k]
    for pat in ["我们", "我", "它", '"', "——", "§", "計算"]:
        c = t.count(pat) if pat != "我" else (t.count("我") - t.count("我们"))
        if c:
            out.append("[%d] %s x%d : %s" % (k, pat, c, t[:200]))
open(os.path.join(ART, "_style_scan.txt"), "w", encoding="utf-8").write("\n".join(out))
print("ok")

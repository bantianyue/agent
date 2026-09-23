# -*- coding: utf-8 -*-
import json, os
ART = r"D:\06_Hermes\articles\sarathi"
blocks = json.load(open(os.path.join(ART, "_blocks.json"), encoding="utf-8"))
n = 0
out = []
for b in blocks:
    if b["type"] == "list":
        n += 1
        out.append("LIST #%d  items=%d" % (n, len(b["items"])))
        for it in b["items"]:
            out.append("   - " + it[:110])
out.insert(0, "total list blocks = %d" % n)
open(os.path.join(ART, "_lists.txt"), "w", encoding="utf-8").write("\n".join(out))
print("lists", n)

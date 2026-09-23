# -*- coding: utf-8 -*-
import json, os
ART = r"D:\06_Hermes\articles\sarathi"
items = json.load(open(os.path.join(ART, "_items.json"), encoding="utf-8"))
out = []
for i in [11, 12, 13, 14, 15, 16, 17, 91, 92, 93, 94, 95, 96]:
    it = items[i]
    out.append("[%d] %s %s" % (i, it["kind"], (it.get("text") or "")[:90]))
open(os.path.join(ART, "_items_spot.txt"), "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))

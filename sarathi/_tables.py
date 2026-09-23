# -*- coding: utf-8 -*-
import json, os
ART = r"D:\06_Hermes\articles\sarathi"
items = json.load(open(os.path.join(ART, "_items.json"), encoding="utf-8"))
out = []
for i, it in enumerate(items):
    if it["kind"] == "table":
        out.append("=== item %d : %s" % (i, it["caption"]))
        for r in it["rows"]:
            out.append("  " + " | ".join(r))
open(os.path.join(ART, "_tables.txt"), "w", encoding="utf-8").write("\n".join(out))
print("ok")

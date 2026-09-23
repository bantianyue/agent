# -*- coding: utf-8 -*-
import json, os
ART = r"D:\06_Hermes\articles\sarathi"
items = json.load(open(os.path.join(ART, "_items.json"), encoding="utf-8"))
out = []
for i, it in enumerate(items):
    if it["kind"] == "head":
        out.append("%3d %-4s %s" % (i, it["level"], it["text"]))
    elif it["kind"] == "p":
        out.append("%3d P    [%s|%s] %s" % (i, it["h3"] or it["h2"], "L" if it.get("list") else "", it["text"][:90]))
    elif it["kind"] == "fig":
        out.append("%3d FIG  %s | %s" % (i, os.path.basename(it["src"]), it["caption"][:70]))
    elif it["kind"] == "table":
        out.append("%3d TBL  %s" % (i, it["caption"][:70]))
open(os.path.join(ART, "_items_list.txt"), "w", encoding="utf-8").write("\n".join(out))
print("ok")

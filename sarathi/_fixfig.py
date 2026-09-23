# -*- coding: utf-8 -*-
import os, json, shutil

ART = r"D:\06_Hermes\articles\sarathi"
mapping = json.load(open(os.path.join(ART, "_figmap.json"), encoding="utf-8"))

log = []
fixed = 0
for m in mapping:
    old = m.get("old")
    target = os.path.join(ART, m["fig"])
    if not old:
        log.append("NOFILE %s <- %s" % (m["fig"], m["src"]))
        continue
    if old.lower().endswith(".svg"):
        cand = os.path.join(ART, os.path.splitext(old)[0] + ".png")
        if os.path.exists(cand):
            with open(cand, "rb") as f:
                ok = f.read(8) == b"\x89PNG\r\n\x1a\n"
            if ok:
                shutil.copyfile(cand, target)
                m["old"] = os.path.basename(cand)
                fixed += 1
                continue
        log.append("STILL_SVG %s <- %s" % (m["fig"], old))
    else:
        shutil.copyfile(os.path.join(ART, old), target)

json.dump(mapping, open(os.path.join(ART, "_figmap.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# verify
bad = []
for m in mapping:
    p = os.path.join(ART, m["fig"])
    if not os.path.exists(p):
        bad.append("MISSING " + m["fig"])
        continue
    with open(p, "rb") as f:
        if f.read(8) != b"\x89PNG\r\n\x1a\n":
            bad.append("NOTPNG " + m["fig"] + " <- " + str(m.get("old")))
log.append("FIXED=%d FIG=%d" % (fixed, len(mapping)))
log.extend(bad)
open(os.path.join(ART, "_fixfig_out.txt"), "w", encoding="utf-8").write("\n".join(log))
print("\n".join(log))

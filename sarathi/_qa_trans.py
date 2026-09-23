# -*- coding: utf-8 -*-
import json, os, re
ART = r"D:\06_Hermes\articles\sarathi"
paras = json.load(open(os.path.join(ART, "_paras.json"), encoding="utf-8"))
tr = json.load(open(os.path.join(ART, "_translations.json"), encoding="utf-8"))
tr = {int(k): v for k, v in tr.items()}

cjk = lambda s: len(re.findall(r"[\u4e00-\u9fff]", s))
en = lambda s: len(re.findall(r"[A-Za-z]", s))

out = []
tot_c = tot_e = 0
bad = []
for p in paras:
    i = p["id"]
    t = tr.get(i, "")
    tot_c += cjk(t); tot_e += en(t)
    ratio = cjk(t) / max(1, cjk(t) + en(t))
    out.append("--- [%d] cjk=%d en=%d\nSRC: %s\nZH : %s" % (i, cjk(t), en(t), p["content"], t))
    if cjk(t) < 8 and en(t) > 40:
        bad.append(i)
open(os.path.join(ART, "_trans_review.txt"), "w", encoding="utf-8").write("\n".join(out))
print("TOTAL cjk=%d en=%d" % (tot_c, tot_e))
print("SUSPECT(no-translate):", bad)

# -*- coding: utf-8 -*-
import os, glob

D = r"D:\06_Hermes\articles\sarathi"
out = []
for p in sorted(glob.glob(os.path.join(D, "fig*.png"))):
    with open(p, "rb") as f:
        head = f.read(64)
    out.append("%s head=%r" % (os.path.basename(p), head[:16]))
open(os.path.join(D, "_magic.txt"), "w", encoding="utf-8").write("\n".join(out))

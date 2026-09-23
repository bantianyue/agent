# -*- coding: utf-8 -*-
import os, glob, struct, io, sys

D = r"D:\06_Hermes\articles\sarathi"

def png_size(p):
    with open(p, "rb") as f:
        head = f.read(33)
    w = struct.unpack(">I", head[16:20])[0]
    h = struct.unpack(">I", head[20:24])[0]
    return w, h

out = []
for p in sorted(glob.glob(os.path.join(D, "fig*.png"))):
    try:
        w, h = png_size(p)
    except Exception as e:
        w = h = -1
    out.append("%s %sx%s %.1fKB" % (os.path.basename(p), w, h, os.path.getsize(p)/1024.0))

open(os.path.join(D, "_figsize.txt"), "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))

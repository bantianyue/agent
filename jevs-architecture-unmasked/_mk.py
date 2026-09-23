# -*- coding: utf-8 -*-
import os, glob
from PIL import Image

files = sorted(glob.glob("frames/f*.png"))
frames = []
for f in files:
    im = Image.open(f).convert("RGB")
    w, h = im.size
    tw = 640
    im = im.resize((tw, round(h * tw / w)), Image.LANCZOS)
    frames.append(im)

sample_idx = [int(i * len(frames) / 24) for i in range(24)]
sample = Image.new("RGB", (frames[0].width * 6, frames[0].height * 4))
for k, i in enumerate(sample_idx):
    sample.paste(frames[i], ((k % 6) * frames[0].width, (k // 6) * frames[0].height))

res = []
for colors in (112, 96, 64):
    pal = sample.convert("P", palette=Image.ADAPTIVE, colors=colors)
    out_frames = [im.quantize(palette=pal, dither=Image.NONE) for im in frames]
    fn = "_test_%d.gif" % colors
    out_frames[0].save(fn, save_all=True, append_images=out_frames[1:], duration=80, loop=0, optimize=True)
    res.append("%s colors=%d KB=%d" % (fn, colors, os.path.getsize(fn) // 1024))
open("_mk.txt", "w", encoding="utf-8").write("\n".join(["frames=%d" % len(frames)] + res))

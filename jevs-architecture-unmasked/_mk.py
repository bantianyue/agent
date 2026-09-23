# -*- coding: utf-8 -*-
import os, glob
from PIL import Image

files = sorted(glob.glob("frames/f*.png"))
print("frames:", len(files))
frames = []
for f in files:
    im = Image.open(f).convert("RGB")
    w, h = im.size
    tw = 640
    im = im.resize((tw, round(h * tw / w)), Image.LANCZOS)
    frames.append(im)

# global palette from a sample of frames
sample_idx = [int(i * len(frames) / 24) for i in range(24)]
sample = Image.new("RGB", (frames[0].width * 6, frames[0].height * 4))
for k, i in enumerate(sample_idx):
    sample.paste(frames[i], ((k % 6) * frames[0].width, (k // 6) * frames[0].height))
pal = sample.convert("P", palette=Image.ADAPTIVE, colors=112)

out_frames = []
for im in frames:
    q = im.convert("P", palette=pal.palette) if False else im.quantize(palette=pal, dither=Image.FLOYDSTEINBERG)
    out_frames.append(q)

sizes = []
out_frames[0].save("fig01.gif", save_all=True, append_images=out_frames[1:], duration=80, loop=0, optimize=True)
print("gif size KB:", os.path.getsize("fig01.gif") // 1024, "n:", len(out_frames))

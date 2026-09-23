# -*- coding: utf-8 -*-
# 情况 B：源图宽高比 1.5~2.35 → 等比缩放 + 纯色背景补齐两侧（不拉伸、不裁剪）
from PIL import Image

ART = r"D:\06_Hermes\articles\sarathi"
src = Image.open(ART + r"\source.png").convert("RGB")
w, h = src.size
print("src", w, h, "ratio %.2f" % (w / h))

def contain(canvas_wh, out):
    cw, ch = canvas_wh
    scale = min(cw / w, ch / h)
    nw, nh = int(w * scale), int(h * scale)
    canvas = Image.new("RGB", (cw, ch), (255, 255, 255))
    canvas.paste(src.resize((nw, nh), Image.LANCZOS), ((cw - nw) // 2, (ch - nh) // 2))
    canvas.save(out)
    print(out, nw, nh)

contain((900, 383), ART + r"\cover.png")
contain((500, 500), ART + r"\cover-square.png")

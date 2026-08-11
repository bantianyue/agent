#!/usr/bin/env python3
"""SVG→PNG 批量转换 + 白边裁剪放大 + 覆盖到文章目录。"""
import os, subprocess
from PIL import Image, ImageFilter

ART = r"D:/06_Hermes/articles/minimax-m3-inference"
TMP = os.path.join(ART, "_images_tmp")
CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"

svgs = ["fig01.svg", "fig02.svg", "fig03.svg", "fig04.svg"]
for svg in svgs:
    name = svg.replace(".svg", "")
    svg_win = os.path.join(TMP, svg)
    png_win = os.path.join(TMP, name + "_raw.png")
    cmd = [
        CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
        "--window-size=1500,1500", "--default-background-color=FFFFFFFF",
        f"--screenshot={png_win}", svg_win
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    out = r.stdout or r.stderr
    ok = "bytes written" in out
    print(f"{svg}: {'OK' if ok else 'FAIL'}", out.strip().splitlines()[-1][:60] if out else "")
    if not ok:
        print("   ", r.stderr[-200:])

# 白边裁剪 + 放大到 1500px 宽
def autocrop(fp, pad=10):
    img = Image.open(fp).convert("RGB"); w, h = img.size; px = img.load()
    min_x, min_y, max_x, max_y = w, h, 0, 0
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            r, g, b = px[x, y]
            if not (r > 245 and g > 245 and b > 245):
                min_x = min(min_x, x); max_x = max(max_x, x)
                min_y = min(min_y, y); max_y = max(max_y, y)
    if max_x < min_x:  # 全白
        return img
    box = (max(0, min_x-pad), max(0, min_y-pad), min(w-1, max_x+pad), min(h-1, max_y+pad))
    return img.crop(box)

for svg in svgs:
    name = svg.replace(".svg", "")
    raw = os.path.join(TMP, name + "_raw.png")
    if not os.path.exists(raw):
        continue
    img = autocrop(raw)
    scale = 1500 / img.size[0]
    img = img.resize((int(img.size[0]*scale), int(img.size[1]*scale)), Image.LANCZOS)
    img = img.filter(ImageFilter.SHARPEN)
    out = os.path.join(ART, name + ".png")
    img.save(out)
    print(f"→ {name}.png  {img.size}  {os.path.getsize(out)//1024}KB")

print("done")

from PIL import Image
import os

dir_path = "D:\\06_Hermes\\articles\\mimo-1000tps"

# Check what we can use as cover
for f in ["execution_gap.png", "microsecond_war.png", "codesign.png"]:
    path = os.path.join(dir_path, f)
    if os.path.exists(path):
        img = Image.open(path)
        w, h = img.size
        ratio = w / h
        print(f"{f:30s} {w}x{h} ratio={ratio:.2f}")

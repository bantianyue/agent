import os, sys, re
import fitz
import numpy as np
from PIL import Image

PDF = r"D:\06_Hermes\articles\mimo-v26-scaling-rl\mimo_v2_6_technical_report.pdf"
OUT = r"D:\06_Hermes\articles\mimo-v26-scaling-rl"

SCALE = 2.0      # render scale used for the whitespace analysis
FINAL = 3.2      # final clip render scale (approx 230 dpi)


def find_caption(page, tag):
    """tag like 'Figure 2' or 'Table 1' -> bbox of that caption text block"""
    blocks = page.get_text("dict")["blocks"]
    hits = []
    for b in blocks:
        if b.get("type") != 0:
            continue
        text = " ".join(
            "".join(sp["text"] for sp in line["spans"]) for line in b["lines"]
        ).strip()
        if re.match(r"^" + re.escape(tag) + r"\b", text):
            hits.append((b["bbox"], text))
    return hits


def row_profile(page):
    pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    arr = np.asarray(img)
    nonwhite = (arr.min(axis=2) < 235).sum(axis=1)
    return arr, nonwhite, pix.width, pix.height


def col_limits(arr, y0, y1, minpix=3):
    sub = arr[y0:y1]
    cols = (sub.min(axis=2) < 235).sum(axis=0)
    idx = np.where(cols > minpix)[0]
    if len(idx) == 0:
        return 0, arr.shape[1]
    return int(idx[0]), int(idx[-1]) + 1


def extract(tag, page_idx, pad_top=6, gap=18):
    doc = fitz.open(PDF)
    page = doc[page_idx]
    caps = find_caption(page, tag)
    if not caps:
        print(f"[MISS] {tag} on page {page_idx+1}")
        return None
    cbbox, ctext = caps[-1]
    arr, nonwhite, W, H = row_profile(page)
    cap_px = int(cbbox[1] * SCALE)
    # walk upward from caption top to find the first blank gap => figure top
    y = cap_px
    blank = 0
    top = 0
    while y > 0:
        if nonwhite[y] <= 2:
            blank += 1
            if blank >= gap:
                top = y + blank
                break
        else:
            blank = 0
        y -= 1
    # figure bottom: caption block bottom
    bottom = int(cbbox[3] * SCALE)
    top = max(0, top - pad_top)
    x0, x1 = col_limits(arr, top, bottom)
    pad = 10
    x0 = max(0, x0 - pad)
    x1 = min(W, x1 + pad)
    rect = fitz.Rect(x0 / SCALE, top / SCALE, x1 / SCALE, bottom / SCALE)
    pix = page.get_pixmap(matrix=fitz.Matrix(FINAL, FINAL), clip=rect, alpha=False)
    name = tag.lower().replace(" ", "") + ".png"
    path = os.path.join(OUT, "figs_raw", name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pix.save(path)
    print(f"[OK] {tag} p{page_idx+1} rect={rect} -> {pix.width}x{pix.height}")
    return path


JOBS = [
    ("Figure 1", 0),
    ("Figure 2", 4),
    ("Figure 3", 7),
    ("Figure 4", 9),
    ("Figure 5", 11),
    ("Figure 6", 15),
    ("Figure 7", 16),
    ("Figure 8", 18),
    ("Figure 9", 21),
    ("Figure 10", 22),
    ("Figure 11", 23),
    ("Figure 12", 23),
    ("Figure 13", 24),
    ("Figure 14", 27),
    ("Figure 15", 29),
    ("Figure 16", 30),
    ("Figure 17", 36),
    ("Table 1", 5),
    ("Table 2", 14),
    ("Table 3", 25),
    ("Table 4", 33),
    ("Table 5", 33),
    ("Table 6", 34),
    ("Table 7", 35),
]

if __name__ == "__main__":
    only = sys.argv[1:] if len(sys.argv) > 1 else None
    for tag, p in JOBS:
        if only and tag not in only:
            continue
        extract(tag, p)

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
    cap_top = cbbox[1]

    # collect graphical items (vector drawings + bitmaps) sitting above the caption
    items = []
    for d in page.get_drawings():
        r = d["rect"]
        big = r.width > 3 and r.height > 3
        rule = r.width > 20 and r.height >= 0.2
        if (big or rule) and r.y1 <= cap_top + 3:
            items.append(r)
    for info in page.get_image_info():
        r = fitz.Rect(info["bbox"])
        if r.width > 3 and r.height > 3 and r.y1 <= cap_top + 3:
            items.append(r)
    if not items:
        print(f"[MISS-GFX] {tag} p{page_idx+1}")
        return None

    # cluster upward: start from items touching the caption area, expand while gap < 30pt
    cluster = [r for r in items if r.y1 >= cap_top - 45]
    if not cluster:
        cluster = [max(items, key=lambda r: r.y1)]
    top = min(r.y0 for r in cluster)
    changed = True
    while changed:
        changed = False
        for r in items:
            if r in cluster:
                continue
            if r.y1 >= top - 30:
                cluster.append(r)
                top = min(top, r.y0)
                changed = True
    x0 = min(min(r.x0 for r in cluster), cbbox[0])
    x1 = max(max(r.x1 for r in cluster), cbbox[2])
    y0 = max(0, top - pad_top)
    y1 = max(cbbox[3], max(r.y1 for r in cluster))
    x0 = max(0, x0 - 6)
    x1 = min(page.rect.width, x1 + 6)
    rect = fitz.Rect(x0, y0, x1, y1)
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

MANUAL = {
    "Table 1": (5, fitz.Rect(64, 74, 532, 604)),
    "Table 2": (14, fitz.Rect(64, 78, 532, 510)),
    "Table 3": (25, fitz.Rect(64, 78, 532, 494)),
    "Table 4": (33, fitz.Rect(64, 80, 532, 232)),
    "Table 5": (33, fitz.Rect(64, 238, 532, 374)),
    "Table 6": (34, fitz.Rect(64, 80, 532, 400)),
    "Table 7": (35, fitz.Rect(64, 80, 532, 339)),
}

if __name__ == "__main__":
    only = sys.argv[1:] if len(sys.argv) > 1 else None
    for tag, p in JOBS:
        if only and tag not in only:
            continue
        if tag in MANUAL:
            pi, rect = MANUAL[tag]
            doc = fitz.open(PDF)
            page = doc[pi]
            pix = page.get_pixmap(matrix=fitz.Matrix(FINAL, FINAL), clip=rect, alpha=False)
            name = tag.lower().replace(" ", "") + ".png"
            path = os.path.join(OUT, "figs_raw", name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            pix.save(path)
            print(f"[OK-manual] {tag} p{pi+1} rect={rect} -> {pix.width}x{pix.height}")
        else:
            extract(tag, p)

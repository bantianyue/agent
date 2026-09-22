import sys, re, json
import fitz

PDF = r"D:\06_Hermes\articles\mimo-v26-scaling-rl\mimo_v2_6_technical_report.pdf"
sys.path.insert(0, r"D:\06_Hermes\articles\_tmp\mimo-probe")
import extract_figs as EF

doc = fitz.open(PDF)


def rect_for(tag, page_idx):
    if tag in EF.MANUAL:
        pi, rect = EF.MANUAL[tag]
        return pi, rect
    page = doc[page_idx]
    caps = EF.find_caption(page, tag)
    if not caps:
        return None, None
    cbbox, _ = caps[-1]
    cap_top = cbbox[1]
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
        return None, None
    cluster = [r for r in items if r.y1 >= cap_top - 45] or [max(items, key=lambda r: r.y1)]
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
    x0 = min(r.x0 for r in cluster) - 6
    x1 = max(r.x1 for r in cluster) + 6
    y0 = max(0, top - 6)
    y1 = max(cbbox[3], max(r.y1 for r in cluster))
    return page_idx, fitz.Rect(max(0, x0), y0, min(page.rect.width, x1), y1)


for tag, p in EF.JOBS:
    pi, rect = rect_for(tag, p)
    if rect is None:
        print(tag, "MISS")
        continue
    txt = doc[pi].get_text(clip=rect)
    lines = [" ".join(l.split()) for l in txt.splitlines() if l.strip()]
    head = " | ".join(lines[:3])[:150]
    tail = " | ".join(lines[-3:])[:150]
    print(f"### {tag} p{pi+1} {rect}")
    print("   HEAD:", head)
    print("   TAIL:", tail)

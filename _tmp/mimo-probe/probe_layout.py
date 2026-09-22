import sys
import fitz

PDF = r"D:\06_Hermes\articles\mimo-v26-scaling-rl\mimo_v2_6_technical_report.pdf"
doc = fitz.open(PDF)
for pi in [int(a) - 1 for a in sys.argv[1:]]:
    p = doc[pi]
    print("===== page", pi + 1)
    for b in p.get_text("dict")["blocks"]:
        if b["type"] == 0:
            txt = " ".join("".join(s["text"] for s in l["spans"]) for l in b["lines"]).strip()
            print("  T [%6.1f,%6.1f] %s" % (b["bbox"][1], b["bbox"][3], txt[:72]))
        else:
            print("  I [%6.1f,%6.1f] image" % (b["bbox"][1], b["bbox"][3]))
    dr = p.get_drawings()
    print("  drawings:", len(dr))
    for d in dr[:14]:
        r = d["rect"]
        print("   D [%6.1f,%6.1f,%6.1f,%6.1f] fill=%s col=%s" % (r.x0, r.y0, r.x1, r.y1, d.get("fill"), d.get("color")))

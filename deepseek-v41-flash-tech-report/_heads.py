import fitz,sys
sys.stdout.reconfigure(encoding="utf-8")
doc=fitz.open("source.pdf")
for i,p in enumerate(doc):
    d=p.get_text("dict")
    for b in d["blocks"]:
        for l in b.get("lines",[]):
            for s in l["spans"]:
                t=s["text"].strip()
                if not t: continue
                sz=round(s["size"],1)
                if sz>=11.5 and len(t)<120:
                    print("p%02d sz%.1f %s"%(i+1,sz,t))

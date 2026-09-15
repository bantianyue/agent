import fitz,sys,json,re
sys.stdout.reconfigure(encoding="utf-8")
doc=fitz.open("source.pdf")
out=[]
for i,p in enumerate(doc):
    out.append("\n\n===== PAGE %d =====\n"%(i+1)+p.get_text())
open("_raw_text.txt","w",encoding="utf-8").write("".join(out))
# headings by font size
from collections import Counter
c=Counter()
for p in doc:
    d=p.get_text("dict")
    for b in d["blocks"]:
        for l in b.get("lines",[]):
            for s in l["spans"]:
                c[round(s["size"],1)]+=len(s["text"])
print(sorted(c.items(),key=lambda x:-x[0])[:15])

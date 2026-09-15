import fitz,re,sys
sys.stdout.reconfigure(encoding="utf-8")
doc=fitz.open("source.pdf")
for i,p in enumerate(doc):
    txt=p.get_text()
    for m in re.finditer(r"^\s*(\d+\.\d+(?:\.\d+)?)\s+([^\n]{3,90})$", txt, re.M):
        print("p%02d SUB %s %s"%(i+1,m.group(1),m.group(2)))
    for m in re.finditer(r"^(Figure\s+\d+[:.][^\n]{0,110})", txt, re.M):
        print("p%02d CAP %s"%(i+1,m.group(1)))
    for m in re.finditer(r"^(Table\s+\d+[:.][^\n]{0,110})", txt, re.M):
        print("p%02d TAB %s"%(i+1,m.group(1)))

# -*- coding: utf-8 -*-
import sys
from pypdf import PdfReader
src=r"D:/06_Hermes/articles/_gva.pdf"
r=PdfReader(src)
parts=[]
for i,p in enumerate(r.pages):
    try:
        parts.append(p.extract_text() or "")
    except Exception as e:
        parts.append(f"[page{i} extract err]")
out="\n".join(parts)
open(r"D:/06_Hermes/articles/_gva.txt","w",encoding="utf8").write(out)
print("pages",len(r.pages),"chars",len(out))

# -*- coding: utf-8 -*-
import re, io

P = r"D:\06_Hermes\articles\sarathi\article_data_build.py"
txt = open(P, encoding="utf-8").read()

pats = [
    ("DUP_TERM", r"（(解码最大化批处理|分块预填充)）"),
    ("SPACE_TERM", r"[\u4e00-\u9fa5\s][ ](解码最大化批处理|分块预填充) |(解码最大化批处理|分块预填充)[ ]"),
    ("RU_SUOSHU", r"如\s+所述"),
    ("DUP2", r"(\*\*)?([\u4e00-\u9fa5A-Za-z]{2,14})\1"),
    ("HUO", r"（（|））"),
    ("SPACE_CJK", r"[\u4e00-\u9fa5] [\u4e00-\u9fa5]"),
    ("DOT_NUM", r'"(\d)\. '),
]
out = []
for name, p in pats:
    hits = []
    for m in re.finditer(p, txt):
        s = max(0, m.start() - 30)
        hits.append(txt[s:m.end() + 30].replace("\n", "⏎"))
    out.append("### %s  (%d)" % (name, len(hits)))
    out.extend("   " + h for h in hits[:40])
open(r"D:\06_Hermes\articles\sarathi\_clean_scan.txt", "w", encoding="utf-8").write("\n".join(out))
print("done")

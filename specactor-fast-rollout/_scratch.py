import json
items=json.load(open("_content.json",encoding="utf-8"))
tr=json.load(open("_translations.json",encoding="utf-8"))
for i,x in enumerate(items):
    if i<70: continue
    if x["kind"] in ("para","bullet","runin"):
        print("[%d|%s] %s" % (i, x["kind"], tr.get(str(i),"<MISSING>")))

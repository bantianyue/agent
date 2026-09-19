import json,re,collections
items=json.load(open("_content.json",encoding="utf-8"))
tr=json.load(open("_translations.json",encoding="utf-8"))
c=collections.Counter()
for i,x in enumerate(items):
    if x["kind"] in ("para","bullet","runin","h2","h3"):
        for m in re.findall(r"\$[^$]{1,60}\$", tr.get(str(i),"")):
            c[m]+=1
for k,v in c.most_common(60): print(v,"|",k)

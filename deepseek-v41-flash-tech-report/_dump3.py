import json,sys
sys.stdout.reconfigure(encoding="utf-8")
d=json.load(open("article_data.json",encoding="utf-8"))
out=[]
out.append("## LEAD")
for x in d["lead"]: out.append(x)
out.append("## CONCLUSION")
for x in d["conclusion"]: out.append(x)
for i,s in enumerate(d["sections"]):
    out.append("\n## [%d] %s"%(i,s["title"]))
    for j,p in enumerate(s["paras"]): out.append("  p%d: %s"%(j,p if isinstance(p,str) else json.dumps(p,ensure_ascii=False)))
    if s.get("table"): out.append("  TABLE: "+json.dumps(s["table"],ensure_ascii=False))
open("_part3.txt","w",encoding="utf-8").write("\n".join(out))
print(len("\n".join(out)))

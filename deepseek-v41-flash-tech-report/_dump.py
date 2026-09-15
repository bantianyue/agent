import json,io,sys
sys.stdout.reconfigure(encoding="utf-8")
d=json.load(open("article_data.json",encoding="utf-8"))
print("TITLE:",d["title"])
print("REF:",d["reference_url"])
print("SUMMARY:")
for s in d["summary"]: print("  -",s["key"],":",s["body"])
print("LEAD:")
for x in d["lead"]: print("  ",x[:200])
for i,s in enumerate(d["sections"]):
    print("--[%d] type=%s title=%s"%(i,s["type"],s["title"]))
    for p in s["paras"][:4]:
        if isinstance(p,str): print("    ",p[:140])
        else: print("    ",{k:str(v)[:70] for k,v in p.items()})
print("CONCLUSION:")
for x in d["conclusion"]: print("  ",x[:300])

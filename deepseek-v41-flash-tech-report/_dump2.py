import json,sys
sys.stdout.reconfigure(encoding="utf-8")
d=json.load(open("article_data.json",encoding="utf-8"))
for i,s in enumerate(d["sections"]):
    print("[%d] type=%s title=%s keys=%s paras=%d"%(i,s.get("type"),s.get("title"),list(s.keys()),len(s.get("paras",[]))))
    print("   fig_after:",s.get("fig_after"), "table:",bool(s.get("table")))
print("top keys:",list(d.keys()))
for k in d:
    if k not in ("sections",): print(k,"=",str(d[k])[:200])

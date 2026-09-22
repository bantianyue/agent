import json, sys
sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open("article_data.json", encoding="utf-8"))
out = []
for i, p in enumerate(d["lead"]):
    out.append("L%d||%s" % (i, p))
for i, p in enumerate(d["summary"]):
    out.append("S%d||%s||%s" % (i, p["key"], p["body"]))
for i, s in enumerate(d["sections"]):
    out.append("#### SEC%d [%s] %s" % (i, s["type"], s["title"]))
    for j, p in enumerate(s["paras"]):
        out.append("%d.%d||%s" % (i, j, p))
    if s.get("fig_after"):
        out.append("   FIGAFTER %s" % json.dumps(s["fig_after"], ensure_ascii=False))
    if s.get("table"):
        out.append("   TABLE %s" % json.dumps(s["table"], ensure_ascii=False))
for i, p in enumerate(d["conclusion"]):
    out.append("C%d||%s" % (i, p))
open("_dump.txt", "w", encoding="utf-8").write("\n".join(out))
print("chars", len("\n".join(out)))

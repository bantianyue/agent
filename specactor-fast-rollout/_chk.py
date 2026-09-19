import json, re
items = json.load(open("_content.json", encoding="utf-8"))
print(items[133]["text"][:400])
print("---")
s = json.dumps(json.load(open("article_data.json", encoding="utf-8")), ensure_ascii=False)
for pat in ["草稿生成", "profiled", "草稿器 "] :
    print("##", pat, s.count(pat))
for m in re.finditer(r".{0,30}草稿生成.{0,20}", s):
    print("   *", m.group(0))

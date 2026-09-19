import os, json, shutil
ORDER = ["fig01","fig11","fig02","fig13","fig09","fig12","fig10","fig14","fig03","fig08","fig04","fig07","fig06","fig05","fig00","fig15"]
mapping = {}
for i, old in enumerate(ORDER, start=1):
    mapping[old] = "fig%02d" % i
# 两阶段重命名防冲突
for old, new in mapping.items():
    if old != new:
        shutil.move(old + ".png", "tmp_" + new + ".png")
for old, new in mapping.items():
    if old != new:
        shutil.move("tmp_" + new + ".png", new + ".png")
print("renamed:", mapping)
# 回写 _content.json 的 src
items = json.load(open("_content.json", encoding="utf-8"))
for x in items:
    if x["kind"] == "fig":
        base = os.path.splitext(x["src"])[0]
        x["src"] = mapping[base] + ".png"
json.dump(items, open("_content.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print([x["src"] for x in items if x["kind"]=="fig"])

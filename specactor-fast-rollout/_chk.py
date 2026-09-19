import json, re
d = json.load(open("article_data.json", encoding="utf-8"))
s = json.dumps(d, ensure_ascii=False)
print("=== x-mult ===")
for m in re.finditer(r".{22}×.{12}", s): print(" |", m.group(0))
print("=== cjk-cjk space samples ===")
sp = re.findall(r"[\u4e00-\u9fff]\s+[\u4e00-\u9fff]", s)
print(len(sp), sp[:20])
print("=== backticks/other ===")
for pat in ["``", "''", "^th", "3.%", "（ 64", "草稿器 ", " 草稿器"]:
    print(repr(pat), s.count(pat))

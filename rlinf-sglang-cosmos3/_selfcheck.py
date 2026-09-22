import json, re, sys
sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open("article_data.json", encoding="utf-8"))
texts = list(d["lead"]) + [x["body"] for x in d["summary"]] + list(d["conclusion"])
for s in d["sections"]:
    texts += list(s["paras"])
    texts.append(s["title"])
    texts.append("")
texts.append(d["title"])
bad = 0
for pat in ["我们", "咱们", "我", "它"]:
    for t in texts:
        body = re.sub(r"<[^>]+>", "", t)
        for m in re.finditer(pat, body):
            bad += 1
            print("HIT", pat, "|", body[max(0, m.start() - 20):m.start() + 20])
print("hits", bad)
print("chars", sum(len(re.sub(r"<[^>]+>", "", t)) for t in texts))

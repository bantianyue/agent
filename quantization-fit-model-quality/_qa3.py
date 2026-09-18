import re

h = open("article.html", encoding="utf-8").read()
h = re.sub(r"<figcaption[^>]*>.*?</figcaption>", "[CAP]", h, flags=re.S)
h = re.sub(r"<img[^>]*>", "\n[IMG]\n", h)
t = re.sub(r"<[^>]+>", "", h)
t = re.sub(r"&nbsp;", " ", t)
t = re.sub(r"\n{2,}", "\n", t)
lines = [l.strip() for l in t.split("\n") if l.strip()]
print(len(lines))
for l in lines[:60]:
    print(l[:150])

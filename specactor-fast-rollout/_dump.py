import re
h = open("article.html", encoding="utf-8").read()
# 去掉 <style>/<script>，正文按块提取
body = h
txt = re.sub(r"<br\s*/?>", "\n", body)
txt = re.sub(r"</(p|h1|h2|h3|figcaption|figure|div|td|th|tr|li)>", "\n", txt)
txt = re.sub(r"<[^>]+>", "", txt)
txt = re.sub(r"\n{3,}", "\n\n", txt)
lines = [l.strip() for l in txt.split("\n")]
out = [l for l in lines if l]
print(len(out), "lines")
print("\n".join(out))

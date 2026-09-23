import urllib.request, re, sys, json

url = "https://arxiv.org/abs/2308.16369v1"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
html = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "ignore")
title = re.search(r'<h1 class="title mathjax"><span class="descriptor">Title:</span>(.*?)</h1>', html, re.S)
if not title:
    title = re.search(r"<title>(.*?)</title>", html, re.S)
abs_ = re.search(r'<blockquote class="abstract mathjax">(.*?)</blockquote>', html, re.S)
out = []
out.append("TITLE: " + re.sub(r"<[^>]+>|\\s+", lambda m: " " if "<" in m.group(0) else m.group(0), (title.group(1) if title else "")).strip())
if abs_:
    out.append("ABS: " + re.sub(r"<[^>]+>", "", abs_.group(1)).replace("\n", " ").strip())
else:
    out.append("ABS: <none>")
open(r"D:\06_Hermes\articles\_tmp_meta.txt", "w", encoding="utf-8").write("\n".join(out))
print("OK")

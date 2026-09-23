# -*- coding: utf-8 -*-
import urllib.request, re, os, json, html as H

ART = r"D:\06_Hermes\articles\sarathi"
URL = "https://arxiv.org/html/2308.16369v1"
req = urllib.request.Request(URL, headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
    "Referer": "https://arxiv.org/",
})
raw = urllib.request.urlopen(req, timeout=90).read().decode("utf-8", "ignore")
open(os.path.join(ART, "_raw.html"), "w", encoding="utf-8").write(raw)

print("RAWLEN", len(raw))

# figures
figs = re.findall(r"<figure[^>]*>.*?</figure>", raw, re.S)
print("FIGURES", len(figs))
for i, f in enumerate(figs):
    cap = re.search(r"<figcaption[^>]*>(.*?)</figcaption>", f, re.S)
    captxt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", cap.group(1))).strip() if cap else ""
    objs = re.findall(r'<object[^>]*data="([^"]+)"', f)
    imgs = re.findall(r'<img[^>]*src="([^"]+)"', f)
    print(i, "OBJ", objs, "IMG", imgs, "CAP", captxt[:160])

# ltxml tables
print("TABLES", len(re.findall(r"<table", raw)))

# section headings
heads = re.findall(r'<h([1-3])[^>]*>(.*?)</h\1>', raw, re.S)
print("HEADS", len(heads))
for lvl, h in heads:
    print(" ", lvl, re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", h)).strip()[:120])

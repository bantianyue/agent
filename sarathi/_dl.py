# -*- coding: utf-8 -*-
import re, os, json, html as HH, urllib.request

ART = r"D:\06_Hermes\articles\sarathi"
raw = open(os.path.join(ART, "_raw.html"), encoding="utf-8").read()
BASE = "https://arxiv.org/html/"

figs = re.findall(r"<figure[^>]*>.*?</figure>", raw, re.S)
assets = []
for i, f in enumerate(figs):
    cap = re.search(r"<figcaption[^>]*>(.*?)</figcaption>", f, re.S)
    captxt = ""
    if cap:
        captxt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", HH.unescape(cap.group(1)))).strip()
    objs = re.findall(r'<object[^>]*data="([^"]+)"', f)
    imgs = re.findall(r'<img[^>]*src="([^"]+)"', f)
    src = (objs + imgs)[0] if (objs + imgs) else None
    assets.append((i, src, captxt))

hdr = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
       "Referer": "https://arxiv.org/html/2308.16369v1"}

out = []
manifest = []
for i, src, cap in assets:
    if not src:
        continue
    url = BASE + src.lstrip("/")
    ext = ".svg" if src.lower().endswith(".svg") else ".png"
    fn = "src%02d%s" % (i, ext)
    dst = os.path.join(ART, fn)
    ok = False
    try:
        req = urllib.request.Request(url, headers=hdr)
        data = urllib.request.urlopen(req, timeout=90).read()
        open(dst, "wb").write(data)
        ok = True
        out.append("OK  %s  %d bytes  <- %s" % (fn, len(data), url))
    except Exception as e:
        out.append("ERR %s  %s" % (url, e))
    manifest.append({"fig_index": i, "file": fn if ok else None, "url": url, "caption": cap})

open(os.path.join(ART, "_dl_out.txt"), "w", encoding="utf-8").write("\n".join(out))
open(os.path.join(ART, "_manifest.json"), "w", encoding="utf-8").write(
    json.dumps(manifest, ensure_ascii=False, indent=1))
print("done", len(manifest))

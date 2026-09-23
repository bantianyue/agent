import urllib.request, re, ssl, json, sys
ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
url = "https://archerhume.com/posts/jevs-architecture-unmasked/?v=3"
req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0 Safari/537.36"})
h = urllib.request.urlopen(req, timeout=60, context=ctx).read().decode("utf-8", "replace")
open("_page.html","w",encoding="utf-8").write(h)
print("len", len(h))
print("img", len(re.findall(r'<img', h)))
print("iframe", len(re.findall(r'<iframe', h)))
print("svg", len(re.findall(r'<svg', h)))
print("canvas", len(re.findall(r'<canvas', h)))
print("figure", len(re.findall(r'<figure', h)))
print("pre", len(re.findall(r'<pre', h)))
print("script", len(re.findall(r'<script', h)))
print("h2", len(re.findall(r'<h2', h)))
print("h3", len(re.findall(r'<h3', h)))
for m in re.findall(r'<img[^>]*>', h)[:40]:
    print("IMG:", m[:220])
for m in re.findall(r'<iframe[^>]*>', h)[:20]:
    print("IFRAME:", m[:300])
print("--- rAF/paint ---")
print("rAF", h.count("requestAnimationFrame"), "paint(", h.count("paint("))

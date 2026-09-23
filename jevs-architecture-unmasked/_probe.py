import urllib.request, re, ssl, os, sys
for k in ("HTTP_PROXY","HTTPS_PROXY","http_proxy","https_proxy","ALL_PROXY","all_proxy"):
    os.environ.pop(k, None)
os.environ["NO_PROXY"] = "*"
ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
url = "https://archerhume.com/posts/jevs-architecture-unmasked/?v=3"
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0 Safari/537.36"})
h = opener.open(req, timeout=90).read().decode("utf-8", "replace")
open("_page.html","w",encoding="utf-8").write(h)
out=[]
out.append("len %d" % len(h))
for tag in ("img","iframe","svg","canvas","figure","figcaption","pre","script","h2","h3","table","video"):
    out.append("%s %d" % (tag, len(re.findall(r'<'+tag, h))))
out.append("rAF %d paint( %d" % (h.count("requestAnimationFrame"), h.count("paint(")))
out.append("--- IMG ---")
for m in re.findall(r'<img[^>]*>', h)[:60]:
    out.append(m[:260])
out.append("--- IFRAME ---")
for m in re.findall(r'<iframe[^>]*>', h)[:20]:
    out.append(m[:300])
out.append("--- SVG inline ---")
for m in re.findall(r'<svg[^>]*>', h)[:20]:
    out.append(m[:200])
out.append("--- object ---")
for m in re.findall(r'<object[^>]*>', h)[:20]:
    out.append(m[:260])
open("_probe.txt","w",encoding="utf-8").write("\n".join(out))
print("done")

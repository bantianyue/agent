import re
h = open("_page.html", encoding="utf-8", errors="replace").read()
out = ["len %d" % len(h)]
for tag in ("img","iframe","svg","canvas","figure","figcaption","pre","script","h2","h3","table","video","picture","source"):
    out.append("%s %d" % (tag, len(re.findall(r'<'+tag, h))))
out.append("rAF %d  paint( %d" % (h.count("requestAnimationFrame"), h.count("paint(")))
out.append("--- IMG ---")
for m in re.findall(r'<img[^>]*>', h)[:80]:
    out.append(m[:300])
out.append("--- IFRAME ---")
for m in re.findall(r'<iframe[^>]*>', h)[:20]:
    out.append(m[:300])
out.append("--- OBJECT ---")
for m in re.findall(r'<object[^>]*>', h)[:20]:
    out.append(m[:300])
out.append("--- inline svg count %d ---" % len(re.findall(r'<svg', h)))
for m in re.findall(r'<svg[^>]*>', h)[:20]:
    out.append(m[:200])
out.append("--- H2 ---")
for m in re.findall(r'<h2[^>]*>(.*?)</h2>', h, re.S)[:40]:
    out.append(re.sub(r'<[^>]+>','',m).strip()[:150])
out.append("--- H3 ---")
for m in re.findall(r'<h3[^>]*>(.*?)</h3>', h, re.S)[:40]:
    out.append(re.sub(r'<[^>]+>','',m).strip()[:150])
out.append("--- src attrs (any) ---")
for m in sorted(set(re.findall(r'src="([^"]+)"', h)))[:80]:
    out.append(m[:200])
open("_probe.txt","w",encoding="utf-8").write("\n".join(out))
print("ok")

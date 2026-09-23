# -*- coding: utf-8 -*-
import urllib.request, os, re
op = urllib.request.build_opener(urllib.request.ProxyHandler({"http":"http://127.0.0.1:7890","https":"http://127.0.0.1:7890"}))
UA = {"User-Agent":"Mozilla/5.0"}
out = []
for f in ["_astro/ArchitectureStudy.astro_astro_type_script_index_0_lang.CkkUmszh.js"]:
    u = "https://archerhume.com/" + f
    try:
        b = op.open(urllib.request.Request(u, headers=UA), timeout=60).read()
        open("_arch.js","wb").write(b)
        out.append("saved %d" % len(b))
    except Exception as e:
        out.append("fail %r" % e)
s = open("_arch.js", encoding="utf-8", errors="replace").read()
out.append("len %d" % len(s))
for pat in [r'duration', r'\bsetInterval\b', r'requestAnimationFrame', r'DURATION', r'seek', r'replay', r'stage']:
    hits = re.findall('.{60}' + pat + '.{100}', s, re.I)
    out.append("--- %s : %d" % (pat, len(hits)))
    for hh in hits[:10]:
        out.append("    " + hh.replace("\n", " ")[:170])
open("_dl.txt","w",encoding="utf-8").write("\n".join(out))

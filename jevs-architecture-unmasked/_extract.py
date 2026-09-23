# -*- coding: utf-8 -*-
import re, os, json
from bs4 import BeautifulSoup

h = open("_page.html", encoding="utf-8", errors="replace").read()
soup = BeautifulSoup(h, "html.parser")

# locate main article
main = soup.find("article") or soup.find("main") or soup.body
print("main tag:", main.name if main else None)

figs = main.find_all("figure")
print("figure count:", len(figs))
os.makedirs("svg_raw", exist_ok=True)
meta = []
for i, f in enumerate(figs, 1):
    cap = f.find("figcaption")
    cap_html = str(cap) if cap else ""
    cap_text = cap.get_text("\n", strip=True) if cap else ""
    svgs = f.find_all("svg")
    info = {"idx": i, "caption": cap_text, "n_svg": len(svgs)}
    for j, s in enumerate(svgs):
        fn = "svg_raw/fig%02d_%d.svg" % (i, j)
        s_str = str(s)
        if 'xmlns' not in s_str:
            s_str = s_str.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
        open(fn, "w", encoding="utf-8").write(s_str)
        info.setdefault("files", []).append(fn)
    meta.append(info)
    print(i, "n_svg", len(svgs), "|", cap_text[:200].replace("\n", " "))

json.dump(meta, open("_figs_meta.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# dump document order text
out = []
SKIP = {"script", "style", "nav", "footer", "header"}
for el in main.find_all(["h1","h2","h3","h4","p","li","figcaption","pre","blockquote","td","th","table","figure","strong","em","code","div"]):
    pass

def walk(node, depth=0):
    for c in node.children:
        if getattr(c, "name", None) is None:
            t = str(c).strip()
            if t:
                out.append(("TEXT:" + t))
            continue
        if c.name in SKIP:
            continue
        if c.name in ("h1","h2","h3","h4"):
            out.append(c.name.upper() + ": " + c.get_text(" ", strip=True))
        elif c.name == "p":
            out.append("P: " + c.get_text(" ", strip=True))
        elif c.name == "li":
            out.append("LI: " + c.get_text(" ", strip=True))
        elif c.name == "figcaption":
            out.append("FIGCAP: " + c.get_text(" ", strip=True))
        elif c.name == "pre":
            out.append("PRE_START")
            out.append(c.get_text("", strip=False))
            out.append("PRE_END")
        elif c.name == "figure":
            out.append("FIGURE_BLOCK_%d" % (len([x for x in out if x.startswith("FIGURE_BLOCK")]) + 1))
            # still walk for caption
            for cc in c.children:
                if getattr(cc, "name", None) == "figcaption":
                    out.append("FIGCAP: " + cc.get_text(" ", strip=True))
            continue
        elif c.name == "blockquote":
            out.append("QUOTE: " + c.get_text(" ", strip=True))
        else:
            walk(c, depth + 1)

walk(main)
open("_content_dump.txt", "w", encoding="utf-8").write("\n".join(out))
print("dump lines:", len(out))
print("total chars:", sum(len(x) for x in out))

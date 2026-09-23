# -*- coding: utf-8 -*-
import re, os, json, html as HH
from bs4 import BeautifulSoup

ART = r"D:\06_Hermes\articles\sarathi"
raw = open(os.path.join(ART, "_raw.html"), encoding="utf-8").read()
soup = BeautifulSoup(raw, "lxml")

body = soup.find("article") or soup.find("div", class_="ltx_page_main") or soup

blocks = []
cur_h2 = ""
cur_h3 = ""

def txtof(el):
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()

# iterate over direct descendants in document order
sec_re = re.compile(r"^section$|^div$")
for el in body.find_all(["h1", "h2", "h3", "h4", "p", "ul", "ol", "figure", "table"]):
    # skip nested (p inside li etc.)
    if el.find_parent(["p", "li", "figure", "table", "h1", "h2", "h3", "h4"]):
        # allow figure/table nested in section only
        if el.name not in ("p", "li"):
            pass
        else:
            continue
    nm = el.name
    cls = " ".join(el.get("class") or [])
    if nm in ("h1", "h2", "h3", "h4"):
        t = txtof(el)
        if nm in ("h1", "h2"):
            cur_h2 = t
        elif nm == "h3":
            cur_h3 = t
        blocks.append({"type": nm, "text": t})
    elif nm == "p":
        t = txtof(el)
        if not t:
            continue
        blocks.append({"type": "p", "h2": cur_h2, "h3": cur_h3, "text": t})
    elif nm in ("ul", "ol"):
        items = [txtof(li) for li in el.find_all("li", recursive=False)]
        items = [i for i in items if i]
        if items:
            blocks.append({"type": "list", "h2": cur_h2, "h3": cur_h3, "items": items})
    elif nm == "figure":
        cap = el.find("figcaption")
        capt = txtof(cap) if cap else ""
        objs = [o.get("data", "") for o in el.find_all("object")]
        imgs = [i.get("src", "") for i in el.find_all("img")]
        src = (objs + imgs)[0] if (objs + imgs) else None
        tbl = el.find("table")
        if src:
            blocks.append({"type": "figure", "h2": cur_h2, "h3": cur_h3, "src": src, "caption": capt})
        elif tbl is not None:
            rows = []
            thead = tbl.find("thead")
            tbody = tbl.find("tbody")
            if thead:
                for tr in thead.find_all("tr"):
                    rows.append([txtof(c) for c in tr.find_all(["td", "th"])])
            if tbody:
                for tr in tbody.find_all("tr"):
                    rows.append([txtof(c) for c in tr.find_all(["td", "th"])])
            else:
                for tr in tbl.find_all("tr"):
                    rows.append([txtof(c) for c in tr.find_all(["td", "th"])])
            # dedupe
            seen = set()
            r2 = []
            for r in rows:
                k = tuple(r)
                if k in seen:
                    continue
                seen.add(k)
                r2.append(r)
            blocks.append({"type": "table", "h2": cur_h2, "h3": cur_h3, "caption": capt, "rows": r2})
        else:
            blocks.append({"type": "figure_other", "h2": cur_h2, "h3": cur_h3, "caption": capt})

open(os.path.join(ART, "_blocks.json"), "w", encoding="utf-8").write(
    json.dumps(blocks, ensure_ascii=False, indent=1))

lines = []
for b in blocks:
    if b["type"] in ("h1", "h2", "h3", "h4"):
        lines.append("\n\n" + "#" * int(b["type"][1]) + " " + b["text"])
    elif b["type"] == "p":
        lines.append("[P] " + b["text"])
    elif b["type"] == "list":
        lines.append("[L] " + " || ".join(b["items"]))
    elif b["type"] == "figure":
        lines.append("[FIG:%s] %s" % (b["src"], b["caption"]))
    elif b["type"] == "table":
        lines.append("[TABLE] %s" % b["caption"])
        for r in b["rows"]:
            lines.append("   | " + " | ".join(r))
    else:
        lines.append("[OTHER] " + b.get("caption", ""))
open(os.path.join(ART, "_fulltext.txt"), "w", encoding="utf-8").write("\n".join(lines))

from collections import Counter
c = Counter(b["type"] for b in blocks)
print(c)
print("chars", sum(len(b.get("text", "")) for b in blocks))

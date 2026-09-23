# -*- coding: utf-8 -*-
import os, re, json, shutil

ART = r"D:\06_Hermes\articles\sarathi"
blocks = json.load(open(os.path.join(ART, "_blocks.json"), encoding="utf-8"))

# 1) figure order -> figNN
fig_map = []   # ordered unique figure src list (doc order, dedup)
seen = set()
for b in blocks:
    if b["type"] == "figure":
        if b["src"] in seen:
            continue
        seen.add(b["src"])
        fig_map.append(b["src"])

src_to_file = {}
for b in blocks:
    if b["type"] == "figure":
        base = os.path.basename(b["src"])
        stem = os.path.splitext(base)[0]
        # find downloaded file
        for cand in os.listdir(ART):
            if cand.startswith("src") and os.path.splitext(cand)[0] == "src" + b["src"][-len(b["src"]):][:0]:
                pass
        src_to_file[b["src"]] = None

# simpler: rebuild mapping from _manifest (fig_index -> file)
man = json.load(open(os.path.join(ART, "_manifest.json"), encoding="utf-8"))
url2file = {m["url"]: m["file"] for m in man if m["file"]}
BASE = "https://arxiv.org/html/"
mapping = []
for i, src in enumerate(fig_map, 1):
    url = BASE + src.lstrip("/")
    old = url2file.get(url)
    mapping.append({"fig": "fig%02d.png" % i, "src": src, "old": old})
    if old:
        shutil.copyfile(os.path.join(ART, old), os.path.join(ART, "fig%02d.png" % i))
json.dump(mapping, open(os.path.join(ART, "_figmap.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# 2) clean math artifacts
def clean(t):
    t = t.replace("\u200b", "").replace("\u2062", "").replace("\u2061", "")
    t = re.sub(r"\s*\\times\b", "", t)
    t = re.sub(r"\s+×", "×", t)
    t = re.sub(r"\(\s*×\s*\)", "", t)
    t = re.sub(r"\s*\\sim\b", "约", t)
    t = re.sub(r"\s*\\approx\b", "≈", t)
    t = re.sub(r"\s*\\theta\b", "θ", t)
    t = re.sub(r"\s*\\geq\b", "≥", t)
    t = re.sub(r"\s*\\times\s*", "", t)
    t = re.sub(r"\s+", " ", t)
    # bracket math [ B , L , H ] -> [B,L,H]
    def br(m):
        inner = m.group(1)
        if len(inner) < 30 and re.fullmatch(r"[A-Za-z0-9 ,\.\-_{}\^]+", inner):
            return "[" + re.sub(r"\s+", "", inner) + "]"
        return m.group(0)
    t = re.sub(r"\[([^\[\]]{1,30})\]", br, t)
    return t.strip()

# 3) ordered content with section path
items = []
cur2 = cur3 = ""
for b in blocks:
    if b["type"] in ("h1",):
        continue
    if b["type"] in ("h2", "h3", "h4"):
        t = b["text"]
        if b["type"] == "h2":
            cur2, cur3 = t, ""
        elif b["type"] == "h3":
            cur3 = t
        items.append({"kind": "head", "level": b["type"], "text": t})
    elif b["type"] == "p":
        items.append({"kind": "p", "h2": cur2, "h3": cur3, "text": clean(b["text"])})
    elif b["type"] == "list":
        for it in b["items"]:
            items.append({"kind": "p", "h2": cur2, "h3": cur3, "text": clean(it), "list": True})
    elif b["type"] == "figure":
        items.append({"kind": "fig", "h2": cur2, "h3": cur3, "src": b["src"], "caption": clean(b["caption"])})
    elif b["type"] == "table":
        items.append({"kind": "table", "h2": cur2, "h3": cur3, "caption": clean(b["caption"]),
                      "rows": [[clean(c) for c in r] for r in b["rows"]]})

json.dump(items, open(os.path.join(ART, "_items.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# stats: paragraphs in sections 1..8 (exclude References)
np_ = sum(1 for it in items if it["kind"] == "p")
print("items", len(items), "paras", np_)
secs = [it["text"] for it in items if it["kind"] == "head" and it["level"] == "h2"]
print(secs)

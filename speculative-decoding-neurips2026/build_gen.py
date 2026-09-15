# -*- coding: utf-8 -*-
"""content.txt (S#/H3/T/L/N/Q/C/F/TH/TR) -> article_data_build.py (DATA dict)

用法: python build_gen.py
产物: <本目录>/article_data_build.py  (只定义 DATA，落盘交给 write-article-data.py)
"""
import json, os, re

D = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(D, "content.txt")

meta = {"title": "", "reference_url": "", "summary": [], "lead": []}
sections = []
cur = None
code_buf = []
lang = ""
table = None
order = []          # 记录顶层块顺序，用于 table/caption 交错


def new_sec(kind, title):
    global cur
    cur = {"type": kind, "title": title, "paras": [], "fig_after": {}}
    sections.append(cur)
    return cur


def flush_code():
    global code_buf, lang
    if code_buf:
        body = "\n".join(code_buf)
        cur["paras"].append("__CODE__" + (lang + "::" if lang else "") + body)
    code_buf = []
    lang = ""


def add_para(text):
    flush_code()
    cur["paras"].append(text)


for raw in open(SRC, encoding="utf-8").read().split("\n"):
    line = raw.rstrip()
    if not line.strip():
        continue
    if line.startswith("#"):            # 注释行
        continue
    if line.startswith("CONC|"):        # 结语在末尾单独收集
        continue
    if line.startswith("TITLE|"):
        meta["title"] = line[6:].strip(); continue
    if line.startswith("REF|"):
        meta["reference_url"] = line[4:].strip(); continue
    if line.startswith("SUM|"):
        _, k, b = line.split("|", 2); meta["summary"].append({"key": k.strip(), "body": b.strip()}); continue
    if line.startswith("LEAD|"):
        meta["lead"].append(line[5:].strip()); continue
    if line.startswith("S# "):
        flush_code(); new_sec("h2", line[3:].strip()); continue
    if line.startswith("H3 "):
        flush_code(); new_sec("h3", line[3:].strip()); continue
    if line.startswith("P#"):
        flush_code(); new_sec("p", ""); continue
    if line.startswith("T "):
        add_para(line[2:].strip()); continue
    if line.startswith("L "):
        add_para('<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">&#9679;</span>&nbsp;' + line[2:].strip()); continue
    if line.startswith("N "):
        num, txt = line[2:].split("|", 1)
        add_para('<span style="color:#0F4C81;font-weight:bold;">' + num.strip() + '</span>&nbsp;' + txt.strip()); continue
    if line.startswith("Q "):
        add_para('<span style="display:block;background:#f5f8fb;border-left:3px solid #0F4C81;padding:10px 14px;border-radius:4px;">' + line[2:].strip() + '</span>'); continue
    if line.startswith("K "):
        add_para('<span style="display:block;background:#fdf6e8;border-left:3px solid #c9a227;padding:10px 14px;border-radius:4px;">' + line[2:].strip() + '</span>'); continue
    if line.startswith("C#") and not code_buf:
        lang = line[2:].strip(); continue
    if line == "C":
        code_buf.append(""); continue
    if line.startswith("C "):
        code_buf.append(line[2:]); continue
    if line.startswith("F "):
        flush_code()
        fn, cap = (line[2:].split("|", 1) + [""])[:2]
        src = [x.strip() for x in fn.split("+")] if "+" in fn else fn.strip()
        idx = max(0, len(cur["paras"]) - 1)
        cur["fig_after"].setdefault(str(idx), []).append({"src": src, "caption": cap.strip()})
        continue
    if line.startswith("TH "):
        flush_code()
        table = {"head": [c.strip() for c in line[3:].split("||")], "rows": []}
        cur["table"] = table
        continue
    if line.startswith("TR "):
        table["rows"].append([c.strip() for c in line[3:].split("||")])
        continue
    raise SystemExit("未识别的行: " + line[:60])

flush_code()

DATA = {
    "title": meta["title"],
    "summary": meta["summary"],
    "lead": meta["lead"],
    "sections": sections,
    "conclusion": [],
    "reference_url": meta["reference_url"],
}

# conclusion 来自 content.txt 末尾的 CONC| 行
conc = []
for raw in open(SRC, encoding="utf-8").read().split("\n"):
    if raw.startswith("CONC|"):
        conc.append(raw[5:].strip())
DATA["conclusion"] = conc

# ---- 自检 ----
nfig = sum(len(v) for s in sections for v in s["fig_after"].values())
ntab = sum(1 for s in sections if s.get("table"))
ncode = sum(1 for s in sections for p in s["paras"] if p.startswith("__CODE__"))
print("sections", len(sections), "paras", sum(len(s["paras"]) for s in sections),
      "figs", nfig, "tables", ntab, "code", ncode)
for s in sections:
    for k in s["fig_after"]:
        assert int(k) < len(s["paras"]), f"fig_after 越界 {s['title']} key={k} paras={len(s['paras'])}"
files = {f for f in os.listdir(D) if f.startswith("fig") and f.endswith((".png", ".gif"))}
used = set()
for s in sections:
    for v in s["fig_after"].values():
        for g in v:
            src = g["src"]
            used.update(src if isinstance(src, list) else [src])
print("磁盘图", len(files), "引用图", len(used), "缺失", sorted(used - files), "未用", sorted(files - used))

out = os.path.join(D, "article_data_build.py")
with open(out, "w", encoding="utf-8") as f:
    f.write("import json, os, sys\n\nDATA = " + json.dumps(DATA, ensure_ascii=False, indent=2) + "\n")
print("wrote", out, len(json.dumps(DATA, ensure_ascii=False)), "chars")

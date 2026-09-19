import re, os, json

BASE = "_src_tmp/"
FILES = ["abs.tex","body/intro.tex","body/bg.tex","body/overview-v3.tex","body/design-v2.tex","body/eval.tex","body/related.tex","body/concl.tex"]

raw = {}
for f in FILES:
    raw[f] = open(BASE+f, encoding="utf-8", errors="ignore").read()

# ---- 1. label -> number maps (document order) ----
sec_map, fig_map, alg_map = {}, {}, {}
sec_n, sub_n, fig_n, alg_n = 0, 0, 0, 0
for f in FILES:
    for m in re.finditer(r"\\(section|subsection|begin\{figure|begin\{algorithm)(\*)?\}", raw[f]):
        pass
for f in FILES:
    t = re.sub(r"(?m)^\s*%.*$", "", raw[f])
    for m in re.finditer(r"\\section\*?\{[^}]*\}((?:\s*\\label\{[^}]*\})?)", t):
        sec_n += 1; sub_n = 0
        lab = re.search(r"\\label\{([^}]*)\}", m.group(1) or "")
        if lab: sec_map[lab.group(1)] = str(sec_n)
    for m in re.finditer(r"\\subsection\*?\{[^}]*\}((?:\s*\\label\{[^}]*\})?)", t):
        sub_n += 1
        lab = re.search(r"\\label\{([^}]*)\}", m.group(1) or "")
        if lab: sec_map[lab.group(1)] = "%d.%d" % (sec_n, sub_n)
    for m in re.finditer(r"\\begin\{figure\}(.*?)\\end\{figure\}", t, re.S):
        fig_n += 1
        lab = re.search(r"\\label\{([^}]*)\}", m.group(1))
        if lab: fig_map[lab.group(1)] = str(fig_n)
    for m in re.finditer(r"\\label\{(alg:[^}]*)\}", t):
        alg_n += 1; alg_map[m.group(1)] = str(alg_n)
json.dump({"sec":sec_map,"fig":fig_map,"alg":alg_map}, open("_labels.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("figs:",fig_n,"secs:",sec_n,"algs:",alg_n)
print(json.dumps(fig_map, ensure_ascii=False))

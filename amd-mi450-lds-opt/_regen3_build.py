# -*- coding: utf-8 -*-
"""再生-3：写回译文 + 微信化样式 + 输出 article.html / article_zh.html（格式 100% 保留）。"""
import re, json
from bs4 import BeautifulSoup

BASE = r"D:/06_Hermes/articles/amd-mi450-lds-opt"
TAGS = ["h1", "h2", "h3", "h4", "h5", "p", "li", "dd", "dt", "td", "th", "figcaption"]
TOKEN = {
    "c1": "#515151", "cm": "#515151", "c": "#515151", "k": "#6730c5", "kn": "#6730c5",
    "kd": "#6730c5", "ow": "#00622f", "mi": "#7f4707", "mf": "#7f4707", "m": "#7f4707",
    "il": "#7f4707", "o": "#00622f", "p": "#080808", "n": "#080808", "nn": "#080808",
    "nx": "#080808", "x": "#080808", "nb": "#7f4707", "s": "#00622f", "s1": "#00622f",
    "s2": "#00622f", "nf": "#005b82", "nd": "#005b82", "fm": "#005b82", "kt": "#6730c5",
    "vi": "#005b82", "err": "#a40000",
}
URL = "https://rocm.blogs.amd.com/software-tools-optimization/mi450-lds-optimization/README.html"


def collect(art):
    out = []
    for el in art.find_all(TAGS):
        if el.find_parent("pre"):
            continue
        anc, nested = el.parent, False
        while anc is not None and anc is not art:
            if getattr(anc, "name", None) in TAGS:
                nested = True
                break
            anc = anc.parent
        if nested:
            continue
        out.append(el)
    return out


blocks = {b["i"]: b for b in json.load(open(f"{BASE}/_regen_blocks.json", encoding="utf-8"))}
zh = {int(k): v for k, v in json.load(open(f"{BASE}/_regen_zh.json", encoding="utf-8")).items()}

soup = BeautifulSoup(open(f"{BASE}/_regen_art.html", encoding="utf-8").read(), "html.parser")
art = soup.find("article")
els = collect(art)
print("elements:", len(els))

done = 0
for i, el in enumerate(els):
    b = blocks.get(i)
    if not b:
        continue
    if i not in zh:
        continue
    restored = zh[i]
    for ph, orig in b["ph"].items():
        restored = restored.replace(ph, orig)
    restored = (
        restored.replace("\u00abB\u00bb", "<strong>").replace("\u00ab/B\u00bb", "</strong>")
        .replace("\u00abI\u00bb", "<em>").replace("\u00ab/I\u00bb", "</em>")
    )
    repl = BeautifulSoup(f"<{el.name}>" + restored + f"</{el.name}>", "html.parser").find()
    if repl is None:
        print("  !! 重建失败 idx=", i, el.name)
        continue
    el.replace_with(repl)
    done += 1
print("写回块数:", done, "/", len(zh))

# ---------- 微信化样式 ----------

# 1) 行内小代码（变量/函数名高亮底纹）
for code in art.find_all("code"):
    if code.find_parent("pre"):
        continue
    cls = code.get("class") or []
    if any(c in ("literal", "docutils", "pre") for c in cls) or code.find("span", class_="pre"):
        code["style"] = (
            ";background:#f3f4f5;padding:2px 5px;border-radius:3px;color:#222832;"
            "font-size:13px;font-family:Consolas,Monaco,monospace;"
        )

# 2) 代码块：底纹 + token 配色 + 空格转 &nbsp;
for hlight in art.select("div.highlight, div.highlight-python, div[class^=highlight], section[class^=highlight]"):
    hlight["style"] = "background:#f3f4f5;border-radius:4px;overflow-x:auto;"
    pre = hlight.find("pre")
    if pre:
        pre["style"] = (
            "padding:14px 16px;line-height:1.5;white-space:pre;overflow-x:auto;"
            "font-size:13px;font-family:Consolas,Monaco,'Courier New',monospace;"
        )
        for txt in pre.find_all(string=True):
            txt.replace_with(txt.replace(" ", "\u00a0"))
    for sp in hlight.find_all("span"):
        if sp.get("style"):
            continue
        for c in sp.get("class") or []:
            if c in TOKEN:
                sp["style"] = f"color:{TOKEN[c]};"
                break

# 3) 行内代码里的空格也转 &nbsp;（微信端同样会塌缩）
for code in art.find_all("code"):
    if code.find_parent("pre"):
        continue
    for txt in code.find_all(string=True):
        if "  " in txt or txt.startswith(" ") or txt.endswith(" "):
            txt.replace_with(txt.replace(" ", "\u00a0"))

# 4) 图片 -> 本地 figNN + 自适应
imgmap = json.load(open(f"{BASE}/_imgmap.json", encoding="utf-8"))
byname = {k.rsplit("/", 1)[-1]: v for k, v in imgmap.items()}
for img in art.find_all("img"):
    src = img.get("src") or img.get("data-src") or ""
    fn = src.rsplit("/", 1)[-1]
    target = byname.get(fn)
    if target:
        img["src"] = target
    img["style"] = "max-width:100%;height:auto;"
    if img.get("data-src"):
        del img["data-src"]

# 5) 图注
for fig in art.find_all("figure"):
    cap = fig.find("figcaption")
    if cap:
        cap["style"] = (
            "font-size:12px;color:#666;text-align:center;margin-top:6px;padding:0 10px;line-height:1.5;"
        )

# 6) 表格
for tb in art.find_all("table"):
    tb["style"] = "border-collapse:collapse;width:100%;font-size:13px;margin:12px 0;"
    for cell in tb.find_all(["td", "th"]):
        cell["style"] = "border:1px solid #ddd;padding:6px 10px;text-align:left;"
    for th in tb.find_all("th"):
        th["style"] += "background:#f3f4f5;font-weight:bold;"

# 7) 段落 / 标题 / 列表
for p in art.find_all("p"):
    if not p.get("style"):
        p["style"] = "font-size:15px;line-height:1.8;margin:12px 0;color:#222832;"
for h in art.find_all(["h1", "h2", "h3", "h4", "h5"]):
    lv = int(h.name[1])
    sz = {1: "26px", 2: "21px", 3: "17px", 4: "15px", 5: "15px"}[lv]
    h["style"] = f"font-weight:bold;font-size:{sz};margin:22px 0 10px;color:#111;"
for ul in art.find_all(["ul", "ol"]):
    ul["style"] = "margin:10px 0 10px 22px;padding-left:16px;"
for li in art.find_all("li"):
    li["style"] = "font-size:15px;line-height:1.8;color:#222832;margin:4px 0;"
for sd in art.find_all(["strong", "b"]):
    sd["style"] = "font-weight:bold;color:#111;"

# 7b) 标题归一（与公众号标题一致、Part II 中文化）
h1 = art.find("h1")
if h1 is not None:
    h1.clear()
    h1.append("AMD Instinct MI450 GPU 上的 LDS 优化深度解析")
H2_FIX = {
    "第一部分：转置 LDS Load": "第一部分：转置 LDS 加载",
    "Part II：Partition Conflicts": "第二部分：分区冲突",
}
for h2 in art.find_all("h2"):
    t = h2.get_text(strip=True)
    if t in H2_FIX:
        h2.clear()
        h2.append(H2_FIX[t])

# 8) 清理 & 破折号
for sel in ["script", "style", "input", "a.headerlink", ".headerlink", ".onlyprint", "nav", "aside"]:
    for el in art.select(sel):
        el.decompose()

for txt in art.find_all(string=True):
    s = str(txt)
    if "—" in s:
        s2 = s.replace("——", "，").replace("—", "，")
        s2 = re.sub(r"，\s*，", "，", s2)
        txt.replace_with(s2)

body = str(art)
ref = (
    '<section style="margin-top:30px;padding:16px;background:#f5f0eb;border-radius:8px;'
    'font-size:13px;color:#555;line-height:1.8;">'
    "<strong>来源</strong><br>"
    "原文：A Deep Dive into LDS Optimizations on AMD Instinct MI450 GPUs（AMD ROCm Blogs）<br>"
    f"作者：Ognjen Plavsic、Nicola Zaghen、Lixun Zhang<br>链接：{URL}</section>"
)
WRAP_OPEN = (
    "<section style=\"font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue','PingFang SC',"
    "'Microsoft YaHei',sans-serif;max-width:100%;box-sizing:border-box;\">"
)
out = (WRAP_OPEN + body + ref + "</section>").replace("\u00a0", "&nbsp;")
open(f"{BASE}/article.html", "w", encoding="utf-8").write(out)
open(f"{BASE}/article_zh.html", "w", encoding="utf-8").write(out)

cnt = lambda p: len(re.findall(p, out))
print(
    "len", len(out), "h1", cnt("<h1"), "h2", cnt("<h2"), "h3", cnt("<h3"), "img", cnt("<img"),
    "pre", cnt("<pre"), "table", cnt("<table"), "figure", cnt("<figure"),
    "cjk", cnt(r"[\u4e00-\u9fff]"),
)
print("code底纹", out.count("#f3f4f5"), "token色", out.count("color:#"), "nbsp", out.count("&nbsp;"))
print("html泄露", cnt(r"<html"), cnt(r"<body"), cnt(r"<head"), "a标签", cnt(r"<a "))
print("破折号", out.count("——"), out.count("—"), "latex残留", cnt(r"\\\(|\\frac|\\mathbb"))

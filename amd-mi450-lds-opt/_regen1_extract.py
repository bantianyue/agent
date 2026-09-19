# -*- coding: utf-8 -*-
"""再生-1：从原始 HTML 提取块级元素（文档序），保护 code/变量高亮，导出待译清单。"""
import re, json
from bs4 import BeautifulSoup

BASE = r"D:/06_Hermes/articles/amd-mi450-lds-opt"
src = open(f"{BASE}/raw.html", encoding="utf-8").read()
soup = BeautifulSoup(src, "html.parser")
art = soup.find("article")
assert art is not None, "no <article>"

# 清理非正文
for sel in ["script", "style", "input", "a.headerlink", ".onlyprint", ".headerlink"]:
    for el in art.select(sel):
        el.decompose()

# 外链 -> 纯文本（微信不认外链），保留图片链接不动
for a in list(art.find_all("a")):
    if a.find("img"):
        continue
    a.unwrap()

# 评估：页面 meta 垃圾段（顶部 Login/作者/语言等）先记录数量，稍后人工核对
TAGS = ["h1", "h2", "h3", "h4", "h5", "p", "li", "dd", "dt", "td", "th", "figcaption"]
PH_RE = re.compile(
    r"<code[^>]*>.*?</code>|<span class=\"pre\"[^>]*>.*?</span>"
    r"|<(em|i|strong|b|sup|sub)[^>]*>.*?</\1>",
    re.S,
)


def protect(raw):
    phmap = {}

    def _r(m):
        k = f"？{len(phmap)}？"
        phmap[k] = m.group(0)
        return k

    return PH_RE.sub(_r, raw), phmap


blocks = []
for i, el in enumerate(art.find_all(TAGS)):
    if el.find_parent("pre"):
        continue
    raw = str(el)
    protected, phmap = protect(raw)
    txt = BeautifulSoup(protected, "html.parser").get_text()
    txt = re.sub(r"\s+", " ", txt).strip()
    blocks.append(
        {
            "i": i,
            "tag": el.name,
            "raw": raw,
            "protected": protected,
            "txt": txt,
            "ph": phmap,
        }
    )

open(f"{BASE}/_regen_art.html", "w", encoding="utf-8").write(str(art))
json.dump(blocks, open(f"{BASE}/_regen_blocks.json", "w", encoding="utf-8"), ensure_ascii=False)

total_chars = sum(len(b["txt"]) for b in blocks)
skip = [b for b in blocks if not re.search(r"[A-Za-z]{2,}", re.sub(r"？\d+？", "", b["txt"]))]
print(f"blocks={len(blocks)} chars={total_chars} skip_candidates={len(skip)}")
for b in skip:
    print("  SKIP", b["i"], b["tag"], repr(b["txt"][:80]))
print("pre:", str(art).count("<pre"), "img:", str(art).count("<img"),
      "table:", str(art).count("<table"), "f3f4f5:", str(art).count("#f3f4f5"))
print("math spans:", str(art).count('class="math'), "mathbb:", str(art).count("\\mathbb"))

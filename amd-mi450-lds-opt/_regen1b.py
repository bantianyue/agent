# -*- coding: utf-8 -*-
"""再生-1：从原始 HTML 提取块级元素（最外层、文档序），保护 code/变量高亮/数学，导出待译清单。"""
import re, json
from bs4 import BeautifulSoup

BASE = r"D:/06_Hermes/articles/amd-mi450-lds-opt"
TAGS = ["h1", "h2", "h3", "h4", "h5", "p", "li", "dd", "dt", "td", "th", "figcaption"]

LATEX_MAP = [
    (r"\\mathbb\{F\}_2", "F₂"),
    (r"\\mathbb\{E\}", "E"),
    (r"\\mathcal\{L\}", "ℒ"),
    (r"\\mathbin\{/_\{?\\ell\}?\}", "/ℓ"),
    (r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"(\1)/(\2)"),
    (r"\\propto", "∝"),
    (r"\\nabla", "∇"),
    (r"\\sim", "∼"),
    (r"\\mid", "|"),
    (r"\\ldots", "…"),
    (r"\\\\", "; "),
    (r"&", " "),
]


def latex_to_unicode(s: str) -> str:
    s = s.strip()
    s = re.sub(r"^\\\(|\\\)$", "", s).strip()
    s = re.sub(r"^\$|\$$", "", s).strip()
    s = re.sub(r"\\begin\{bmatrix\}(.*?)\\end\{bmatrix\}", r"[\1]", s, flags=re.S)
    for a, b in LATEX_MAP:
        s = re.sub(a, b, s)
    s = re.sub(r"\\+([{}])", r"\1", s)
    return re.sub(r"\s+", " ", s).strip()


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


src = open(f"{BASE}/raw.html", encoding="utf-8").read()
soup = BeautifulSoup(src, "html.parser")
art = soup.find("article")
assert art is not None, "no <article>"

for sel in ["script", "style", "input", "a.headerlink", ".onlyprint", ".headerlink"]:
    for el in art.select(sel):
        el.decompose()


def _math_repl(m):
    return f'<span class="mathreg">{latex_to_unicode(m.group(1))}</span>'


raw_art = re.sub(
    r'<span class="math[^"]*"[^>]*>(.*?)</span>', _math_repl, str(art), flags=re.S
)
art = BeautifulSoup(raw_art, "html.parser").find("article")

# 外链 -> 纯文本（微信不认外链），图片链接不动
for a in list(art.find_all("a")):
    if a.find("img"):
        continue
    a.unwrap()

PH_RE = re.compile(
    r"<code[^>]*>.*?</code>|<span class=\"pre\"[^>]*>.*?</span>"
    r"|<span class=\"mathreg\"[^>]*>.*?</span>"
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
for i, el in enumerate(collect(art)):
    raw = str(el)
    protected, phmap = protect(raw)
    txt = BeautifulSoup(protected, "html.parser").get_text()
    txt = re.sub(r"\s+", " ", txt).strip()
    if not txt:
        continue
    blocks.append({"i": i, "tag": el.name, "protected": protected, "txt": txt, "ph": phmap})

open(f"{BASE}/_regen_art.html", "w", encoding="utf-8").write(str(art))
json.dump(blocks, open(f"{BASE}/_regen_blocks.json", "w", encoding="utf-8"), ensure_ascii=False)

skip = [b for b in blocks if not re.search(r"[A-Za-z]{2,}", re.sub(r"？\d+？", "", b["txt"]))]
print(f"blocks={len(blocks)} chars={sum(len(b['txt']) for b in blocks)} skip={len(skip)}")
a = str(art)
print("pre:", a.count("<pre"), "img:", a.count("<img"), "table:", a.count("<table"),
      "figcaption:", a.count("<figcaption"))
print("残留 latex:", len(re.findall(r"\\\(|\\mathbb|\\frac", a)), "mathreg:", a.count("mathreg"))
print("skip:", [(b["i"], b["tag"], b["txt"][:18]) for b in skip[:10]])

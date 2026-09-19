# -*- coding: utf-8 -*-
"""再生-1b：在 _regen1b 基础上补块级公式（<div class="math">\[...\]</div>）转 Unicode/中文。"""
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

# 块级公式里的 \text{...} 词条（两处，人工定稿）
TEXT_MAP = {
    r"\text{TDM instructions}": "TDM 指令数",
    r"\text{number of pieces}": "片数",
    r"\text{number of warps}": "warp 数",
    r"\text{cycles}": "cycles",
    r"\text{fixed}": "fixed",
    r"\text{bytes}": "bytes",
    r"\text{rate}": "rate",
}


def latex_to_unicode(s: str, text_map=False) -> str:
    s = s.strip()
    s = re.sub(r"^\\\(|\\\)$|^\\\[|\\\]$", "", s).strip()
    s = re.sub(r"^\$|\$$", "", s).strip()
    s = re.sub(r"\\begin\{bmatrix\}(.*?)\\end\{bmatrix\}", r"[\1]", s, flags=re.S)
    if text_map:
        for k, v in TEXT_MAP.items():
            s = s.replace(k, v)
        s = s.replace(r"\left\lceil", "⌈").replace(r"\right\rceil", "⌉")
        s = s.replace(r"\left", "").replace(r"\right", "")
        s = re.sub(r"\\text\{([^{}]*)\}", r"\1", s)
        s = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"\1 / \2", s)
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

# 1) 块级公式 div -> 纯文本 <p class="mathblock">
def _block_math(m):
    val = latex_to_unicode(m.group(1), text_map=True)
    return f'<p class="mathblock">{val}</p>'


art_html = re.sub(
    r'<div class="math[^"]*"[^>]*>\s*\\\[(.*?)\\\]\s*</div>', _block_math, str(art), flags=re.S
)

# 2) 行内数学 span -> Unicode，保护成占位符
def _inline_math(m):
    return f'<span class="mathreg">{latex_to_unicode(m.group(1))}</span>'


art_html = re.sub(
    r'<span class="math[^"]*"[^>]*>(.*?)</span>', _inline_math, art_html, flags=re.S
)
art = BeautifulSoup(art_html, "html.parser").find("article")

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
      "figcaption:", a.count("<figcaption"), "mathblock:", a.count("mathblock"))
print("残留 latex:", len(re.findall(r"\\\(|\\\[|\\mathbb|\\frac", a)))
print("块级公式:", [b["txt"] for b in blocks if b["tag"] == "p" and "cycles = " in b["txt"] or b["tag"] == "p" and "TDM 指令数" in b["txt"]])

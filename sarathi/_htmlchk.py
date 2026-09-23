# -*- coding: utf-8 -*-
import re, os

ART = r"D:\06_Hermes\articles\sarathi"
html = open(os.path.join(ART, "article.html"), encoding="utf-8").read()

imgs = re.findall(r'<img[^>]*src="([^"]+)"', html)
figs = [s for s in imgs if "fig" in s.lower()]
others = [s for s in imgs if s not in figs]
missing = [s for s in imgs if not s.startswith("http") and not os.path.exists(os.path.join(ART, s))]

info = []
info.append("total <img> = %d" % len(imgs))
info.append("fig images  = %d" % len(figs))
info.append("uniq fig    = %d" % len(set(figs)))
info.append("other imgs  = %s" % others)
info.append("missing     = %s" % missing)
info.append("WECHATIMGPH_ = %d" % html.count("WECHATIMGPH_"))
info.append("PORTAL links = %d" % len(re.findall(r'mp\.weixin\.qq\.com/s/', html)))
info.append("h2 = %d  h3 = %d" % (html.count("<h2"), html.count("<h3")))
info.append("table = %d" % html.count("<table"))
info.append("figure/figcaption = %d / %d" % (html.count("<figure"), html.count("<figcaption")))
info.append("html bytes = %d" % len(html))
open(os.path.join(ART, "_htmlchk.txt"), "w", encoding="utf-8").write("\n".join(info))
print("\n".join(info))

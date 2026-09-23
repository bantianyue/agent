# -*- coding: utf-8 -*-
import re, os

ART = r"D:\06_Hermes\articles\sarathi"
html = open(os.path.join(ART, "_draft_raw.html"), encoding="utf-8").read()
src = open(os.path.join(ART, "article.html"), encoding="utf-8").read()

out = []
out.append("draft len=%d  src len=%d" % (len(html), len(src)))
out.append("draft: img=%d  h2=%d h3=%d table=%d figure=%d"
           % (len(re.findall(r"<img", html)), len(re.findall(r"<h2", html)),
              len(re.findall(r"<h3", html)), len(re.findall(r"<table", html)),
              len(re.findall(r"<figure", html))))
out.append("draft: strong=%d em=%d ul=%d li=%d blockquote=%d" % (
    len(re.findall(r"<strong", html)), len(re.findall(r"<em", html)),
    len(re.findall(r"<ul", html)), len(re.findall(r"<li", html)),
    len(re.findall(r"<blockquote", html))))
out.append("draft: portal-a=%d  参考=%s" % (
    len(re.findall(r"mp\.weixin\.qq\.com/s\?", html)), "参考：" in html))
# 检查残留标记
for tok in ["*", "**", "```", "WECHATIMGPH", "fig0", "fig1", "fig2", "undefined", "None"]:
    c = html.count(tok)
    if c:
        out.append("RESIDUE %-12s = %d" % (tok, c))
# 正文段落数
out.append("draft <p =%d" % len(re.findall(r"<p ", html)))
open(os.path.join(ART, "_draftchk.txt"), "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))

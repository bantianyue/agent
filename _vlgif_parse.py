# -*- coding: utf-8 -*-
"""One-off: flatten the dumped X Article HTML into an ordered text + media list."""
import re, sys, html

sys.stdout.reconfigure(encoding="utf-8")
h = open(r"D:/06_Hermes/articles/_vlgif_article.html", encoding="utf-8").read()


def _src(m):
    s = re.search(r'src="([^"]+)"', m.group(0))
    if not s:
        return " @@IMG:?@@ "
    key = s.group(1).split("/")[-1].split("?")[0]
    return " @@IMG:%s@@ " % key


h = re.sub(r"<img[^>]*>", _src, h)
print("DEBUG raw img matches:", len(re.findall(r"<img[^>]*>", open(r"D:/06_Hermes/articles/_vlgif_article.html", encoding="utf-8").read())))
print("DEBUG marker count after sub:", h.count("IMG"))
h = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", h, flags=re.S)
h = re.sub(r"</(p|div|li|h1|h2|h3|h4|figure|blockquote)>", "\n", h)
h = re.sub(r"<[^>]+>", "", h)
h = html.unescape(h)
lines = [l.strip() for l in h.split("\n")]
lines = [l for l in lines if l]
out = "\n".join(lines)
open(r"D:/06_Hermes/articles/_vlgif_article.txt", "w", encoding="utf-8").write(out)
print(out[:7000])

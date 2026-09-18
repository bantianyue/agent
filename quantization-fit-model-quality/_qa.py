import re
import sys

h = open("article.html", encoding="utf-8").read()
print("html len", len(h))
print("img", len(re.findall(r"<img", h)))
print("figcaption", h.count("<figcaption"))
print("h2", h.count("<h2"))
print("h3", h.count("<h3"))
print("strong", h.count("<strong"))
print("portal", h.count("portal-title"), h.count("portal-links"))
print("srcs", re.findall(r'src="([^"]+)"', h))
zh = len(re.findall(r"[\u4e00-\u9fa5]", h))
en = len(re.findall(r"[A-Za-z]", h))
print("zh", zh, "en", en)

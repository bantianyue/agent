import re

h = open("article.html", encoding="utf-8").read()
i = h.find('<span class="portal-title"')
seg = h[i - 400:i + 2000]
seg = re.sub(r"\s+", " ", seg)
print(seg)
print("=== order check ===")
print("conclusion idx", h.find("结语"))
print("portal idx", i)
print("reference idx", h.find("参考："))

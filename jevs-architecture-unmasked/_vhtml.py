# -*- coding: utf-8 -*-
h = open("article.html", encoding="utf-8").read()
out = []
out.append("pre=%d img=%d table=%d strong=%d h2=%d" % (h.count("<pre"), h.count("<img"), h.count("<table"), h.count("<strong>"), h.count("<h2")))
out.append("gif_in=%s" % ("fig01.gif" in h))
out.append("portal=%d" % h.count("portal-title"))
out.append("markdown_hash=%d" % h.count("## "))
out.append("single_star=%d" % h.count("*"))
open("_vhtml.txt", "w", encoding="utf-8").write("\n".join(out))

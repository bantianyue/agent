# -*- coding: utf-8 -*-
import os, sys, re, json, requests

sys.path.insert(0, r"C:\Users\twfehh7\.workbuddy\skills\wechat-article-sop\scripts")
from importlib import import_module
m = import_module("verify-draft-images")

media_id = sys.argv[1]
appid, secret = m.get_credential()
tok = requests.get("https://api.weixin.qq.com/cgi-bin/token",
                   params={"grant_type": "client_credential", "appid": appid, "secret": secret}).json()["access_token"]
d = requests.post("https://api.weixin.qq.com/cgi-bin/draft/get",
                  params={"access_token": tok}, json={"media_id": media_id}).json()
it = d["news_item"][0]
html = it["content"]
html = html.encode("latin-1", errors="ignore").decode("utf-8", errors="ignore")

out = []
out.append("TITLE      = %s" % it.get("title"))
out.append("DIGEST     = %s" % (it.get("digest") or "")[:60])
out.append("AUTHOR     = %s" % it.get("author"))
out.append("mmbiz imgs = %d" % html.count("mmbiz.qpic.cn"))
out.append("IMGPH_     = %d" % html.count("WECHATIMGPH_"))
out.append("portal     = %d" % len(re.findall(r"mp\.weixin\.qq\.com/s/", html)))
out.append("h2/h3      = %d / %d" % (len(re.findall(r"<h2", html)), len(re.findall(r"<h3", html))))
out.append("table      = %d" % len(re.findall(r"<table", html)))
out.append("html len   = %d" % len(html))
open(r"D:\06_Hermes\articles\sarathi\_verify2.txt", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))

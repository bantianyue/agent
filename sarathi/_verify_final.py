# -*- coding: utf-8 -*-
import sys, re, requests
sys.path.insert(0, r"C:\Users\twfehh7\.workbuddy\skills\wechat-article-sop\scripts")
from importlib import import_module
m = import_module("verify-draft-images")

media_id = open(r"D:\06_Hermes\articles\sarathi\draft.id", encoding="utf-8").read().strip()
appid, secret = m.get_credential()
tok = requests.get("https://api.weixin.qq.com/cgi-bin/token",
                   params={"grant_type": "client_credential", "appid": appid, "secret": secret}).json()["access_token"]
d = requests.post("https://api.weixin.qq.com/cgi-bin/draft/get",
                  params={"access_token": tok}, json={"media_id": media_id}).json()
it = d["news_item"][0]
html = it["content"]
open(r"D:\06_Hermes\articles\sarathi\_draft_raw.html", "w", encoding="utf-8").write(html)

out = []
out.append("media_id    = %s" % media_id)
out.append("mmbiz imgs  = %d" % html.count("mmbiz.qpic.cn"))
out.append("IMGPH_      = %d" % html.count("WECHATIMGPH_"))
out.append("portal-a    = %d" % len(re.findall(r"mp\.weixin\.qq\.com/s\?", html)))
out.append("strong      = %d" % len(re.findall(r"<strong", html)))
out.append("bold-span   = %d" % html.count("font-weight:bold"))
out.append("h2/h3       = %d / %d" % (len(re.findall(r"<h2", html)), len(re.findall(r"<h3", html))))
out.append("table       = %d" % len(re.findall(r"<table", html)))
out.append("figure      = %d" % len(re.findall(r"<figure", html)))
out.append("参考         = %s" % ("参考：" in html))
open(r"D:\06_Hermes\articles\sarathi\_verify_final.txt", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))

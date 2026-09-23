# -*- coding: utf-8 -*-
import sys, re, requests
sys.path.insert(0, r"C:\Users\twfehh7\.workbuddy\skills\wechat-article-sop\scripts")
from importlib import import_module
m = import_module("verify-draft-images")

media_id = sys.argv[1]
appid, secret = m.get_credential()
tok = requests.get("https://api.weixin.qq.com/cgi-bin/token",
                   params={"grant_type": "client_credential", "appid": appid, "secret": secret}).json()["access_token"]
r = requests.post("https://api.weixin.qq.com/cgi-bin/draft/get",
                  params={"access_token": tok}, json={"media_id": media_id})
r.encoding = "utf-8"
d = r.json()
it = d["news_item"][0]
html = it["content"]
open(r"D:\06_Hermes\articles\sarathi\_draft_raw.html", "w", encoding="utf-8").write(html)
out = []
out.append("== DRAFT TAIL (last 3000 chars) ==")
open(r"D:\06_Hermes\articles\sarathi\_draft_tail.txt", "w", encoding="utf-8").write("\n".join(out) + "\n" + html[-3000:])
print("written, len=%d" % len(html))

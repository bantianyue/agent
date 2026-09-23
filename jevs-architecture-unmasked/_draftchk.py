# -*- coding: utf-8 -*-
import os, json, re, urllib.request

env = {}
for line in open(os.path.expanduser("~/.baoyu-skills/.env"), encoding="utf-8"):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip().strip('"').strip("'")
appid = env.get("WECHAT_APP_ID")
secret = env.get("WECHAT_APP_SECRET")

op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}))
tok = json.load(op.open("https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s" % (appid, secret), timeout=30))["access_token"]
mid = "TIqnnVEu6Oy3-wtKttGa0axBKRM8W-1Rzgc_T5Dv6QABNJf3UuQKKBG9KrsDz1HJ"
req = urllib.request.Request("https://api.weixin.qq.com/cgi-bin/draft/get?access_token=" + tok,
                             data=json.dumps({"media_id": mid}).encode())
d = json.load(op.open(req, timeout=30))
items = d.get("item", [])
if items and "news_item" in items[0]:
    content = items[0]["news_item"][0].get("content", "")
elif "news_item" in d:
    content = d["news_item"][0].get("content", "")
elif items and "articles" in items[0]:
    content = items[0]["articles"][0].get("content", "")
elif items:
    content = items[0].get("content", {}).get("html", "") if isinstance(items[0].get("content"), dict) else items[0].get("content", "")
else:
    content = ""
open("_draft.html", "w", encoding="utf-8").write(content)
out = []
out.append("errcode=%s itemtype=%s title=%s" % (d.get("errcode"), type(items[0]).__name__ if items else "-",
          (items[0].get("articles", [{}])[0].get("title", "?")[:40] if items and "articles" in items[0] else "?")))
out.append("img=%d gif=%d placeholder=%d" % (content.count("<img"), content.count("sz_mmbiz_gif"),
          len(re.findall(r'placeholder|待插图', content))))
out.append("strong=%d pre=%d br=%d" % (content.count("<strong"), content.count("<pre"), content.count("<br")))
out.append("portal=%d hr=%d" % (content.count("portal-title"), content.count("<hr")))
# order check: last occurrences
i_concl = content.find("结语")
i_portal = content.find("portal-title")
i_ref = content.find("参考：")
out.append("pos 结语=%d 传送门=%d 参考=%d" % (i_concl, i_portal, i_ref))
txt = re.sub(r"<[^>]+>", "", content)
txt = re.sub(r"\s+", "", txt)
out.append("textlen=%d" % len(txt))
for key in ["决策不必先变成文本", " causal transformer", "排列测试", "要点速览", "Jev"]:
    out.append("has[%s]=%s" % (key[:16], key.replace(" ", "") in txt.replace(" ", "")))
open("_draftchk.txt", "w", encoding="utf-8").write("\n".join(out))

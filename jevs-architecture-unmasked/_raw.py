# -*- coding: utf-8 -*-
import os, json, urllib.request
env = {}
for line in open(os.path.expanduser("~/.baoyu-skills/.env"), encoding="utf-8"):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip()
op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}))
tok = json.load(op.open("https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s" % (env["WECHAT_APP_ID"], env["WECHAT_APP_SECRET"]), timeout=30))
open("_tok.txt", "w", encoding="utf-8").write(json.dumps({k: (v[:6] + "..." if isinstance(v, str) and len(v) > 12 else v) for k, v in tok.items()}))
if "access_token" not in tok:
    open("_raw.txt", "w", encoding="utf-8").write("no token: " + json.dumps(tok))
    raise SystemExit
mid = "TIqnnVEu6Oy3-wtKttGa0axBKRM8W-1Rzgc_T5Dv6QABNJf3UuQKKBG9KrsDz1HJ"
req = urllib.request.Request("https://api.weixin.qq.com/cgi-bin/draft/get?access_token=" + tok["access_token"],
                             data=json.dumps({"media_id": mid}).encode())
raw = op.open(req, timeout=30).read()
open("_raw.txt", "wb").write(raw[:800])

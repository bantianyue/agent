import json
import os
import re

import requests

env_path = os.path.expanduser("~/.baoyu-skills/.env")
appid = secret = None
for line in open(env_path):
    line = line.strip()
    if line.startswith("WECHAT_APP_ID="):
        appid = line.split("=", 1)[1]
    elif line.startswith("WECHAT_APP_SECRET="):
        secret = line.split("=", 1)[1]

proxies = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
tok = requests.get("https://api.weixin.qq.com/cgi-bin/token",
                   params={"grant_type": "client_credential", "appid": appid, "secret": secret},
                   proxies=proxies, timeout=30).json()["access_token"]
mid = open('draft.id', encoding='utf-8').read().strip()
d = requests.post("https://api.weixin.qq.com/cgi-bin/draft/get",
                  params={"access_token": tok}, json={"media_id": mid},
                  proxies=proxies, timeout=60).json()
item = d["news_item"][0]
html = item["content"].encode("latin-1", errors="ignore").decode("utf-8")
print('title:', item.get("title"))
print('mmbiz imgs:', html.count("mmbiz.qpic.cn"))
print('WECHATIMGPH_:', html.count("WECHATIMGPH_"))
print('preview-table:', html.count("preview-table"))
print('pre:', html.count("<pre"))
print('strong:', html.count("<strong"))
print('h2 pill:', html.count('data-heading'))
print('portal links:', html.count("mp.weixin.qq.com/s/"))
print('---- img srcs ----')
for m in re.finditer(r'<img[^>]*src="([^"]+)"', html):
    print(m.group(1)[:110])

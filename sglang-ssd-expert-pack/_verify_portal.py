import os

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
html = d["news_item"][0]["content"].encode("latin-1", errors="ignore").decode("utf-8")
open('_draft_content.html', 'w', encoding='utf-8').write(html)
print('len', len(html))
for kw in ['portal', '传送门', 'mp.weixin', '参考', 'href', '结语']:
    print(kw, html.count(kw))
i = html.find('传送门')
print(repr(html[max(0, i - 300):i + 500]) if i >= 0 else 'no 传送门')
i2 = html.find('参考')
print(repr(html[i2 - 200:i2 + 300]) if i2 >= 0 else 'no 参考')

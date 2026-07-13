import json, urllib.request, urllib.parse, os, sys

ENV = os.path.expanduser("~/.baoyu-skills/.env")
cfg = {}
for line in open(ENV, encoding="utf-8"):
    line = line.strip()
    if line and "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        cfg[k.strip()] = v.strip()

APPID = cfg["WECHAT_APP_ID"]
SECRET = cfg["WECHAT_APP_SECRET"]
DRAFT_MEDIA_ID = sys.argv[1] if len(sys.argv) > 1 else "TIqnnVEu6Oy3-wtKttGa0X6WDUYbwFQFt6dE3uqE9GVd40FIxvWah9N9D7aznCOD"

def get_token():
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={SECRET}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())["access_token"]

def draft_get(token, media_id):
    url = f"https://api.weixin.qq.com/cgi-bin/draft/get?access_token={token}"
    body = json.dumps({"media_id": media_id}).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

token = get_token()
print("token OK, len:", len(token))
data = draft_get(token, DRAFT_MEDIA_ID)
news = data.get("news_item", [{}])[0]
content = news.get("content", "")
title = news.get("title", "")
print("TITLE:", title)
print("CONTENT chars:", len(content))
# count images
import re
imgs = re.findall(r'<img[^>]+src="([^"]+)"', content)
print("IMG count in content:", len(imgs))
for i, u in enumerate(imgs, 1):
    print(f"  [{i}] {u[:80]}")
# save html for preview
open("draft_preview.html", "w", encoding="utf-8").write(content)
print("saved draft_preview.html")

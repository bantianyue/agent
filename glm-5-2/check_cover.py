import os, json, urllib.request

env_path = os.path.expanduser("~/.baoyu-skills/.env")
with open(env_path) as f:
    content = f.read()

appid = None
secret = None
sq = "'" + '"'
for line in content.split("\n"):
    line = line.strip()
    if line.startswith("WECHAT_APP_ID="):
        appid = line.split("=", 1)[1].strip().strip(sq)
    if "WECHAT_APP_SECRET" in line:
        secret = line.split("=", 1)[1].strip().strip(sq)

url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=" + appid + "&secret=" + secret
req = urllib.request.Request(url)
with urllib.request.urlopen(req, timeout=10) as resp:
    data = json.loads(resp.read())
token = data["access_token"]

draft_id = "TIqnnVEu6Oy3-wtKttGa0WgBWNiC3TVyXM37wHAH3C9AzmRUqYb5lYk7Gdah2LOb"
get_url = "https://api.weixin.qq.com/cgi-bin/draft/get?access_token=" + token
get_body = json.dumps({"media_id": draft_id}).encode()
req = urllib.request.Request(get_url, data=get_body, method="POST")
req.add_header("Content-Type", "application/json")
with urllib.request.urlopen(req, timeout=10) as resp:
    draft = json.loads(resp.read())

item = draft["news_item"][0]
print("Title:", item["title"])
print("Thumb media_id:", item.get("thumb_media_id", "N/A"))

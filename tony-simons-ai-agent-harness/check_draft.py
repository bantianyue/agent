import os, re, json, urllib.request

env_path = os.path.expanduser("~/.baoyu-skills/.env")
appid = None
secret = None
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line.startswith("WECHAT_APP_ID="):
            appid = line.split("=", 1)[1].strip().strip("'").strip('"')
        if line.startswith("WECHAT_APP_SECRET="):
            secret = line.split("=", 1)[1].strip().strip("'").strip('"')

url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=" + appid + "&secret=" + secret
req = urllib.request.Request(url)
with urllib.request.urlopen(req, timeout=10) as resp:
    data = json.loads(resp.read())
token = data["access_token"]

draft_id = "TIqnnVEu6Oy3-wtKttGa0e8WwBu6Tp-_7D7G5S3ZpYogWtKTJVedBOJZqf1lDzRT"
get_url = "https://api.weixin.qq.com/cgi-bin/draft/get?access_token=" + token
get_body = json.dumps({"media_id": draft_id}).encode()
req = urllib.request.Request(get_url, data=get_body, method="POST")
req.add_header("Content-Type", "application/json")
with urllib.request.urlopen(req, timeout=10) as resp:
    draft = json.loads(resp.read())

item = draft["news_item"][0]
content_html = item["content"]
placeholders = re.findall(r"WECHATIMGPH_\d+", content_html)
print("Placeholders:", placeholders)

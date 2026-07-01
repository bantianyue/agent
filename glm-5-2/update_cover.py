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

# Get token
url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=" + appid + "&secret=" + secret
req = urllib.request.Request(url)
with urllib.request.urlopen(req, timeout=10) as resp:
    data = json.loads(resp.read())
token = data["access_token"]
print("Token obtained")

# Upload cover image as permanent material
import io
img_path = "D:/06_Hermes/articles/glm-5-2/cover.png"
with open(img_path, "rb") as f:
    img_data = f.read()

boundary = "----WebKitFormBoundary" + os.urandom(16).hex()
parts = []
parts.append("--" + boundary)
parts.append('Content-Disposition: form-data; name="media"; filename="cover.png"')
parts.append("Content-Type: image/png")
parts.append("")
parts.append(img_data.decode("latin-1"))
parts.append("--" + boundary + "--")
body = "\r\n".join(parts).encode("latin-1")

upload_url = "https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=" + token + "&type=image"
req = urllib.request.Request(upload_url, data=body, method="POST")
req.add_header("Content-Type", "multipart/form-data; boundary=" + boundary)
with urllib.request.urlopen(req, timeout=30) as resp:
    upload_result = json.loads(resp.read())

cover_media_id = upload_result["media_id"]
print("Cover uploaded, media_id:", cover_media_id[:30] + "...")

# Update draft with new cover
draft_id = "TIqnnVEu6Oy3-wtKttGa0WgBWNiC3TVyXM37wHAH3C9AzmRUqYb5lYk7Gdah2LOb"

# First get existing draft
get_url = "https://api.weixin.qq.com/cgi-bin/draft/get?access_token=" + token
get_body = json.dumps({"media_id": draft_id}).encode()
req = urllib.request.Request(get_url, data=get_body, method="POST")
req.add_header("Content-Type", "application/json")
with urllib.request.urlopen(req, timeout=10) as resp:
    draft = json.loads(resp.read())

item = draft["news_item"][0]
item["thumb_media_id"] = cover_media_id

# Update draft
update_payload = {
    "media_id": draft_id,
    "index": 0,
    "articles": item
}
update_url = "https://api.weixin.qq.com/cgi-bin/draft/update?access_token=" + token
update_body = json.dumps(update_payload, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(update_url, data=update_body, method="POST")
req.add_header("Content-Type", "application/json; charset=utf-8")
with urllib.request.urlopen(req, timeout=10) as resp:
    update_result = json.loads(resp.read())

print("Update result:", update_result)

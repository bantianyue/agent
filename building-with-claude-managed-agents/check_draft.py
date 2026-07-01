import json, urllib.request, os, re

env_path = os.path.expanduser("~/.baoyu-skills/.env")
appid = secret = None
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line.startswith("WECHAT_APP_ID="):
            appid = line.split("=", 1)[1].strip().strip('"').strip("'")
        elif line.startswith("WECHAT_APP_SECRET="):
            secret = line.split("=", 1)[1].strip().strip('"').strip("'")

print(f"AppID: {appid[:4] if appid else 'NONE'}...")

token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}"
resp = urllib.request.urlopen(token_url)
data = json.loads(resp.read())
token = data.get("access_token")
print(f"Token: {token[:10] if token else 'NONE'}...")

if not token:
    print("FAILED:", data)
    exit(1)

media_id = "TIqnnVEu6Oy3-wtKttGa0ZtpSa-TTBk9vASejQKO4zqpq-wuahbp10dmFnEoO1dD"
check_url = f"https://api.weixin.qq.com/cgi-bin/draft/get?access_token={token}"
body = json.dumps({"media_id": media_id}).encode()
req = urllib.request.Request(check_url, data=body, method="POST", headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req)
draft = json.loads(resp.read())

content = draft.get("news_item", [{}])[0].get("content", "")
placeholders = re.findall(r'WECHATIMGPH_\d+', content)
print(f"\nRemaining placeholders: {len(placeholders)}")
if placeholders:
    print("PLACEHOLDERS FOUND:", placeholders[:5])
else:
    print("No placeholders - body images uploaded successfully!")

imgs = re.findall(r'<img[^>]+src="([^"]+)"', content)
print(f"\nTotal images in draft body: {len(imgs)}")
for i, img in enumerate(imgs[:3]):
    print(f"  img {i+1}: {img[:80]}...")
if len(imgs) > 3:
    print(f"  ... and {len(imgs)-3} more")

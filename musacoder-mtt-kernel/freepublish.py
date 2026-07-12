import os, re, json, urllib.request

# 读 .env
envp = os.path.expanduser("~/.baoyu-skills/.env")
vals = {}
for line in open(envp, encoding="utf-8"):
    line = line.strip()
    if not line or "=" not in line:
        continue
    k, v = line.split("=", 1)
    vals[k.strip()] = v.strip()

appid = vals.get("WECHAT_APP_ID")
secret = vals.get("WECHAT_APP_SECRET")
if not appid or not secret:
    print("ERR: missing creds"); raise SystemExit(1)

# 取 token
tok_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}"
def get(url, data=None):
    req = urllib.request.Request(url, data=data, headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

tok = get(tok_url)
print("token resp:", {k:v for k,v in tok.items() if k!="access_token"})
at = tok.get("access_token")
if not at:
    print("NO TOKEN"); raise SystemExit(1)

media_id = open("draft.id", encoding="utf-8").read().strip()
pub_url = f"https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token={at}"
body = json.dumps({"media_id": media_id}).encode("utf-8")
resp = get(pub_url, body)
print("submit resp:", json.dumps(resp, ensure_ascii=False))

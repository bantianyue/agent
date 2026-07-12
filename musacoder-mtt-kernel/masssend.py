import os, json, urllib.request

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

def get(url, data=None):
    req = urllib.request.Request(url, data=data, headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

tok = get(f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}")
at = tok.get("access_token")
if not at:
    print("NO TOKEN:", tok); raise SystemExit(1)

media_id = open("draft.id", encoding="utf-8").read().strip()
url = f"https://api.weixin.qq.com/cgi-bin/message/mass/sendall?access_token={at}"
body = json.dumps({
    "filter": {"is_to_all": True},
    "mpnews": {"media_id": media_id},
    "msgtype": "mpnews",
    "send_ignore_reprint": 0
}).encode("utf-8")
resp = get(url, body)
print("masssend resp:", json.dumps(resp, ensure_ascii=False))

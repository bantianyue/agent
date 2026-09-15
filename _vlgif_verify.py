# -*- coding: utf-8 -*-
"""One-off: draft/get the pushed draft and verify GIF vs static body images."""
import json
import os
import re
import sys
import urllib.request

import requests

sys.stdout.reconfigure(encoding="utf-8")

DIR = r"D:/06_Hermes/articles/vllm-agentx-agentic-serving"
media_id = open(os.path.join(DIR, "draft.id"), encoding="utf-8").read().strip()

env_path = os.path.expanduser("~/.baoyu-skills/.env")
appid = secret = None
for line in open(env_path, encoding="utf-8"):
    line = line.strip()
    if line.startswith("WECHAT_APP_ID="):
        appid = line.split("=", 1)[1]
    elif line.startswith("WECHAT_APP_SECRET="):
        secret = line.split("=", 1)[1]

tok = requests.get(
    "https://api.weixin.qq.com/cgi-bin/token",
    params={"grant_type": "client_credential", "appid": appid, "secret": secret},
    timeout=30,
).json()["access_token"]

r = requests.post(
    f"https://api.weixin.qq.com/cgi-bin/draft/get?access_token={tok}",
    data=json.dumps({"media_id": media_id}).encode(),
    headers={"Content-Type": "application/json"},
    timeout=30,
).json()

item = r["news_item"][0]
content = item["content"]
print("title:", item["title"])
print("thumb_media_id:", item.get("thumb_media_id"))

imgs = re.findall(r'<img[^>]*src="([^"]+)"', content)
print("body img count:", len(imgs))
gif = [u for u in imgs if "mmbiz_gif" in u]
png = [u for u in imgs if "mmbiz_gif" not in u]
print("mmbiz_gif:", len(gif), " other:", len(png))
for i, u in enumerate(imgs, 1):
    print(f"  {i:2d} {'GIF ' if 'mmbiz_gif' in u else 'IMG '} {u[:110]}")

# save the fetched content for further inspection
open(os.path.join(DIR, "_draft_get.html"), "w", encoding="utf-8").write(content)

# verify each GIF url really serves a GIF (animated) payload
for u in gif:
    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        head = resp.read(6)
    print("fetch", u[:80], "header=", head)

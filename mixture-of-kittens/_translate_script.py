#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, sys

sys.path.insert(0, "C:/Users/twfehh7/AppData/Local/hermes/skills/content-creation/wechat-article-sop/scripts")
import llm_utils

BASE = "D:/06_Hermes/articles/mixture-of-kittens"
items = json.load(open(BASE+"/_items.json", encoding="utf-8"))

# Translate queue: p/li/h1/h2/h3 (text), code (keep)
paras = []
for i,(k,v) in enumerate(items):
    if v is None:
        continue
    if k == "code":
        paras.append({"id": i, "type": "code", "content": v})
    elif k in ("p","li","h1","h2","h3"):
        paras.append({"id": i, "type": "text", "content": v})

def is_noise(s):
    # 标题里的 "# " 前缀、纯 citation 代码尾
    return s.startswith('@misc') or (len(s) < 12 and not s.strip())

print(f"Total to translate: {len(paras)}", flush=True)

all_results = {}
CHUNK = 32
# translate text items in chunks; code preserved
text_only = [p for p in paras if p["type"]=="text"]
code_map = {p["id"]: p["content"] for p in paras if p["type"]=="code"}
for p in code_map:
    all_results[p] = code_map[p]

for c in range(0, len(text_only), CHUNK):
    chunk = text_only[c:c+CHUNK]
    try:
        res = llm_utils.translate_batch(chunk, batch_size=8)
        for r in res:
            all_results[r["id"]] = r.get("content", "")
        print(f"  chunk {c//CHUNK+1} done ({len(res)})", flush=True)
    except Exception as e:
        print(f"  chunk {c//CHUNK+1} FAILED: {str(e)[:60]}", flush=True)
        for p in chunk:
            try:
                all_results[p["id"]] = llm_utils.translate(p["content"], stream=False)
            except Exception:
                all_results[p["id"]] = p["content"]
    with open(BASE+"/_translations.json","w",encoding="utf-8") as f:
        json.dump({str(k):v for k,v in all_results.items()}, f, ensure_ascii=False, indent=2)

print(f"\n=== COMPLETE: {len(all_results)} items ===", flush=True)

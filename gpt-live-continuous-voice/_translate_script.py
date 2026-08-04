#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, sys

sys.path.insert(0, "C:/Users/twfehh7/AppData/Local/hermes/skills/content-creation/wechat-article-sop/scripts")
import llm_utils

BASE = "D:/06_Hermes/articles/gpt-live-continuous-voice"
items = json.load(open(BASE+"/_items.json", encoding="utf-8"))

paras = [{"id": i, "type": "text", "content": v} for i,(k,v) in enumerate(items) if k in ("p","h1","h2","h3")]
print(f"Total paragraphs: {len(paras)}", flush=True)

all_results = {}
CHUNK = 32
for c in range(0, len(paras), CHUNK):
    chunk = paras[c:c+CHUNK]
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

print(f"\n=== COMPLETE: {len(all_results)}/{len(paras)} ===", flush=True)

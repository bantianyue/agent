#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 翻译 kimi-k3-day0-support 全部段落（100%保留原文），输出 json
import json, sys

sys.path.insert(0, "C:/Users/twfehh7/AppData/Local/hermes/skills/content-creation/wechat-article-sop/scripts")
import llm_utils

BASE = "D:/06_Hermes/articles/kimi-k3-day0-support"

with open(BASE+"/_extract_blocks.json", encoding="utf-8") as f:
    blocks = json.load(f)

# Build ordered items with global ids: ("h1"|"h2"|"p"|"li"|"figure"|"imgsrc", content)
items = []
for kind, content in blocks:
    if kind in ("h1","h2"):
        items.append((kind, content))
    elif kind == "p":
        if str(content).strip().startswith("Image source"):
            items.append(("imgsrc", content))
        else:
            items.append(("p", content))
    elif kind == "li":
        items.append(("li", content))
    elif kind == "figure":
        items.append(("figure", content["src"]))

with open(BASE+"/_items.json","w",encoding="utf-8") as f:
    json.dump(items, f, ensure_ascii=False, indent=2)

# Prepare paragraphs for translate_batch: only p/li (text)
paras = []
item_to_para = {}
idx_map = {}
for i, (kind, content) in enumerate(items):
    if kind in ("p","li"):
        paras.append({"id": i, "type": "text", "content": content})

print(f"Total paragraphs to translate: {len(paras)}", flush=True)

# Split into chunks of 40 and translate via translate_batch (which batches internally at 8)
# translate_batch caches and handles the loop. Call it in slices to persist progress.
CHUNK = 32
all_results = {}
for c in range(0, len(paras), CHUNK):
    chunk = paras[c:c+CHUNK]
    try:
        res = llm_utils.translate_batch(chunk, batch_size=8)
        for r in res:
            all_results[r["id"]] = r.get("content", chunk[[p["id"] for p in chunk].index(r["id"])]["content"])
        print(f"  chunk {c//CHUNK+1} done ({len(res)} items)", flush=True)
    except Exception as e:
        print(f"  chunk {c//CHUNK+1} FAILED: {str(e)[:80]}", flush=True)
        for p in chunk:
            try:
                all_results[p["id"]] = llm_utils.translate(p["content"], stream=False)
            except Exception as e2:
                all_results[p["id"]] = p["content"]
        print(f"  chunk {c//CHUNK+1} fallback done", flush=True)
    json.dump({str(k):v for k,v in all_results.items()}, open(BASE+"/_translations.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
    if (c//CHUNK+1) % 2 == 0:
        print(f"  progress checkpoint: {len(all_results)}/{len(paras)}", flush=True)

print(f"\n=== TRANSLATION COMPLETE: {len(all_results)}/{len(paras)} ===", flush=True)
missing = [p["id"] for p in paras if p["id"] not in all_results]
if missing:
    print(f"MISSING ids: {missing}", flush=True)

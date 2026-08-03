#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 生成 kimi-k3-day0-support 的完整 build.py（100%保留原文）
import json, sys, os, time

sys.path.insert(0, "C:/Users/twfehh7/AppData/Local/hermes/skills/content-creation/wechat-article-sop/scripts")
import llm_utils

BASE = "D:/06_Hermes/articles/kimi-k3-day0-support"

# Load parsed blocks
with open(BASE+"/_extract_blocks.json", encoding="utf-8") as f:
    blocks = json.load(f)

# Load img mapping (source name -> figN)
with open(BASE+"/img_mapping.json", encoding="utf-8") as f:
    imgmap = json.load(f)

# Structure: iterate blocks, translate text blocks, keep figures with position
# Skip "Image source:" lines (they are attribution, redundant) - but keep them as invisible? User wants 100%. 
# We'll keep image source as part of figure caption instead of separate paragraph for cleanliness.
# But "100%保留原文" -> keep all content. Let's keep image source note as its own para after figure.

def is_image_source(text):
    return text.strip().startswith("Image source:")

# Build list: each item = ("h1"|"h2"|"p"|"li"|"figure", content)
items = []
for kind, content in blocks:
    if kind in ("h1","h2"):
        items.append((kind, content))
    elif kind == "p":
        if is_image_source(content):
            items.append(("imgsrc", content))  # keep for 100%, will attach to figure
        else:
            items.append(("p", content))
    elif kind == "li":
        items.append(("li", content))
    elif kind == "figure":
        items.append(("figure", content["src"]))

# Save items for the waiting process to consume
with open(BASE+"/_items.json","w",encoding="utf-8") as f:
    json.dump(items, f, ensure_ascii=False, indent=2)

# Translate all translatable text items
translations = {}
to_translate = [i for i, it in enumerate(items) if it[0] in ("p","li")]
print(f"Items to translate: {len(to_translate)} / total {len(items)}")

# Batch translate in groups of 8
BATCH = 8
for start in range(0, len(to_translate), BATCH):
    batch_idx = to_translate[start:start+BATCH]
    batch = [{"id": i, "text": items[i][1]} for i in batch_idx]
    try:
        res = llm_utils.translate_batch(batch, batch_size=len(batch))
        for r in res:
            translations[r["id"]] = r["translation"]
        print(f"  batch {start//BATCH+1}: done ({len(res)}/{len(batch)})", flush=True)
    except Exception as e:
        print(f"  batch {start//BATCH+1} FAILED: {str(e)[:80]}", flush=True)
        # fallback: single-item translate
        for b in batch:
            try:
                translations[b["id"]] = llm_utils.translate(b["text"], stream=False)
            except Exception as e2:
                translations[b["id"]] = b["text"]
        print(f"  batch {start//BATCH+1}: single-fallback done", flush=True)
    # persist progress
    with open(BASE+"/_translations.json","w",encoding="utf-8") as f:
        json.dump({str(k):v for k,v in translations.items()}, f, ensure_ascii=False, indent=2)

print(f"\n=== TRANSLATION COMPLETE: {len(translations)}/{len(to_translate)} ===")
missing = [i for i in to_translate if i not in translations]
if missing:
    print(f"MISSING: {missing}")

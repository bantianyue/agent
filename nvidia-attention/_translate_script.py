#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 翻译 nvidia-attention 全部正文段落（保留~80%，先全部翻译再在组装时删减）
import json, sys, os

sys.path.insert(0, "C:/Users/twfehh7/AppData/Local/hermes/skills/content-creation/wechat-article-sop/scripts")
import llm_utils

BASE = "D:/06_Hermes/articles/nvidia-attention"
blocks = json.load(open(BASE+"/blocks.json", encoding="utf-8"))

# Build items: translate p/li, keep headings (h2/h3) separately (translate them too in final)
items = [(kind, content) for kind, content in blocks if kind != "figure"]
# Exclude navigation tail: Acknowledgments/Tags/About
skip_titles = {"Acknowledgments", "Tags", "About the Authors"}
filtered = []
for kind, content in items:
    if kind in ("h2","h3") and content.strip() in skip_titles:
        continue
    filtered.append((kind, content))

# paragraphs to translate: p/li
paras = []
for i, (kind, content) in enumerate(filtered):
    if kind in ("p","li","h2","h3"):
        # headings also get translated for our build (short)
        paras.append({"id": i, "type": "text", "content": content})

print(f"Total paragraphs (incl headings): {len(paras)}", flush=True)

# Translate in chunks, persist progress
CHUNK = 32
all_results = {}
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
            except Exception as e2:
                all_results[p["id"]] = p["content"]
    with open(BASE+"/_translations.json","w",encoding="utf-8") as f:
        json.dump({str(k):v for k,v in all_results.items()}, f, ensure_ascii=False, indent=2)

print(f"\n=== TRANSLATION COMPLETE: {len(all_results)}/{len(paras)} ===", flush=True)

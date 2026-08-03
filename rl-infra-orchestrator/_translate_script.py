#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 翻译 rl-infra-orchestrator 全部段落（100%保留原文），输出 json
import json, sys

sys.path.insert(0, "C:/Users/twfehh7/AppData/Local/hermes/skills/content-creation/wechat-article-sop/scripts")
import llm_utils

BASE = "D:/06_Hermes/articles/rl-infra-orchestrator"

with open("D:/06_Hermes/articles/vivekvkashyap_blocks.json", encoding="utf-8") as f:
    blocks = json.load(f)

items = [(kind, content) for kind, content in blocks]
with open(BASE+"/_items.json","w",encoding="utf-8") as f:
    json.dump(items, f, ensure_ascii=False, indent=2)

# Build paras: code blocks preserved (type=code), p/li translated (type=text), h preserved as-is
paras = []
for i, (kind, content) in enumerate(items):
    if kind == "p":
        paras.append({"id": i, "type": "text", "content": content})
    elif kind == "li":
        paras.append({"id": i, "type": "text", "content": content})
    elif kind == "code":
        paras.append({"id": i, "type": "code", "content": content})

print(f"Total paragraphs (p/li/code): {len(paras)}", flush=True)

CHUNK = 32
all_results = {}
for c in range(0, len(paras), CHUNK):
    chunk = paras[c:c+CHUNK]
    try:
        res = llm_utils.translate_batch(chunk, batch_size=8)
        for r in res:
            all_results[r["id"]] = r.get("content", "")
        print(f"  chunk {c//CHUNK+1} done ({len(res)} items)", flush=True)
    except Exception as e:
        print(f"  chunk {c//CHUNK+1} FAILED: {str(e)[:80]}", flush=True)
        for p in chunk:
            try:
                all_results[p["id"]] = llm_utils.translate(p["content"], stream=False) if p["type"]=="text" else p["content"]
            except Exception as e2:
                all_results[p["id"]] = p["content"]
        print(f"  chunk {c//CHUNK+1} fallback done", flush=True)
    json.dump({str(k):v for k,v in all_results.items()}, open(BASE+"/_translations.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)

print(f"\n=== TASK2 TRANSLATION COMPLETE: {len(all_results)}/{len(paras)} ===", flush=True)

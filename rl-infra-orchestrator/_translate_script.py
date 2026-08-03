#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 生成 rl-infra-orchestrator 的翻译（100%保留原文，代码块不翻译）
import json, sys, os

sys.path.insert(0, "C:/Users/twfehh7/AppData/Local/hermes/skills/content-creation/wechat-article-sop/scripts")
import llm_utils

BASE = "D:/06_Hermes/articles/rl-infra-orchestrator"

with open(BASE+"/_items.json", encoding="utf-8") as f:
    items = json.load(f)

# Translate p/li only (code and h stay as-is; h will be translated separately later)
translations = {}
to_translate = [i for i, it in enumerate(items) if it[0] in ("p","li")]
print(f"Task2 items to translate: {len(to_translate)}", flush=True)

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
        print(f"  batch {start//BATCH+1} FAILED: {str(e)[:60]}", flush=True)
        for b in batch:
            try:
                translations[b["id"]] = llm_utils.translate(b["text"], stream=False)
            except Exception as e2:
                translations[b["id"]] = b["text"]
        print(f"  batch {start//BATCH+1}: fallback done", flush=True)
    with open(BASE+"/_translations.json","w",encoding="utf-8") as f:
        json.dump({str(k):v for k,v in translations.items()}, f, ensure_ascii=False, indent=2)

print(f"\n=== TASK2 TRANSLATION COMPLETE: {len(translations)}/{len(to_translate)} ===")

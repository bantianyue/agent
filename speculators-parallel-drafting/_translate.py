#!/usr/bin/env python3
"""临时翻译脚本：Speculators 博客 100% 保留模式全段翻译。落盘 _translations.json 检查点。"""
import json, sys, os

sys.path.insert(0, r"C:/Users/twfehh7/AppData/Local/hermes/skills/content-creation/wechat-article-sop/scripts")
from llm_utils import translate_batch

DIR = r"D:/06_Hermes/articles/speculators-parallel-drafting"
blocks = json.load(open(os.path.join(DIR, "_extract_blocks.json"), encoding="utf-8"))

# 待翻译：非 code 块（text + figure + title）。code 语法保留看原文无碍，且正文无代码表意需保留
to_translate = [b for b in blocks if b["type"] != "code"]
print(f"待翻译 {len(to_translate)} 块", flush=True)

# 分块翻译，每 chunk 落盘检查点
CHUNK = 32
all_done = {}
if os.path.exists(os.path.join(DIR, "_translations.json")):
    all_done = json.load(open(os.path.join(DIR, "_translations.json"), encoding="utf-8"))

todo = [b for b in to_translate if str(b["id"]) not in all_done]
for c in range(0, len(todo), CHUNK):
    chunk = todo[c:c+CHUNK]
    print(f"翻译 chunk {c//CHUNK + 1} ({len(chunk)} 块)...", flush=True)
    try:
        translated = translate_batch(chunk, batch_size=8)
        for t in translated:
            all_done[str(t["id"])] = t["content"]
    except Exception as e:
        print(f"chunk 失败: {e}，逐段回退", flush=True)
        from llm_utils import translate
        for b in chunk:
            try:
                all_done[str(b["id"])] = translate(b["content"], stream=False)
            except Exception as e2:
                print(f"  段 {b['id']} 失败: {e2}", flush=True)
                all_done[str(b["id"])] = b["content"]
    json.dump(all_done, open(os.path.join(DIR, "_translations.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"  检查点已存：{len(all_done)}/{len(to_translate)}", flush=True)

print("翻译完成，全部块已翻译。", flush=True)

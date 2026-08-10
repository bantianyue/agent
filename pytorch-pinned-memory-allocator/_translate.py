#!/usr/bin/env python3
"""临时：PyTorch pinned memory devlog 翻译。"""
import json, sys, os
sys.path.insert(0, r"C:/Users/twfehh7/AppData/Local/hermes/skills/content-creation/wechat-article-sop/scripts")
from llm_utils import translate_batch

DIR = r"D:/06_Hermes/articles/pytorch-pinned-memory-allocator"
content = json.load(open(os.path.join(DIR, "_content.json"), encoding="utf-8"))

# References 节标志
in_ref = False
blocks = []
bid = 0
for x in content:
    t = x['type']
    if t == 'h2' and x['text'].strip().lower() == 'references':
        in_ref = True; continue
    if in_ref:
        continue  # References 节内容保留原文
    if t in ('p','h2'):
        blocks.append({"id": bid, "type":"text", "content": x['text']}); bid += 1
    elif t == 'li':
        blocks.append({"id": bid, "type":"text", "content": x['text']}); bid += 1

json.dump(blocks, open(os.path.join(DIR, "_extract_blocks.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"待翻译块总数: {len(blocks)}")

done = {}
if os.path.exists(os.path.join(DIR, "_translations.json")):
    done = json.load(open(os.path.join(DIR, "_translations.json"), encoding="utf-8"))
todo = [b for b in blocks if str(b["id"]) not in done]
print(f"待翻译 {len(todo)}/{len(blocks)} 块", flush=True)

CHUNK=30
for c in range(0, len(todo), CHUNK):
    chunk=todo[c:c+CHUNK]
    print(f"翻译 chunk {c//CHUNK+1} ({len(chunk)}块)", flush=True)
    try:
        tr = translate_batch(chunk, batch_size=8)
        for t in tr: done[str(t["id"])]=t["content"]
    except Exception as e:
        print(f"chunk失败 {e}，逐段回退", flush=True)
        from llm_utils import translate
        for b in chunk:
            try: done[str(b["id"])]=translate(b["content"], stream=False)
            except Exception as e2: done[str(b["id"])]=b["content"]; print(f"  {b['id']}失败{e2}",flush=True)
    json.dump(done, open(os.path.join(DIR, "_translations.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"  检查点 {len(done)}/{len(blocks)}", flush=True)
print("翻译完成", flush=True)

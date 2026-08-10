#!/usr/bin/env python3
"""临时：arXiv 论文翻译（公式保留LaTeX）。"""
import json, sys, os
sys.path.insert(0, r"C:/Users/twfehh7/AppData/Local/hermes/skills/content-creation/wechat-article-sop/scripts")
from llm_utils import translate_batch

DIR = r"D:/06_Hermes/articles/cross-model-kv-cache-transfer"
content = json.load(open(os.path.join(DIR, "_content.json"), encoding="utf-8"))

PROMPT_SUFFIX = "\n\n[翻译要求：把上面英文翻译为简体中文技术文章。保留所有 LaTeX 数学公式（\\(...\\) 内内容原样）、专有名词/模型名/数据集名（Qwen3/Llama/CoQA/PRM800K等）与代码标识符。技术术语可意译。]"

blocks = [{"id": i, "type":"text", "content": x['text']} for i,x in enumerate(content)]
json.dump(blocks, open(os.path.join(DIR, "_extract_blocks.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"待翻译块总数: {len(blocks)}")

done = {}
if os.path.exists(os.path.join(DIR, "_translations.json")):
    done = json.load(open(os.path.join(DIR, "_translations.json"), encoding="utf-8"))
todo = [b for b in blocks if str(b["id"]) not in done]
print(f"待翻译 {len(todo)}/{len(blocks)} 块", flush=True)

CHUNK=10
for c in range(0, len(todo), CHUNK):
    chunk=todo[c:c+CHUNK]
    print(f"翻译 chunk {c//CHUNK+1} ({len(chunk)}块, 共{len(todo)}待转)", flush=True)
    try:
        tr = translate_batch(chunk, batch_size=4)
        for t in tr: done[str(t["id"])]=t["content"]
    except Exception as e:
        print(f"chunk失败 {e}，逐段回退", flush=True)
        from llm_utils import translate
        for b in chunk:
            try: done[str(b["id"])]=translate(b["content"]+PROMPT_SUFFIX, stream=False)
            except Exception as e2: done[str(b["id"])]=b["content"]; print(f"  {b['id']}失败{e2}",flush=True)
    json.dump(done, open(os.path.join(DIR, "_translations.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"  检查点 {len(done)}/{len(blocks)}", flush=True)
print("翻译完成", flush=True)

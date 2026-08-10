#!/usr/bin/env python3
"""通用翻译：读 _content.json -> _translations.json。用法: _translate_common.py <dir>"""
import json, sys, os
sys.path.insert(0, r"C:/Users/twfehh7/AppData/Local/hermes/skills/content-creation/wechat-article-sop/scripts")
from llm_utils import translate_batch

DIR = sys.argv[1]
content = json.load(open(os.path.join(DIR, "_content.json"), encoding="utf-8"))

# 收集可翻译块：p/h2/h3/h4/li/img(caption=alt)
blocks=[]; bidmap={}  # content索引 -> 翻译id
bid=0
for i,x in enumerate(content):
    t=x['type']
    if t in ('p','h2','h3','h4','li'):
        text=x.get('text','').strip()
        if text:
            blocks.append({"id":bid,"type":"text","content":text}); bidmap[i]=bid; bid+=1
    elif t=='img':
        # img 的 caption/alt 翻译
        cap=x.get('caption') or ''
        if cap:
            blocks.append({"id":bid,"type":"text","content":cap}); bidmap[i]=bid; bid+=1

json.dump(bidmap, open(os.path.join(DIR,"_bidmap.json"),"w"), ensure_ascii=False)
print(f"待翻译块总数: {len(blocks)}", flush=True)

done={}
if os.path.exists(os.path.join(DIR,"_translations.json")):
    done=json.load(open(os.path.join(DIR,"_translations.json"),encoding="utf-8"))
todo=[b for b in blocks if str(b["id"]) not in done]
print(f"待翻译 {len(todo)}/{len(blocks)}", flush=True)

CHUNK=15
for c in range(0,len(todo),CHUNK):
    chunk=todo[c:c+CHUNK]
    print(f"chunk {c//CHUNK+1} ({len(chunk)}块)", flush=True)
    try:
        tr=translate_batch(chunk,batch_size=6)
        for t_ in tr: done[str(t_["id"])]=t_["content"]
    except Exception as e:
        print(f"chunk失败{str(e)[:60]}，逐段回退", flush=True)
        from llm_utils import translate
        for b in chunk:
            try: done[str(b["id"])]=translate(b["content"],stream=False)
            except Exception as e2: done[str(b["id"])]=b["content"]; print(f"  {b['id']}失败",flush=True)
    json.dump(done, open(os.path.join(DIR,"_translations.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"  检查点 {len(done)}/{len(blocks)}", flush=True)
print("翻译完成", flush=True)

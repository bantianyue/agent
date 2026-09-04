# -*- coding: utf-8 -*-
"""翻译 Decagon 4.7x 推理优化文章"""
import json, os, sys
base=r"D:/06_Hermes/articles/inference-4p7x-gpu-efficiency"
d=json.load(open(base+"/_fxtwitter.json",encoding="utf-8"))
art=d['tweet']['article']
blocks=art['content']['blocks']
# 提取文本(保留 header-two 为标题)+ code
texts=[]
for bi,b in enumerate(blocks):
    if b['type']=='atomic': 
        texts.append({"id":bi,"text":"","type":"fig"})
        continue
    ty=b['type']
    texts.append({"id":bi,"text":b.get('text','').strip() or b.get('text',''),"type":"h3" if ty=='header-two' else "p"})
# 翻译非 fig 文本
import sys
sys.path.insert(0, r"C:/Users/twfehh7/AppData/Local/hermes/skills/content-creation/wechat-article-sop/scripts")
os.environ["LLM_BASE_URL"]="https://api.deepseek.com"
os.environ["LLM_API_KEY"]="sk-5576e41b77af4cd2895e9decd1f89901"
os.environ["LLM_MODEL"]="deepseek-chat"
import llm_utils
to_t=[t for t in texts if t['text']]
outfile=base+"/_trans.json"
translations=json.load(open(outfile,encoding="utf-8")) if os.path.exists(outfile) else {}
todo=[{"id":t['id'],"content":t['text'],"type":"p"} for t in to_t if str(t['id']) not in translations]
print(f"待译 {len(todo)}/{len(to_t)}")
CHUNK=8
for st in range(0,len(todo),CHUNK):
    try:
        res=llm_utils.translate_batch(todo[st:st+CHUNK],batch_size=len(todo[st:st+CHUNK]))
        for r in res:
            translations[str(r['id'])]=r.get('content','')
        json.dump(translations,open(outfile,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
        print(f"批{st//CHUNK+1} ✓ {len(translations)}",flush=True)
    except Exception as e:
        print("fail",str(e)[:150]); break
# title前序内容打印供 build
for t in to_t:
    print(f"[{t['id']}:{t['type']}] {t['text'][:70]}")
JSOND={'blocks':[]}
for t in to_t:
    JSOND['blocks'].append({"id":t['id'],"type":t['type'],"en":t['text'],"zh":translations.get(str(t['id']),'')})
json.dump(JSOND,open(base+"/_all.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("\nALL done")
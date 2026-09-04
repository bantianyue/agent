# -*- coding: utf-8 -*-
"""翻译 X Article 文本段（正确 translate_batch API）"""
import json, os, sys
sys.path.insert(0, r"C:/Users/twfehh7/AppData/Local/hermes/skills/content-creation/wechat-article-sop/scripts")
import llm_utils
base=r"D:/06_Hermes/articles/llm-inference-efficient-frontier"
texts=json.load(open(base+"/_texts.json",encoding="utf-8"))
# 转 proper paragraphs: {id, content, type}
paras=[]
for i,t in enumerate(texts):
    paras.append({"id":i,"content":t['text'],"type":t['type']})
outfile=base+"/_translations_full.json"
CHUNK=12
all_trans={}
if os.path.exists(outfile):
    all_trans=json.load(open(outfile,encoding="utf-8"))
# 找待译
def need(p):
    return p['type']!='code' and str(p['id']) not in all_trans
todo=[p for p in paras if need(p)]
print(f"待译 {len(todo)}/{len(paras)}")
for start in range(0,len(todo),CHUNK):
    batch=todo[start:start+CHUNK]
    try:
        res=llm_utils.translate_batch(batch, batch_size=len(batch))
        n=0
        for r in res:
            all_trans[str(r['id'])]=r.get('content','')
            n+=1
        json.dump(all_trans,open(outfile,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
        print(f"  批 {start//CHUNK+1}/{(len(todo)+CHUNK-1)//CHUNK} 完成，累计 {len(all_trans)}")
    except Exception as e:
        print(f"  批失败: {str(e)[:150]}")
        break
print("\n=== 翻译结果核对 ===")
for i in sorted(all_trans.keys(), key=int):
    print(f"[{i}] {str(all_trans[i])[:65]}")

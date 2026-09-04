# -*- coding: utf-8 -*-
"""翻译 E-Commerce Bench 核心段落"""
import json, os, sys
sys.path.insert(0, r"C:/Users/twfehh7/AppData/Local/hermes/skills/content-creation/wechat-article-sop/scripts")
os.environ["LLM_BASE_URL"]="https://api.deepseek.com"
os.environ["LLM_API_KEY"]="sk-5576e41b77af4cd2895e9decd1f89901"
os.environ["LLM_MODEL"]="deepseek-chat"
import llm_utils
base=r"D:/06_Hermes/articles/ecommerce-bench-llm-agents"
core=json.load(open(base+"/_core_dedup.json",encoding="utf-8"))
paras=[{"id":i,"content":c['text'],"type":"p"} for i,c in enumerate(core) if c['type']=='text']
outfile=base+"/_core_trans.json"
translations={}
if os.path.exists(outfile):
    translations=json.load(open(outfile,encoding="utf-8"))
todo=[p for p in paras if str(p['id']) not in translations]
print(f"待译: {len(todo)}/{len(paras)}")
CHUNK=10
for start in range(0,len(todo),CHUNK):
    batch=todo[start:start+CHUNK]
    try:
        res=llm_utils.translate_batch(batch,batch_size=len(batch))
        for r in res:
            translations[str(r['id'])]=r.get('content','')
        json.dump(translations,open(outfile,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
        print(f"  批{start//CHUNK+1} ✓ 累计{len(translations)}")
    except Exception as e:
        print(f"  批失败: {str(e)[:150]}")
        break
print(f"\n完成 {len(translations)}/{len(paras)}")
# 打印部分翻译验证
for k in list(translations.keys())[:6]:
    print(f"[{k}] {str(translations[k])[:55]}")

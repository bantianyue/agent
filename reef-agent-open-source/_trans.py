# -*- coding: utf-8 -*-
"""翻译 Reef 文章文本块（代码保留原文）"""
import json, os, sys
sys.path.insert(0, r"C:/Users/twfehh7/AppData/Local/hermes/skills/content-creation/wechat-article-sop/scripts")
os.environ["LLM_BASE_URL"]="https://api.deepseek.com"
os.environ["LLM_API_KEY"]="sk-5576e41b77af4cd2895e9decd1f89901"
os.environ["LLM_MODEL"]="deepseek-chat"
import llm_utils
base=r"D:/06_Hermes/articles/reef-agent-open-source"
items=json.load(open(base+"/_items.json",encoding="utf-8"))
# 翻译文本项
texts=[it for it in items if it['type']=='text']
codes=[it for it in items if it['type']=='code']
figs=[it for it in items if it['type']=='fig']
print(f"文本 {len(texts)}, 代码 {len(codes)}, 图 {len(figs)}")
paras=[{"id":i,"content":it['text'],"type":"p"} for i,it in enumerate(texts)]
outfile=base+"/_trans.json"
translations={}
if os.path.exists(outfile):
    translations=json.load(open(outfile,encoding="utf-8"))
todo=[p for p in paras if str(p['id']) not in translations]
print(f"待译 {len(todo)}")
CHUNK=8
for start in range(0,len(todo),CHUNK):
    batch=todo[start:start+CHUNK]
    try:
        res=llm_utils.translate_batch(batch,batch_size=len(batch))
        for r in res:
            translations[str(r['id'])]=r.get('content','')
        json.dump(translations,open(outfile,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
        print(f"  批{start//CHUNK+1} ✓ 累计{len(translations)}")
    except Exception as e:
        print(f"  批失败 {str(e)[:200]}")
        break
print(f"\n完成 {len(translations)}/{len(texts)}")
# 翻译验证（正文前中后）
for k in ['0','1','15','36','54','55']:
    if k in translations:
        print(f"[{k}] {str(translations[k])[:60]}")
# 存原文本备份
json.dump([{"id":i,"en":it['text']} for i,it in enumerate(texts)],open(base+"/_texts_en.json","w",encoding="utf-8"),ensure_ascii=False)
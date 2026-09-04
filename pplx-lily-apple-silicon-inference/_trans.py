# -*- coding: utf-8 -*-
"""Apple silicon 文章 翻译文本段(标题/段落/LI/图注)"""
import json, os, sys, time
sys.path.insert(0, r"C:/Users/twfehh7/AppData/Local/hermes/skills/content-creation/wechat-article-sop/scripts")
os.environ["LLM_BASE_URL"]="https://api.deepseek.com"
os.environ["LLM_API_KEY"]="sk-5576e41b77af4cd2895e9decd1f89901"
os.environ["LLM_MODEL"]="deepseek-chat"
import llm_utils
base=r"D:/06_Hermes/articles/pplx-lily-apple-silicon-inference"
body=json.load(open(base+"/_blocks_clean.json",encoding="utf-8"))
outfile=base+"/_trans.json"
translations=json.load(open(outfile,encoding="utf-8")) if os.path.exists(outfile) else {}
# text items: normalize各块
def text_of(b):
    if b[0]=='H': return b[2]   # title
    if b[0] in ('P','LI','CAP'): return b[1]
    return None
todo=[]
for i,b in enumerate(body):
    txt=text_of(b)
    if txt and str(i) not in translations:
        todo.append({"id":i,"content":txt,"type":"p"})
print(f"待译 {len(todo)}")
CH=8
for st in range(0,len(todo),CH):
    try:
        res=llm_utils.translate_batch(todo[st:st+CH],batch_size=len(todo[st:st+CH]))
        for r in res: translations[str(r['id'])]=r.get('content','')
        json.dump(translations,open(outfile,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
        print(f"批{st//CH+1}.{len(translations)}",flush=True)
    except Exception as e:
        print("fail",str(e)[:120]);time.sleep(2)
print("DONE",len(translations))

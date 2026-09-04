# -*- coding: utf-8 -*-
"""翻译 Hot Chips 2026 全文 154 段"""
import json, os, sys, time
sys.path.insert(0, r"C:/Users/twfehh7/AppData/Local/hermes/skills/content-creation/wechat-article-sop/scripts")
os.environ["LLM_BASE_URL"]="https://api.deepseek.com"
os.environ["LLM_API_KEY"]="sk-5576e41b77af4cd2895e9decd1f89901"
os.environ["LLM_MODEL"]="deepseek-chat"
import llm_utils
base=r"D:/06_Hermes/articles/hotchips-2026-conference-analysis"
items=json.load(open(base+"/_items2.json",encoding="utf-8"))
texts=[it for it in items if it['k']=='T']
outfile=base+"/_trans.json"
translations=json.load(open(outfile,encoding="utf-8")) if os.path.exists(outfile) else {}
# 标题单独译(a要准确)
hdrs=[it for it in texts if it['type'] in ('h1','h2')]
body=[it for it in texts if it['type'] not in ('h1','h2')]
def tr_batch(lst,tag):
    todo=[{"id":it['tidx'],"content":it['text'],"type":"p"} for it in lst if str(it['tidx']) not in translations]
    if not todo: return
    for st in range(0,len(todo),8):
        try:
            res=llm_utils.translate_batch(todo[st:st+8],batch_size=len(todo[st:st+8]))
            for r in res: translations[str(r['id'])]=r.get('content','')
            json.dump(translations,open(outfile,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
            print(f"{tag} 批{st//8+1} {len(translations)}",flush=True)
        except Exception as e:
            print(f"{tag} 失败 {str(e)[:120]}",flush=True); time.sleep(2); break
print(f"标题{len(hdrs)} 正文{len(body)} 待译(含已存)")
tr_batch(hdrs,"H ")
tr_batch(body,"B ")
print(f"DONE {len(translations)}/{len(texts)}")

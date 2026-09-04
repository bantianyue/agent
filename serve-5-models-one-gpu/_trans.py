# -*- coding: utf-8 -*-
"""翻译 serve-5-models GPU 全文 210 段（可续跑）"""
import json, os, sys, time
sys.path.insert(0, r"C:/Users/twfehh7/AppData/Local/hermes/skills/content-creation/wechat-article-sop/scripts")
os.environ["LLM_BASE_URL"]="https://api.deepseek.com"
os.environ["LLM_API_KEY"]="sk-5576e41b77af4cd2895e9decd1f89901"
os.environ["LLM_MODEL"]="deepseek-chat"
import llm_utils
base=r"D:/06_Hermes/articles/serve-5-models-one-gpu"
items=json.load(open(base+"/_items2.json",encoding="utf-8"))
texts=[it for it in items if it['k']=='T']
outfile=base+"/_trans.json"
translations=json.load(open(outfile,encoding="utf-8")) if os.path.exists(outfile) else {}
# 全部文本翻译，去重（相同文本只译一次）
uniq={}
for it in texts:
    uniq[it['tidx']]=it['text']
# 待译（按 tidx 全局 id 存储）
todo=[{"id":i,"content":uniq[i],"type":"p"} for i in sorted(uniq) if str(i) not in translations]
print(f"总 {len(uniq)}, 待译 {len(todo)}")
CHUNK=8
for start in range(0,len(todo),CHUNK):
    batch=todo[start:start+CHUNK]
    try:
        res=llm_utils.translate_batch(batch,batch_size=len(batch))
        for r in res:
            translations[str(r['id'])]=r.get('content','')
        json.dump(translations,open(outfile,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
        print(f"批{start//CHUNK+1}/{(len(todo)+CHUNK-1)//CHUNK} ✓ 累计{len(translations)}",flush=True)
    except Exception as e:
        print(f"批{start//CHUNK+1} 失败: {str(e)[:120]}",flush=True)
        time.sleep(3)
        break
print(f"DONE {len(translations)}/{len(uniq)}",flush=True)

# -*- coding: utf-8 -*-
"""vLLM 博客 format-preserving 中文翻译：正文段落/LI/标题/Q，代码与图原样;纯引用URL段保留"""
import json, os, sys
base=r"D:/06_Hermes/articles/vllm-anatomy-high-throughput-inference"
bl=json.load(open(base+"/_blocks.json",encoding="utf-8"))
# 收集需要翻译的文本：T(带lvl标题也算), LI, Q; TBL 需翻cell但结构保留(简单字符串map后包装)
transl_needed=[]
translations=json.load(open(base+"/_trans.json",encoding="utf-8")) if os.path.exists(base+"/_trans.json") else {}
def txt_of(b):
    if 'T' in b: return b['T']
    if 'LI' in b: return b['LI']
    if 'Q' in b: return b['Q']
for idx,b in enumerate(bl):
    txt=txt_of(b)
    if txt is None: continue
    # 纯URL/纯引用行/纯数字不翻
    if txt.startswith('vLLM https://') or (txt.startswith('http') and len(txt)<40): continue
    if idx not in translations:
        transl_needed.append({"id":idx,"content":txt,"type":"p"})
print(f"待翻译 {len(transl_needed)} 块")
# 分批，含已有缓存
sys.path.insert(0, r"C:/Users/twfehh7/AppData/Local/hermes/skills/content-creation/wechat-article-sop/scripts")
os.environ["LLM_BASE_URL"]="https://api.deepseek.com"
os.environ["LLM_API_KEY"]="sk-5576e41b77af4cd2895e9decd1f89901"
os.environ["LLM_MODEL"]="deepseek-chat"
import llm_utils
CH=8
for st in range(0,len(transl_needed),CH):
    batch=transl_needed[st:st+CH]
    try:
        res=llm_utils.translate_batch(batch,batch_size=len(batch))
        for r in res: translations[r['id']]=r.get('content','')
        json.dump(translations,open(base+"/_trans.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
        print(f"批{st//CH+1} ✓ {len(translations)}",flush=True)
    except Exception as e:
        print(f"批失败 {str(e)[:150]}",flush=True); import time; time.sleep(2)
print(f"DONE {len(translations)}/{len(bl)}")

# -*- coding: utf-8 -*-
"""PyTorch2.14 翻译 - 全部文本块 P/LI/H titles; 用API名保护占位改善 inline code"""
import json, os, sys, re, time
base=r"D:/06_Hermes/articles/pytorch-2-14-release"
blocks=json.load(open(base+"/_blocks.json",encoding="utf-8"))
trans=json.load(open(base+"/_trans.json",encoding="utf-8")) if os.path.exists(base+"/_trans.json") else {}
outfile=base+"/_trans.json"
# 给待译段加持: 提取已经 inline code 文本,不用占位(deepseek 保标识符) —— 但 API 名会丢空格? 保守: 把 [A-Za-z_](\w*[._]\w*)+ 类标识符用 ◈N◈ 护
CODE_TOK=re.compile(r'`([^`]+)`|([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*){1,4})')
# 只保护反引号code和形如 torch.compile 带点; 简单的lower (compile/torch)误护会坏中文, 不护单词
placeholder_seen=[]
def text_of(b):
    if 'T' in b: return b['T']
    if 'P' in b: return b['P']
    if 'LI' in b: return b['LI']
    return None

todo=[]
for i,b in enumerate(blocks):
    txt=text_of(b)
    if txt and str(i) not in trans:
        todo.append({'id':i,'content':txt,'type':'p'})
print("待译:",len(todo))
sys.path.insert(0, r"C:/Users/twfehh7/AppData/Local/hermes/skills/content-creation/wechat-article-sop/scripts")
os.environ["LLM_BASE_URL"]="https://api.deepseek.com"
os.environ["LLM_API_KEY"]="sk-5576e41b77af4cd2895e9decd1f89901"
os.environ["LLM_MODEL"]="deepseek-chat"
import llm_utils
CH=8
for st in range(0,len(todo),CH):
    try:
        res=llm_utils.translate_batch(todo[st:st+CH],batch_size=len(todo[st:st+CH]))
        for r in res: trans[str(r['id'])]=r.get('content','')
        json.dump(trans,open(outfile,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
        print(f"批{st//CH+1}.{len(trans)}",flush=True)
    except Exception as e:
        print("fail",str(e)[:120]);time.sleep(2)
print("DONE",len(trans),"/",len(blocks))

# -*- coding: utf-8 -*-
"""翻译 Custom Base Die 全文（原文100%保留）"""
import json, os, sys
sys.path.insert(0, r"C:/Users/twfehh7/AppData/Local/hermes/skills/content-creation/wechat-article-sop/scripts")
os.environ["LLM_BASE_URL"]="https://api.deepseek.com"
os.environ["LLM_API_KEY"]="sk-5576e41b77af4cd2895e9decd1f89901"
os.environ["LLM_MODEL"]="deepseek-chat"
import llm_utils
base=r"D:/06_Hermes/articles/custom-base-die-hbm-bandwidth"
# 读原始 blocks 的文本（用 _all_texts 但保留完整文本）
d=json.load(open(base+"/_fxtwitter.json",encoding="utf-8"))
art=d['tweet']['article']
blocks=art['content']['blocks']
em={str(e['key']):{'type':e['value']['type'],'data':e['value']['data']} for e in art['content']['entityMap']}
# 提取文本块（保留所有 type）
texts=[]
for bi,b in enumerate(blocks):
    if b['type']=='atomic': continue
    ty=b['type']
    ht={'header-one':'h2','header-two':'h3','blockquote':'quote','ordered-list-item':'ol','unordered-list-item':'ul','unstyled':'p'}.get(ty,'p')
    texts.append({"type":ht,"text":b.get('text','').strip(),"block":bi})
# 过滤 34-37 订阅推广（保留用于参考，不翻正文）
main_texts=[t for t in texts if t['block']<34]
promo=[t for t in texts if t['block']>=34]
print(f"正文翻译 {len(main_texts)} 段, 跳过推广 {len(promo)} 段")
# 翻译主文本（保留 h2/h3/quote/ul 结构）
paras=[{"id":t['block'],"content":t['text'],"type":"p"} for t in main_texts]
outfile=base+"/_translations.json"
translations={}
if os.path.exists(outfile):
    translations=json.load(open(outfile,encoding="utf-8"))
todo=[p for p in paras if str(p['id']) not in translations]
print(f"待译: {len(todo)}")
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
        print(f"  批失败: {str(e)[:120]}")
        break
np=len(main_texts)-len(promo)+0
print(f"\n完成 {len(translations)}/{len(main_texts)}")
# 验证翻译
for k in sorted(translations.keys(),key=int):
    print(f"[{k}] {str(translations[k])[:55]}")
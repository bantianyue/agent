# -*- coding: utf-8 -*-
"""翻译 Tenstorrent QuietBox 全文"""
import json, os, sys
sys.path.insert(0, r"C:/Users/twfehh7/AppData/Local/hermes/skills/content-creation/wechat-article-sop/scripts")
os.environ["LLM_BASE_URL"]="https://api.deepseek.com"
os.environ["LLM_API_KEY"]="sk-5576e41b77af4cd2895e9decd1f89901"
os.environ["LLM_MODEL"]="deepseek-chat"
import llm_utils
base=r"D:/06_Hermes/articles/tenstorrent-quietbox-400tps"
blocks=[json.loads(l) for l in open(base+"/blocks.jsonl",encoding="utf-8")]
# 去掉广告块
clean=[b for b in blocks if not (b['type']=='text' and ('Join Medium' in b.get('content','') or 'Get updates' in b.get('content',''))) ]
print(f"blocks: {len(blocks)} -> {len(clean)}")
# 分类：标题 vs 段落
texts=[b for b in clean if b['type']=='text']
figs=[b for b in clean if b['type']=='figure']
# 翻译文本（标题检测）
paras=[]
for i,b in enumerate(texts):
    content=b['content']
    is_h='## ' in content[:5]
    paras.append({"id":i,"content":content.replace('## ',''),"type":"p","ish":"h2" if is_h else "p"})
outfile=base+"/_trans.json"
translations={}
if os.path.exists(outfile):
    translations=json.load(open(outfile,encoding="utf-8"))
todo=[p for p in paras if str(p['id']) not in translations]
print(f"待译 {len(todo)}/{len(paras)}")
CHUNK=9
for start in range(0,len(todo),CHUNK):
    batch=todo[start:start+CHUNK]
    try:
        res=llm_utils.translate_batch([{"id":p['id'],"content":p['content'],"type":"p"} for p in batch],batch_size=len(batch))
        for r in res:
            translations[str(r['id'])]=r.get('content','')
        json.dump(translations,open(outfile,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
        print(f"  批{start//CHUNK+1} ✓ 累计{len(translations)}")
    except Exception as e:
        print(f"  批失败: {str(e)[:200]}")
        break
print(f"\n完成 {len(translations)}/{len(paras)}")
for k in sorted(translations.keys(),key=int):
    print(f"[{k}] {str(translations[k])[:55]}")
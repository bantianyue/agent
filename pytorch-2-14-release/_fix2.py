# -*- coding: utf-8 -*-
import json,re
base=r"D:/06_Hermes/articles/pytorch-2-14-release"
D=json.load(open(base+"/article_data.json",encoding="utf-8"))
def clean(p):
    # batch * 2 数学 -> ×
    p=re.sub(r'\s*\*\s*(\d+)', r'×\1', p)
    # kernel_* -> kernel（多个）: 末尾wildcard
    p=re.sub(r'(_\*)\s*$', r'（所有变体）', p)
    p=p.replace('ncclSymkDevKernel_*','ncclSymkDevKernel')
    return p
for s in D['sections']: s['paras']=[clean(x) for x in s['paras']]
D['lead']=[clean(x) for x in D['lead']]
def bad(p): return p.count('*')>p.count('**')*2
n=sum(1 for s in D['sections'] for p in s['paras'] if bad(p))
print("剩余孤星段数:",n)
for s in D['sections']:
    for p in s['paras']:
        if bad(p): print(' 残',p[:70])
json.dump(D,open(base+"/article_data.json","w",encoding="utf-8"),ensure_ascii=False,indent=2)

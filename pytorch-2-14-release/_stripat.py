# -*- coding: utf-8 -*-
import json,re
base=r"D:/06_Hermes/articles/pytorch-2-14-release"
D=json.load(open(base+"/article_data.json",encoding="utf-8"))
def clean(p):
    # @dynamic_spec 装饰器写法 → "dynamic_spec 装饰器"? 保留函数语境"装饰器 @dynamic_spec"=去@保留dynamic_spec即可(前置说明)
    # 通用: 脱@ 词首
    p=re.sub(r'(?<!\w)\@([A-Za-z_])', r'\1', p)
    return p
for s in D['sections']: s['paras']=[clean(x) for x in s['paras']]
D['lead']=[clean(x) for x in D['lead']]; D['conclusion']=[clean(x) for x in D['conclusion']]
json.dump(D,open(base+"/article_data.json","w",encoding="utf-8"),ensure_ascii=False,indent=2)
# count removed
txt=''.join(p for s in D['sections'] for p in s['paras'])
print("残留@word:", len(re.findall(r'(?<!\w)@[A-Za-z_]', txt)))

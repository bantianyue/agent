# -*- coding: utf-8 -*-
import json,re
base=r"D:/06_Hermes/articles/pytorch-2-14-release"
D=json.load(open(base+"/article_data.json",encoding="utf-8"))
# 去掉文本里孤立代码通配符* （非**加粗）: 出现在 token前缀 `*_` , `*args`, 数字乘? 
# 全局去除非 ** 上下文中的单星只影响 *_name 型与参数展开 `*args`-> args  用保守正则
def clean(p):
    # 1) *_identifier -> identifier (glob参数名)
    p=re.sub(r'\*_([A-Za-z_])', r'\1', p)
    # 2) dangling 单 * (排除被**包住的只有内容里真正单独出现) 移除 (如放在单词间 *foo*)
    # p=re.sub(r'(?<!\*)\*([^*\s][^*]*?)\*(?!\*)','\\1',p) # 太激进,保留
    return p
for s in D['sections']:
    s['paras']=[clean(p) for p in s['paras']]
D['lead']=[clean(p) for p in D['lead']]
# recheck
def bad(p): return p.count('*')>p.count('**')*2
badn=sum(1 for s in D['sections'] for p in s['paras'] if bad(p))
print("残留孤星段:",badn)
for s in D['sections']:
    for p in s['paras']:
        if bad(p): print("   ",p[:70])
json.dump(D,open(base+"/article_data.json","w",encoding="utf-8"),ensure_ascii=False,indent=2)

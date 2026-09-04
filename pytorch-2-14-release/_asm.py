# -*- coding: utf-8 -*-
"""PyTorch2.14 DATA writer (简 clear build)"""
import json, os
base=r"D:/06_Hermes/articles/pytorch-2-14-release"
blocks=json.load(open(base+"/_blocks.json",encoding="utf-8"))
tr=json.load(open(base+"/_trans.json",encoding="utf-8"))
def txt(i,k): return tr.get(str(i), '')

# 大节 h2 set 作为边界(遇新h2即隔离section)
S=[]
cur=None
def close():
    global cur
    if isinstance(cur,dict) and cur.get('paras'): S.append(cur)
    cur=None
def h2open(title):
    global cur;close();cur={'type':'h2','title':title,'paras':[]}
intro_buf=[]
for i,b in enumerate(blocks):
    k=next(iter(b))
    if k=='P': val=b['P']
    elif k=='H': val=''
    elif k=='LI': val=b['LI']
    else: val=''
    if k=='H':
        lv=b['H'];title=tr.get(str(i),val)
        if i==0: 
            # block0 = 精选项目h3 -> 不管,跳到后续
            continue
        if lv<=2: h2open(title)
        else:
            if cur is None: h2open('')  # 未开先开空(不会)
            cur.setdefault('paras',[]).append('**'+title+'**')
        continue
    if k=='LI': 
        # highlight bullets在lead区(3-11)全部进intro_buf 若i<18 ; 各节LI 进正文
        t=tr.get(str(i),val); t=('· '+t) if t else ''
        if i<18: 
            if t: intro_buf.append(t)
        elif cur is not None and t: cur['paras'].append(t)
        continue
    # k==P
    t=tr.get(str(i),val)
    if not t: continue
    if i<18: intro_buf.append(t)
    elif cur is not None: cur['paras'].append(t)
close()
# 剔除 S 里纯空title节
S=[x for x in S if x['title'].strip()]
print("sections:",len(S))
for x in S: print('  h2',x['title'][:40],len(x['paras']))
print("intro P 数:",len(intro_buf))
json.dump({'S':S,'intro':intro_buf},open(base+"/_S.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)

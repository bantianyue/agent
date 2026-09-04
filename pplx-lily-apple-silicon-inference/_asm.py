# -*- coding: utf-8 -*-
"""Apple Silicon 文章 组装 article_data.json"""
import json, os, re
base=r"D:/06_Hermes/articles/pplx-lily-apple-silicon-inference"
body=json.load(open(base+"/_blocks_clean.json",encoding="utf-8"))
tr=json.load(open(base+"/_trans.json",encoding="utf-8"))
# fig 顺序: FIG blocks in body
figidx=[i for i,b in enumerate(body) if b[0]=='FIG']
figcap_of={}   # pidx->caption(前后续cap)
for i,b in enumerate(body):
    if b[0]=='CAP':
        # 关联: CAP 对应前面最近 FIG (原文FIG后跟 CAP 行)
        prev_fig=None
        for j in range(i-1,-1,-1):
            if body[j][0]=='FIG': prev_fig=j;break
        if prev_fig is not None: figcap_of[prev_fig]=tr.get(str(i),b[1])

def is_toc_preamble(i):
    # block1-8=Contents目录 LI, block? 跳过目录但保留图1/图? 图1在18
    return 1<=i<=8

S=[]; cur=None
def close():
    global cur
    if cur is not None:
        # 去空节
        if cur.get('paras') or cur.get('fig_after'): S.append(cur)
    cur=None
def open1(lvl,title):
    global cur
    close()
    cur={'type':'h2' if lvl<=2 else 'h3','title':title,'paras':[]}

lead=[]  # 从 preamble
# walk
pending_fig=None
for i,b in enumerate(body):
    k=b[0]
    if is_toc_preamble(i): continue
    if k=='FIG' and i<12:
        # 放后 lead 无图；记
        continue
    if k=='FIG':
        # 图: 挂到当前 cur
        if cur is None: open1(2,'')
        fa=cur.setdefault('fig_after',{})
        cap=figcap_of.get(i,'')
        fa.setdefault('0',[]).append({'src':f'fig{c:02d}' if False else '', 'caption':cap})
        # src 需真实名: 用定位
        try:
            pass
        except: pass
        continue
    if k=='CAP': continue   # 其文已用作 fig caption
    txt=tr.get(str(i)) or (b[2] if k=='H' else b[1] if k!='FIG' else '')
    if not txt: continue
    if k=='H':
        open1(b[1], txt)
    elif cur is not None:
        if k=='LI': txt='· '+txt
        cur['paras'].append(txt)
close()

# fig src 修正 (上面占位): 重扫赋值真实
import re as _re
fig_n=0
for s in S:
    for idx,lst in (s.get('fig_after') or {}).items():
        for f in lst:
            if not f['src']:
                fig_n+=1; f['src']=f'fig{fig_n:02d}.png'
# 可能 fig 顺序不符DOM (若图在某节中间而非节0前)。修正按实际DOM序编号重来
# 直接按 body DOM序找出每fig归属section为其后cur
print("S sections:",len(S),"共 paras:",sum(len(s.get('paras',[])) for s in S))
fcount=sum(len(v) for s in S for v in s.get('fig_after',{}).values())
print("fig插位:",fcount)
json.dump(S,open(base+"/_secTmp.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)

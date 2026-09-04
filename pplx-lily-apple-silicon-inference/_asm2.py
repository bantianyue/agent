# -*- coding: utf-8 -*-
"""Apple Silicon 组装器 v2: 精确图序, lead分离, fig插当前节正确key"""
import json, os, re
base=r"D:/06_Hermes/articles/pplx-lily-apple-silicon-inference"
body=json.load(open(base+"/_blocks_clean.json",encoding="utf-8"))
tr=json.load(open(base+"/_trans.json",encoding="utf-8"))
# ---- lead: preamble 就是 body 0..? 到引言H12之前 的 block(不含目录LI 1-8, 不含被废弃日期等，已在clean删)
lead_items=[]
body_i_start=0
for i in range(len(body)):
    if body[i][0]=='H' and str(body[i][2]).strip() in ("Introduction","引言"):
        body_i_start=i; break
# lead = 前面非目录非图文字
for i in range(body_i_start):
    b=body[i]
    if b[0] in ('P','LI') and not (1<=i<=8):  # 目录跳过
        t=tr.get(str(i)) or b[1]
        if b[0]=='LI': t='· '+t
        lead_items.append(t)
    if b[0]=='FIG':
        lead_items.append('[图]')  # 实际lead不放图，只正文; image1/2 in intro一般图在正文

# ---- 正文 from body_i_start
S=[]; cur=None; next_fig=1
def close():
    global cur
    if cur is not None and (cur.get('paras') or cur.get('fig_after')):
        S.append(cur)
def open1(lvl,title):
    global cur
    close(); cur={'type':'h2' if lvl<=2 else 'h3','title':title,'paras':[]}
def add_para(tx):
    if cur is None: open1(2,'') 
    cur['paras'].append(tx)

for i in range(body_i_start, len(body)):
    b=body[i]; k=b[0]
    if k=='FIG':
        if cur is None: open1(2,'')
        fa=cur.setdefault('fig_after',{})
        nm=f'fig{next_fig:02d}.png'; next_fig+=1
        cap=''
        # 下个是CAP?
        if i+1<len(body) and body[i+1][0]=='CAP':
            cap=tr.get(str(i+1), body[i+1][1])
        key=str(max(0,len(cur['paras'])-1))
        fa.setdefault(key,[]).append({"src":nm,"caption":cap})
        continue
    if k=='CAP': continue
    txt=tr.get(str(i)) or (b[2] if k=='H' else b[1])
    if not txt: continue
    if k=='H':
        open1(b[1], txt)
    else:
        if k=='LI': txt='· '+txt
        add_para(txt)
close()
print("lead paras:",len(lead_items))
print("sections:",len(S), "图:", next_fig-1)
for i,s in enumerate(S):
    nb=sum(len(v) for v in s.get('fig_after',{}).values())
    print(f" [{i}]{s['type']}«{s['title'][:26]}» p{len(s['paras'])} f{nb}")
json.dump({"lead":lead_items,"sec":S},open(base+"/_ready.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)

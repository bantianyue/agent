# -*- coding: utf-8 -*-
import os,json
DIR=r"D:/06_Hermes/articles/attention-mechanisms-explained-long"
p=os.path.join(DIR,'article_data.json')
d=json.load(open(p,encoding='utf8'))
S=d['sections']
# flatten nontrivial paragraphs: list of (sid,pidx)
anch=[]
for sid,sec in enumerate(S):
    # ignore pure intro helper? none empty
    for pidx,pa in enumerate(sec['paras']):
        if pa.strip(): anch.append((sid,pidx))
L=len(anch); nfig=16
# choose spaced anchors, avoid first paragraph (index0) to not precede opening
steps=[int(round((i*(L-1))/(nfig))) for i in range(nfig)]
# dedup & ensure <=L-1
seen=set(); chosen=[]
for s in steps:
    if s not in seen and s>0: seen.add(s); chosen.append(s)
# if not enough, fill any
k=1
while len(chosen)<nfig:
    if k not in seen: seen.add(k); chosen.append(k)
    k+=1
chosen=sorted(chosen)
# clear previous fig_after
for sec in S: sec['fig_after']={}
for i,a in enumerate(chosen):
    sid,pidx=anch[a]
    sec=S[sid]
    fn=f"fig{i+1:02d}.png"
    sec.setdefault('fig_after',{})[str(pidx)]=sec.setdefault('fig_after',{}).get(str(pidx),[])+[{"src":fn,"caption":""}]
json.dump(d,open(p,'w',encoding='utf8'),ensure_ascii=False,indent=2)
print("anchored",len(chosen),"paragraphs total",L)
tot=sum(len(v) for s in S for v in s.get('fig_after',{}).values())
print("total figs in json",tot)

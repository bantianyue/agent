#!/usr/bin/env python3
"""临时：组装 SemiAnalysis  sections。"""
import json, os

DIR = r"D:/06_Hermes/articles/tile-rt-inferencex"
c = json.load(open(os.path.join(DIR, "_content.json"), encoding="utf-8"))
t = json.load(open(os.path.join(DIR, "_translations.json"), encoding="utf-8"))

bid=0; tid_map={}
for i,x in enumerate(c):
    if x['type'] in ('p','h1','h2'):
        if 'paid subscribers' in x.get('text',''):
            tid_map[i]=None; continue
        tid_map[i]=bid; bid+=1
    elif x['type']=='img' and x.get('caption'):
        tid_map[i]=bid; bid+=1
def tr(i):
    tid=tid_map.get(i)
    return t.get(str(tid),'') if tid is not None else ''

# 组装
sections=[]; cur=None; para_list=[]; fig_list=[]
def flush():
    global cur,para_list,fig_list
    if cur is None: return
    if para_list or fig_list:
        fa={}
        for pi,figs in fig_list:
            fa.setdefault(str(pi),[]).extend(figs)
        sec={'type':'h2','title':cur}
        sec['paras']=para_list
        if fa: sec['fig_after']=fa
        sections.append(sec)
    para_list=[]; fig_list=[]; cur=None

lead_taken = False
lead_paras = []
for i,x in enumerate(c):
    tp=x['type']
    if tp in ('h1','h2'):
        if cur is None and lead_paras:
            # 首个标题前的内容 → lead
            lead_paras = lead_paras  # keep
        flush(); cur=tr(i)
    elif tp=='p':
        txt=tr(i).strip()
        if not txt: continue
        if cur is None:
            lead_paras.append(txt)
        else:
            para_list.append(txt)
    elif tp=='img':
        pi=max(0,len(para_list)-1) if para_list else 0
        cap=tr(i)
        fig_list.append((pi,[{"src":x['file'],"caption":cap}]))
    elif tp=='li':
        if cur is None:
            lead_paras.append(x['text'])
        else:
            para_list.append(x['text'])
flush()

json.dump({"lead":lead_paras,"sections":sections}, open(os.path.join(DIR,"_sections_preview.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=2)
print("lead paras:", len(lead_paras))
print("sections:", len(sections))
tp=sum(len(s.get('paras',[])) for s in sections)
print("total paras:", tp+len(lead_paras))
ok=True
adir=DIR
for si,s in enumerate(sections):
    n=len(s.get('paras',[]))
    for k in s.get('fig_after',{}):
        if int(k)>=n: print(f"!! 越界 sec{si} fig@{k} 节仅{n}段"); ok=False
print("bounds:", "OK" if ok else "VIOLATION")
allfigs={f["src"] for s in sections for v in s.get("fig_after",{}).values() for f in v}
disk=set(f for f in os.listdir(adir) if f.startswith('fig'))
print("match:", allfigs==disk, "| total figs:", sum(len(v) for s in sections for v in s.get('fig_after',{}).values()))
